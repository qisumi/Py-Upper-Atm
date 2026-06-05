"""SHIELDOSE 辐射剂量模型。

计算铝屏蔽层后的辐射吸收剂量，支持探测器材料 Al、H2O、Si、SiO2，
三种几何构型：有限平板透射面、半无限介质、球体中心。

基于 S. M. Seltzer (NIST) 1980 年开发的 SHIELDOSE 代码，
参考 NBS Technical Note 1116 (1980)。
"""

from __future__ import annotations

__all__ = ["Model"]

import ctypes
import os
import re
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

import numpy as np
import numpy.typing as npt

from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

# DETECTOR_NAMES: idet -> 名称
DETECTOR_NAMES: Dict[int, str] = {
    1: "Al",
    2: "H2O",
    3: "Si",
    4: "SiO2",
}

# COMPONENT_NAMES: 输出矩阵第二维索引 -> 分量名称
COMPONENT_NAMES: Dict[int, str] = {
    0: "electron",
    1: "bremsstrahlung",
    2: "electron_brems",
    3: "trapped_proton",
    4: "solar_proton",
}

_EXP_FLOAT_RE = re.compile(
    r"[+-]?(?:\d+(?:\.\s*\d*)?|\.\s*\d+)[EDed]\s*[+-]?\s*\d+"
)
_BREMS_HEADER_RE = re.compile(r"^\s*\d+\.\d{5}\s+\d+\.\d{5}\s*$")


def _parse_fortran_ints(line: str) -> list:
    """从一行中解析整数。"""
    return [int(x) for x in line.split() if x.strip()]


def _parse_fixed_width_floats(line: str, width: int) -> list[float]:
    """按 Fortran 固定宽度浮点字段解析一行。"""
    line = line.rstrip("\r\n")
    zpos = line.find("Z")
    if zpos >= 0:
        line = line[:zpos]

    values = []
    for pos in range(0, len(line), width):
        field = line[pos:pos + width]
        if not field.strip():
            continue
        values.append(_parse_fortran_float_field(field))
    return values


def _parse_fortran_float_field(field: str) -> float:
    """解析单个 Fortran 浮点字段，兼容指数符号中的空格。"""
    token = field.strip().replace("D", "E").replace("d", "E").replace("e", "E")
    if token in {"", ".", ".E", ".E-", ".E+"}:
        return 0.0
    if "E" not in token:
        return float(token.replace(" ", ""))

    mantissa, exponent = token.split("E", 1)
    mantissa = mantissa.replace(" ", "")
    exponent = exponent.strip().replace(" ", "")
    if mantissa in {"", ".", "+.", "-."}:
        return 0.0
    if not exponent:
        return 0.0
    if not exponent.startswith(("+", "-")):
        exponent = f"+{exponent}"
    return float(f"{mantissa}E{exponent}")


def _parse_flexible_fortran_floats(line: str) -> list[float]:
    """解析带空格指数符号的 Fortran 科学计数法数值。"""
    zpos = line.find("Z")
    if zpos >= 0:
        line = line[:zpos]
    return [_parse_fortran_float_field(token) for token in _EXP_FLOAT_RE.findall(line)]


def _strip_listing_marker(line: str) -> str:
    zpos = line.find("Z")
    if zpos >= 0:
        line = line[:zpos]
    return line.strip()


def _is_brems_header_line(line: str) -> bool:
    return bool(_BREMS_HEADER_RE.match(_strip_listing_marker(line)))


class _FortranDataReader:
    """逐条 READ 语句读取固定格式 Fortran 数据。"""

    def __init__(self, lines: Sequence[str], start_idx: int) -> None:
        self._lines = lines
        self._idx = start_idx

    def read_values(self, count: int, width: int) -> list[float]:
        values: list[float] = []
        while len(values) < count:
            if self._idx >= len(self._lines):
                raise ValueError(f"数据文件在读取第 {count} 个值时意外结束")
            values.extend(_parse_fixed_width_floats(self._lines[self._idx], width))
            self._idx += 1
        return values[:count]


