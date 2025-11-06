"""
NRLMSIS-2.0 Python wrapper (C-ABI shim)
- 单点：calc(...)
- 批量：calc_many(...)
- 工具：doy(...), seconds_of_day(...)
"""

from __future__ import annotations
import os
import sys
import ctypes as C
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

try:
    import numpy as np  # 可选
    _HAS_NUMPY = True
except Exception:
    np = None  # type: ignore
    _HAS_NUMPY = False

__all__ = [
    "NRLMSIS2",
    "MSISResult",
    "doy",
    "seconds_of_day",
]

# -----------------------------
# 工具函数
# -----------------------------


def doy(year: int, month: int, day: int) -> float:
    """将 (year, month, day) 转换为年内日（浮点），不含闰秒。"""
    import datetime as _dt
    d0 = _dt.date(year, 1, 1)
    d = _dt.date(year, month, day)
    return float((d - d0).days + 1)


def seconds_of_day(hour: int, minute: int = 0, second: float = 0.0) -> float:
    """一天内秒数（0~86400），可带小数秒。"""
    return float(hour) * 3600.0 + float(minute) * 60.0 + float(second)


@dataclass
class MSISResult:
    alt_km: float
    T_local_K: float
    T_exo_K: float
    # dn10 顺序由模型定义，这里保留原始数组；上层可自行映射物种名
    dn10: Tuple[float, float, float, float,
                float, float, float, float, float, float]

# -----------------------------
# 主封装
# -----------------------------


