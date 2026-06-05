"""SHIELDOSE 模型测试。"""

import numpy as np
import pytest

from model import SHIELDOSE


class TestModuleExports:
    """模块导出测试。"""

    def test_all(self):
        from model.pyshieldose import __all__

        assert __all__ == ["Model"]
        assert SHIELDOSE.__module__ == "model.pyshieldose"


class TestModelInit:
    """模型初始化测试。"""

    def test_invalid_detector(self):
        with pytest.raises(ValueError, match="无效的探测器编号"):
            SHIELDOSE(detector=5, unit=2, data_dir="data")

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="无效的单位编号"):
            SHIELDOSE(detector=1, unit=4, data_dir="data")

    @pytest.mark.requires_dll
    def test_valid_init(self, shieldose_al_model):
        assert shieldose_al_model.detector == 1
        assert shieldose_al_model.detector_name == "Al"
        assert shieldose_al_model.unit == 2
        assert shieldose_al_model.unit_name == "g/cm²"


@pytest.mark.requires_dll
class TestCalculation:
    """计算功能测试。"""

    def test_no_spectrum(self, shieldose_al_model):
        """无能谱时所有剂量应为 0。"""
        result = shieldose_al_model.calculate(depths=1.0)
        assert np.all(result["dose_slab"] == 0.0)
        assert np.all(result["dose_semi"] == 0.0)
        assert np.all(result["dose_sphere"] == 0.0)

    def test_scalar_input(self, shieldose_al_model):
        """标量输入应返回标量输出。"""
        result = shieldose_al_model.calculate(depths=1.0)
        assert np.ndim(result["depths"]) == 0
        assert np.ndim(result["dose_slab"]) == 1
        assert len(result["dose_slab"]) == 5

    def test_array_input(self, shieldose_al_model):
        """数组输入应返回数组输出。"""
        result = shieldose_al_model.calculate(depths=[0.5, 1.0, 5.0])
        assert np.ndim(result["depths"]) == 1
        assert len(result["depths"]) == 3
        assert result["dose_slab"].shape == (3, 5)

    def test_result_keys(self, shieldose_al_model):
        """结果应包含所有必需的键。"""
        result = shieldose_al_model.calculate(depths=1.0)
        expected_keys = {
            "depths", "detector", "unit",
            "dose_slab", "dose_semi", "dose_sphere",
            "eunit", "tinter",
        }
        assert set(result.keys()) == expected_keys

    def test_detector_info(self, shieldose_al_model):
        """结果应包含正确的探测器信息。"""
        result = shieldose_al_model.calculate(depths=1.0)
        assert result["detector"]["id"] == 1
        assert result["detector"]["name"] == "Al"
        assert result["unit"]["id"] == 2
        assert result["unit"]["name"] == "g/cm²"


@pytest.mark.requires_dll
class TestSpectrumInput:
    """能谱输入测试。"""

    def test_mismatched_energies_flux(self, shieldose_al_model):
        """能量和通量数组长度不同时应报错。"""
        with pytest.raises(ValueError, match="长度必须相同"):
            shieldose_al_model.calculate(
                depths=1.0,
                electron_energies=[0.1, 1.0],
                electron_flux=[1.0],
            )

    def test_too_few_points(self, shieldose_al_model):
        """能谱点数不足 3 个时应报错。"""
        with pytest.raises(ValueError, match="至少需要 3 个"):
            shieldose_al_model.calculate(
                depths=1.0,
                electron_energies=[0.1, 1.0],
                electron_flux=[1.0, 0.5],
            )

    def test_too_many_points(self, shieldose_al_model):
        """能谱点数超过 Fortran 工作数组时应报错。"""
        with pytest.raises(ValueError, match="最多支持 101 个"):
            shieldose_al_model.calculate(
                depths=1.0,
                electron_energies=np.linspace(0.1, 10.0, 102),
                electron_flux=np.ones(102),
            )

    def test_non_positive_depth(self, shieldose_al_model):
        """屏蔽深度必须为正值。"""
        with pytest.raises(ValueError, match="depths"):
            shieldose_al_model.calculate(depths=0.0)

    def test_electron_spectrum(self, shieldose_al_model):
        """电子能谱应产生非零剂量。"""
        result = shieldose_al_model.calculate(
            depths=0.5,
            electron_energies=[0.1, 1.0, 5.0],
            electron_flux=[1.0, 0.5, 0.1],
            tinter=1.0,
        )
        # 至少有一个分量非零
        assert np.any(result["dose_slab"] != 0.0)
        assert np.all(np.isfinite(result["dose_slab"]))
        np.testing.assert_allclose(
            result["dose_slab"][2],
            result["dose_slab"][0] + result["dose_slab"][1],
            rtol=1e-6,
        )


@pytest.mark.requires_dll
class TestDetectorTypes:
    """不同探测器类型测试。"""

    def test_al_detector(self, shieldose_al_model):
        assert shieldose_al_model.detector_name == "Al"

    def test_si_detector(self, shieldose_si_model):
        assert shieldose_si_model.detector_name == "Si"

    def test_different_detectors(self, shieldose_al_model, shieldose_si_model):
        """不同探测器应产生不同结果。"""
        kwargs = dict(
            depths=0.5,
            electron_energies=[0.1, 1.0, 5.0],
            electron_flux=[1.0, 0.5, 0.1],
            tinter=1.0,
        )
        result_al = shieldose_al_model.calculate(**kwargs)
        result_si = shieldose_si_model.calculate(**kwargs)
        assert result_al["dose_slab"].shape == result_si["dose_slab"].shape
        assert not np.array_equal(result_al["dose_slab"], result_si["dose_slab"])