def _pad_table(values: Sequence[float], length: int) -> np.ndarray:
    table = np.zeros(length, dtype=float)
    n = min(len(values), length)
    if n:
        table[:n] = np.asarray(values[:n], dtype=float)
    return table


def _read_electron_tables(
    lines: Sequence[str],
    start_idx: int,
    lemax: int,
) -> tuple[list[np.ndarray], int]:
    tables: list[np.ndarray] = []
    current: list[float] = []
    idx = start_idx
    while idx < len(lines) and len(tables) < 8:
        values = _parse_fixed_width_floats(lines[idx], width=10)
        if values:
            current.extend(values)
            if len(values) == 1:
                tables.append(_pad_table(current, lemax))
                current = []
        idx += 1

    if len(tables) != 8:
        raise ValueError(f"电子剂量表数量异常：期望 8，实际 {len(tables)}")
    return tables, idx


def _split_brems_tables(lines: Sequence[str], lbmax: int) -> list[np.ndarray]:
    tables: list[np.ndarray] = []
    for index in range(8):
        if index < 7:
            table_lines = lines[index * 7:(index + 1) * 7]
        else:
            table_lines = lines[index * 7:]
        values: list[float] = []
        for line in table_lines:
            values.extend(_parse_flexible_fortran_floats(line))
        tables.append(_pad_table(values, lbmax))
    return tables


def _find_next_line(lines: Sequence[str], start_idx: int, predicate) -> int:
    for idx in range(start_idx, len(lines)):
        if predicate(lines[idx]):
            return idx
    return len(lines)