class NRLMSIS2:
    """
    C-ABI 封装：基于你提供的 bind(C, name="msiscalc") 包装。
    - precision: "single" 或 "double"（需与 DLL/shim 一致）
    - dll_path: 指定 nrlmsis2.dll 路径；默认在 <包根>/build/nrlmsis2.dll
    - add_mingw_bin: 在 Windows 上把 C:\mingw64\bin 加入 DLL 搜索（缺运行时就开）
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        precision: str = "single",
        add_mingw_bin: bool = False,
        extra_dll_dirs: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        self._precision = precision.lower().strip()
        if self._precision not in ("single", "double"):
            raise ValueError("precision 必须是 'single' 或 'double'")

        # 解析默认 DLL 路径：包根/build/nrlmsis2.dll
        if dll_path is None:
            pkg_root = Path(__file__).resolve().parent
            dll_path = pkg_root / "build" / "nrlmsis2.dll"
        self._dll_path = Path(dll_path)

        # Windows: 显式加 DLL 搜索目录（Python3.8+不会自动查 PATH）
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(self._dll_path.parent))
            if add_mingw_bin and sys.platform.startswith("win"):
                mingw_bin = Path(r"C:\mingw64\bin")
                if mingw_bin.exists():
                    os.add_dll_directory(str(mingw_bin))
            if extra_dll_dirs:
                for p in extra_dll_dirs:
                    pp = Path(p)
                    if pp.exists():
                        os.add_dll_directory(str(pp))

        # 加载 DLL
        self._dll = C.CDLL(str(self._dll_path))

        # 选精度类型
        self._FT = C.c_double if self._precision == "double" else C.c_float

        # 解析 C-ABI 符号
        try:
            self._msiscalc = getattr(self._dll, "msiscalc")
        except AttributeError:
            # 兜底：大写符号
            self._msiscalc = getattr(self._dll, "MSISCALC")

        # 绑定签名：
        # void msiscalc(FT day, FT utsec, FT z, FT lat, FT lon,
        #               FT f107a, FT f107, const FT ap7[7],
        #               FT* t_local, FT dn10[10], FT* t_exo)
        FT = self._FT
        self._msiscalc.argtypes = [
            FT, FT, FT, FT, FT,
            FT, FT, C.POINTER(FT),
            C.POINTER(FT), C.POINTER(FT), C.POINTER(FT),
        ]
        self._msiscalc.restype = None

        # 预分配输出缓冲，减少 GC 压力
        self._dn10_buf = (FT * 10)()
        self._t_local = FT()
        self._t_exo = FT()
        self._ap7_buf = (FT * 7)()

    # -----------------------------
    # 单点计算
    # -----------------------------
    def calc(
        self,
        *,
        day: float,
        utsec: float,
        alt_km: float,
        lat_deg: float,
        lon_deg: float,
        f107a: float,
        f107: float,
        ap7: Optional[Sequence[float]] = None,
    ) -> MSISResult:
        """
        单点计算。
        参数均为标量；ap7 为长度 7 的序列（若 None 则默认全 4.0）。
        返回 MSISResult（包含 T_local, T_exo, dn10）。
        """
        FT = self._FT

        # ap7
        if ap7 is None:
            for i in range(7):
                self._ap7_buf[i] = FT(4.0)
        else:
            if len(ap7) != 7:
                raise ValueError("ap7 长度必须为 7")
            for i, v in enumerate(ap7):
                self._ap7_buf[i] = FT(v)

        # 调用
        self._msiscalc(
            FT(day), FT(utsec), FT(alt_km), FT(lat_deg), FT(lon_deg),
            FT(f107a), FT(f107), self._ap7_buf,
            C.byref(self._t_local), self._dn10_buf, C.byref(self._t_exo),
        )

        dn10 = tuple(float(self._dn10_buf[i]) for i in range(10))
        return MSISResult(
            alt_km=float(alt_km),
            T_local_K=float(self._t_local.value),
            T_exo_K=float(self._t_exo.value),
            dn10=dn10,
        )

    # -----------------------------
    # 批量计算（支持纯 Python & NumPy）
    # -----------------------------
    def calc_many(
        self,
        *,
        day: Union[float, Sequence[float]],
        utsec: Union[float, Sequence[float]],
        alt_km: Union[float, Sequence[float]],
        lat_deg: Union[float, Sequence[float]],
        lon_deg: Union[float, Sequence[float]],
        f107a: Union[float, Sequence[float]],
        f107: Union[float, Sequence[float]],
        ap7: Optional[Union[Sequence[float],
                            Sequence[Sequence[float]]]] = None,
        out_numpy: bool = False,
    ):
        """
        批量计算。广播规则：
        - 标量会自动广播到所有样本；
        - 序列长度需一致；
        - ap7 可为长度 7 的序列（对所有样本复用），或形如 (N,7) 的二维序列（逐样本设置）。
        返回：
        - out_numpy=False：List[MSISResult]
        - out_numpy=True：dict[str, numpy.ndarray]（shape=(N,) 或 (N,10)）
        """
        if _HAS_NUMPY:
            return self._calc_many_numpy(
                day=day, utsec=utsec, alt_km=alt_km, lat_deg=lat_deg, lon_deg=lon_deg,
                f107a=f107a, f107=f107, ap7=ap7, out_numpy=out_numpy
            )
        # 纯 Python 路径
        # 1) 标准化为列表

        def _to_list(x):
            return x if isinstance(x, (list, tuple)) else [x]

        dayL = _to_list(day)
        utsecL = _to_list(utsec)
        altL = _to_list(alt_km)
        latL = _to_list(lat_deg)
        lonL = _to_list(lon_deg)
        f107aL = _to_list(f107a)
        f107L = _to_list(f107)

        # 广播：取最大长度 N
        N = max(len(dayL), len(utsecL), len(altL), len(
            latL), len(lonL), len(f107aL), len(f107L))

        def _get(seq, i):
            return seq[i % len(seq)]

        # ap7 处理
        ap_is_matrix = ap7 is not None and isinstance(
            ap7[0], (list, tuple))  # type: ignore
        if ap7 is None:
            ap_rows = None
        elif ap_is_matrix:
            # (N,7)
            if any(len(row) != 7 for row in ap7):  # type: ignore
                raise ValueError("ap7 二维输入的每行长度都必须为 7")
            if len(ap7) not in (1, N):  # type: ignore
                raise ValueError("ap7 二维输入的行数必须为 1 或 N")
            ap_rows = ap7  # type: ignore
        else:
            if len(ap7) != 7:  # type: ignore
                raise ValueError("ap7 一维输入长度必须为 7")
            ap_rows = [ap7]  # type: ignore

        results: List[MSISResult] = []
        for i in range(N):
            ap_row = None
            if ap_rows is not None:
                ap_row = ap_rows[i % len(ap_rows)]  # type: ignore
            res = self.calc(
                day=float(_get(dayL, i)),
                utsec=float(_get(utsecL, i)),
                alt_km=float(_get(altL, i)),
                lat_deg=float(_get(latL, i)),
                lon_deg=float(_get(lonL, i)),
                f107a=float(_get(f107aL, i)),
                f107=float(_get(f107L, i)),
                ap7=ap_row,  # None → 默认 7*4.0
            )
            results.append(res)

        if not out_numpy:
            return results
        # 转 dict of arrays
        import array
        alt = array.array("d", (r.alt_km for r in results))
        tloc = array.array("d", (r.T_local_K for r in results))
        texo = array.array("d", (r.T_exo_K for r in results))
        dn = [array.array("d", (r.dn10[j] for r in results))
              for j in range(10)]
        return {
            "alt_km": list(alt),
            "T_local_K": list(tloc),
            "T_exo_K": list(texo),
            "dn10": [list(col) for col in dn],  # 列主形式
        }

    # numpy 路径（如可用）
    def _calc_many_numpy(self, **kw):
        assert _HAS_NUMPY
        FT = self._FT
        # 统一成列向量

        def _as_col(x):
            arr = np.array(
                x, dtype=np.float64 if FT is C.c_double else np.float32).reshape(-1)
            return arr

        day = _as_col(kw["day"])
        utsec = _as_col(kw["utsec"])
        alt = _as_col(kw["alt_km"])
        lat = _as_col(kw["lat_deg"])
        lon = _as_col(kw["lon_deg"])
        f107a = _as_col(kw["f107a"])
        f107 = _as_col(kw["f107"])

        N = max(len(day), len(utsec), len(alt), len(
            lat), len(lon), len(f107a), len(f107))

        def _pick(a, i):
            return a[i % len(a)]

        # ap7
        ap7 = kw.get("ap7", None)
        if ap7 is None:
            ap_mat = np.full((N, 7), 4.0, dtype=day.dtype)
        else:
            ap_mat = np.array(ap7, dtype=day.dtype)
            if ap_mat.ndim == 1:
                if ap_mat.shape[0] != 7:
                    raise ValueError("ap7 一维输入长度必须为 7")
                ap_mat = np.tile(ap_mat, (N, 1))
            elif ap_mat.ndim == 2:
                if ap_mat.shape[1] != 7:
                    raise ValueError("ap7 二维输入必须为 (N,7)")
                if ap_mat.shape[0] not in (1, N):
                    raise ValueError("ap7 行数必须为 1 或 N")
                if ap_mat.shape[0] == 1:
                    ap_mat = np.tile(ap_mat, (N, 1))
            else:
                raise ValueError("ap7 维度错误")

        # 输出
        t_local = np.empty((N,), dtype=day.dtype)
        t_exo = np.empty((N,), dtype=day.dtype)
        dn10 = np.empty((N, 10), dtype=day.dtype)

        # 逐样本调用（ctypes 不好直接批量）
        # 若你对吞吐有要求，可以后续用 Cython/numba 包一层
        ap_buf = (FT * 7)()
        dn_buf = (FT * 10)()
        tloc = FT()
        texo = FT()
        for i in range(N):
            for j in range(7):
                ap_buf[j] = FT(ap_mat[i, j])
            self._msiscalc(
                FT(_pick(day, i)), FT(_pick(utsec, i)), FT(_pick(alt, i)),
                FT(_pick(lat, i)), FT(_pick(lon, i)),
                FT(_pick(f107a, i)), FT(_pick(f107, i)),
                ap_buf, C.byref(tloc), dn_buf, C.byref(texo)
            )
            t_local[i] = float(tloc.value)
            t_exo[i] = float(texo.value)
            for j in range(10):
                dn10[i, j] = float(dn_buf[j])

        if kw.get("out_numpy", False):
            return {
                "alt_km": np.array([_pick(alt, i) for i in range(N)], dtype=alt.dtype),
                "T_local_K": t_local,
                "T_exo_K": t_exo,
                "dn10": dn10,   # shape (N,10)
            }
        # 转 List[MSISResult]
        out: List[MSISResult] = []
        for i in range(N):
            out.append(MSISResult(
                alt_km=float(_pick(alt, i)),
                T_local_K=float(t_local[i]),
                T_exo_K=float(t_exo[i]),
                dn10=tuple(float(dn10[i, j]) for j in range(10)),
            ))
        return out