def _resolve_data_file(
    data_dir: Optional[Union[str, Path]] = None,
    *,
    auto_download: bool = True,
) -> Path:
    """定位 shieldose.dat 数据文件路径。"""
    root = ensure_model_data(
        "shieldose",
        data_dir=data_dir,
        auto_download=auto_download,
    )
    candidates = [
        root / "shieldose.dat",
        root / "shieldosedata" / "shieldose.dat",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(
        "找不到 shieldose.dat 数据文件。"
        f"已搜索：{', '.join(str(c) for c in candidates)}"
    )


def _read_shieldose_data(filepath: Path, detector: int = 1) -> dict:
    """解析 SHIELDOSE 数据文件，返回查找表数据。"""
    with open(filepath) as f:
        lines = f.readlines()

    # 跳过空行，找到维度行
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    dims = _parse_fortran_ints(lines[idx])
    idx += 1
    mpmax, lpmax, kmax, memax, lemax, mbmax, lbmax = dims
    reader = _FortranDataReader(lines, idx)

    # --- 质子剂量数据 ---
    # 只读取前 MPMAX 个质子能量
    ep = np.zeros(mpmax)
    rp = np.zeros(mpmax)
    dp = np.zeros((lpmax, mpmax))  # dp(depth, energy)

    for m in range(mpmax):
        vals = reader.read_values(2, width=12)
        ep[m] = vals[0]
        rp[m] = vals[1]

        for det in range(1, 5):
            vals = reader.read_values(lpmax, width=12)
            if det == detector:
                dp[:, m] = vals

    # --- 电子数据 ---
    er = np.array(reader.read_values(kmax, width=12))
    re_arr = np.array(reader.read_values(kmax, width=12))

    # 电子剂量数据
    ee = np.zeros(memax)
    de = np.zeros((lemax, 2, memax))  # de(depth, table, energy)

    for m in range(memax):
        vals = _parse_fixed_width_floats(lines[reader._idx], width=12)
        if not vals:
            raise ValueError("电子能量行为空")
        ee[m] = vals[0]
        reader._idx += 1

        tables, next_idx = _read_electron_tables(lines, reader._idx, lemax)
        selected = (detector - 1) * 2
        de[:, 0, m] = tables[selected]
        de[:, 1, m] = tables[selected + 1]
        reader._idx = next_idx

    # --- 轫致辐射数据 ---
    zb = np.array(reader.read_values(lbmax, width=9))

    eb = np.zeros(mbmax)
    db = np.zeros((lbmax, 2, mbmax))  # db(depth, table, energy)

    for m in range(mbmax):
        vals = reader.read_values(2, width=12)
        eb[m] = vals[0]
        renorm = vals[1]

        next_idx = _find_next_line(lines, reader._idx, _is_brems_header_line)
        tables = _split_brems_tables(lines[reader._idx:next_idx], lbmax)
        selected = (detector - 1) * 2
        db[:, 0, m] = tables[selected] / renorm
        db[:, 1, m] = tables[selected + 1] / renorm
        reader._idx = next_idx

    # 转换到 log 空间
    ep_log = np.log(ep)
    rp_log = np.log(rp)
    er_log = np.log(er)
    re_log = np.log(re_arr)
    ee_log = np.log(ee)
    zb_log = np.log(1000.0 * zb)
    eb_log = np.log(eb)

    return {
        'mpmax': mpmax, 'lpmax': lpmax, 'kmax': kmax,
        'memax': memax, 'lemax': lemax, 'mbmax': mbmax, 'lbmax': lbmax,
        'ep_log': ep_log, 'rp_log': rp_log, 'dp': dp,
        'er_log': er_log, 're_log': re_log,
        'ee_log': ee_log, 'de': de,
        'zb_log': zb_log, 'eb_log': eb_log, 'db': db,
    }


class Model:
    """SHIELDOSE 辐射剂量模型。

    计算铝屏蔽层后的辐射吸收剂量（rads），
    支持三种几何构型和四种探测器材料。

    参数:
        detector: 探测器材料编号 (1=Al, 2=H2O, 3=Si, 4=SiO2)
        unit: 屏蔽深度单位 (1=mils, 2=g/cm², 3=mm)
        data_dir: 数据文件目录，默认自动查找
        auto_download: 是否自动下载缺失的数据文件
        dll_path: DLL 路径，默认自动查找
    """

    def __init__(
        self,
        detector: int = 1,
        unit: int = 2,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if detector not in DETECTOR_NAMES:
            raise ValueError(
                f"无效的探测器编号 {detector}，"
                f"有效值：{list(DETECTOR_NAMES.keys())}"
            )
        if unit not in (1, 2, 3):
            raise ValueError(
                f"无效的单位编号 {unit}，有效值：1 (mils), 2 (g/cm²), 3 (mm)"
            )

        self._detector = detector
        self._unit = unit

        # 定位数据文件
        data_path = _resolve_data_file(data_dir, auto_download=auto_download)

        # 加载 DLL
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "shieldose.dll" if os.name == "nt" else "libshieldose.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = ctypes.CDLL(str(self._dll_path))

        # 设置函数签名
        self._setup_functions()

        # 解析数据文件并传给 Fortran
        self._data = _read_shieldose_data(data_path, detector=self._detector)
        self._set_data(self._data)

    def _setup_functions(self) -> None:
        dll = self._dll

        # shieldose_set_data(...)
        dll.shieldose_set_data.argtypes = [
            ctypes.c_int,  # mpmax
            ctypes.c_int,  # lpmax
            ctypes.c_int,  # kmax
            ctypes.c_int,  # memax
            ctypes.c_int,  # lemax
            ctypes.c_int,  # mbmax
            ctypes.c_int,  # lbmax
            ctypes.POINTER(ctypes.c_double),  # ep_log
            ctypes.POINTER(ctypes.c_double),  # rp_log
            ctypes.POINTER(ctypes.c_double),  # dp (lpmax, mpmax)
            ctypes.POINTER(ctypes.c_double),  # er_log
            ctypes.POINTER(ctypes.c_double),  # re_log
            ctypes.POINTER(ctypes.c_double),  # ee_log
            ctypes.POINTER(ctypes.c_double),  # de (lemax, 2, memax)
            ctypes.POINTER(ctypes.c_double),  # zb_log
            ctypes.POINTER(ctypes.c_double),  # eb_log
            ctypes.POINTER(ctypes.c_double),  # db (lbmax, 2, mbmax)
        ]
        dll.shieldose_set_data.restype = None

        # shieldose_calc_dose(...)
        dll.shieldose_calc_dose.argtypes = [
            ctypes.POINTER(ctypes.c_float),  # depths
            ctypes.c_int,                     # ndepth
            ctypes.c_int,                     # idet
            ctypes.c_int,                     # iunt
            ctypes.POINTER(ctypes.c_float),  # solar_energies
            ctypes.POINTER(ctypes.c_float),  # solar_flux
            ctypes.c_int,                     # nsolar
            ctypes.POINTER(ctypes.c_float),  # prot_energies
            ctypes.POINTER(ctypes.c_float),  # prot_flux
            ctypes.c_int,                     # nprot
            ctypes.POINTER(ctypes.c_float),  # elec_energies
            ctypes.POINTER(ctypes.c_float),  # elec_flux
            ctypes.c_int,                     # nelec
            ctypes.c_float,                   # eunit
            ctypes.c_float,                   # tinter
            ctypes.POINTER(ctypes.c_float),  # dose_slab
            ctypes.POINTER(ctypes.c_float),  # dose_semi
            ctypes.POINTER(ctypes.c_float),  # dose_sphere
        ]
        dll.shieldose_calc_dose.restype = None

        # shieldose_is_loaded() -> int
        dll.shieldose_is_loaded.argtypes = []
        dll.shieldose_is_loaded.restype = ctypes.c_int

    def _set_data(self, data: dict) -> None:
        """将解析后的数据传给 Fortran。"""
        c_double_p = ctypes.POINTER(ctypes.c_double)

        # dp 的形状是 (lpmax, mpmax)，Fortran 期望 (lpmax, mpmax)
        dp = np.asfortranarray(data['dp'], dtype=np.float64)
        de = np.asfortranarray(data['de'], dtype=np.float64)
        db = np.asfortranarray(data['db'], dtype=np.float64)

        self._dll.shieldose_set_data(
            ctypes.c_int(data['mpmax']),
            ctypes.c_int(data['lpmax']),
            ctypes.c_int(data['kmax']),
            ctypes.c_int(data['memax']),
            ctypes.c_int(data['lemax']),
            ctypes.c_int(data['mbmax']),
            ctypes.c_int(data['lbmax']),
            data['ep_log'].ctypes.data_as(c_double_p),
            data['rp_log'].ctypes.data_as(c_double_p),
            dp.ctypes.data_as(c_double_p),
            data['er_log'].ctypes.data_as(c_double_p),
            data['re_log'].ctypes.data_as(c_double_p),
            data['ee_log'].ctypes.data_as(c_double_p),
            de.ctypes.data_as(c_double_p),
            data['zb_log'].ctypes.data_as(c_double_p),
            data['eb_log'].ctypes.data_as(c_double_p),
            db.ctypes.data_as(c_double_p),
        )

    @property
    def detector(self) -> int:
        """当前探测器编号。"""
        return self._detector

    @property
    def detector_name(self) -> str:
        """当前探测器名称。"""
        return DETECTOR_NAMES[self._detector]

    @property
    def unit(self) -> int:
        """当前深度单位编号。"""
        return self._unit

    @property
    def unit_name(self) -> str:
        """当前深度单位名称。"""
        return {1: "mils", 2: "g/cm²", 3: "mm"}[self._unit]

    def calculate(
        self,
        *,
        depths: Union[float, npt.ArrayLike],
        solar_proton_energies: Optional[npt.ArrayLike] = None,
        solar_proton_flux: Optional[npt.ArrayLike] = None,
        trapped_proton_energies: Optional[npt.ArrayLike] = None,
        trapped_proton_flux: Optional[npt.ArrayLike] = None,
        electron_energies: Optional[npt.ArrayLike] = None,
        electron_flux: Optional[npt.ArrayLike] = None,
        eunit: float = 1.0,
        tinter: float = 1.0,
    ) -> Dict[str, object]:
        """计算辐射剂量。

        参数:
            depths: 屏蔽深度，标量或数组（单位由构造函数 unit 参数决定）
            solar_proton_energies: 太阳质子能谱能量点 (MeV)，至少 3 个
            solar_proton_flux: 太阳质子能谱通量 (/Energy/cm²)，与能量点一一对应
            trapped_proton_energies: 捕获质子能谱能量点 (MeV)，至少 3 个
            trapped_proton_flux: 捕获质子能谱通量 (/Energy/cm²/Time)，与能量点一一对应
            electron_energies: 电子能谱能量点 (MeV)，至少 3 个
            electron_flux: 电子能谱通量 (/Energy/cm²/Time)，与能量点一一对应
            eunit: 能量单位转换因子（如 /keV 则设为 1000），默认 1.0 (/MeV)
            tinter: 任务持续时间（单位时间倍数），默认 1.0

        返回:
            dict: 包含以下键:
                - depths: 输入深度数组
                - detector: 探测器编号和名称
                - unit: 深度单位编号和名称
                - dose_slab: 有限平板透射面剂量 [ndepth, 5]
                - dose_semi: 半无限介质剂量 [ndepth, 5]
                - dose_sphere: 球体中心剂量 [ndepth, 5]
                各剂量矩阵的 5 列分别为:
                  [电子, 轫致辐射, 电子+轫致, 捕获质子, 太阳质子] (rads)
        """
        scalar_input = np.ndim(depths) == 0
        depths_arr = np.atleast_1d(np.asarray(depths, dtype=np.float32))
        if np.any(depths_arr <= 0):
            raise ValueError("depths 必须全部为正值")
        ndepth = len(depths_arr)

        # 处理能谱
        def _prep_spectrum(
            energies: Optional[npt.ArrayLike],
            flux: Optional[npt.ArrayLike],
        ) -> tuple:
            if energies is None or flux is None:
                return np.array([], dtype=np.float32), np.array([], dtype=np.float32)
            e = np.asarray(energies, dtype=np.float32).ravel()
            f = np.asarray(flux, dtype=np.float32).ravel()
            if len(e) != len(f):
                raise ValueError("能量和通量数组长度必须相同")
            if len(e) < 3:
                raise ValueError("能谱至少需要 3 个数据点")
            if len(e) > 101:
                raise ValueError("能谱最多支持 101 个数据点")
            return e, f

        sol_e, sol_f = _prep_spectrum(solar_proton_energies, solar_proton_flux)
        prt_e, prt_f = _prep_spectrum(trapped_proton_energies, trapped_proton_flux)
        ele_e, ele_f = _prep_spectrum(electron_energies, electron_flux)

        self._set_data(self._data)

        # 分配输出数组
        dose_slab = np.zeros((ndepth, 5), dtype=np.float32, order="F")
        dose_semi = np.zeros((ndepth, 5), dtype=np.float32, order="F")
        dose_sphere = np.zeros((ndepth, 5), dtype=np.float32, order="F")

        # 调用 Fortran
        self._dll.shieldose_calc_dose(
            depths_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_int(ndepth),
            ctypes.c_int(self._detector),
            ctypes.c_int(self._unit),
            sol_e.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            sol_f.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_int(len(sol_e)),
            prt_e.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            prt_f.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_int(len(prt_e)),
            ele_e.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ele_f.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_int(len(ele_e)),
            ctypes.c_float(eunit),
            ctypes.c_float(tinter),
            dose_slab.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            dose_semi.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            dose_sphere.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        )

        # 标量输入时压缩维度
        if scalar_input:
            depths_out = float(depths_arr[0])
            dose_slab_out = dose_slab[0]
            dose_semi_out = dose_semi[0]
            dose_sphere_out = dose_sphere[0]
        else:
            depths_out = depths_arr
            dose_slab_out = dose_slab
            dose_semi_out = dose_semi
            dose_sphere_out = dose_sphere

        return {
            "depths": depths_out,
            "detector": {"id": self._detector, "name": self.detector_name},
            "unit": {"id": self._unit, "name": self.unit_name},
            "dose_slab": dose_slab_out,
            "dose_semi": dose_semi_out,
            "dose_sphere": dose_sphere_out,
            "eunit": eunit,
            "tinter": tinter,
        }
