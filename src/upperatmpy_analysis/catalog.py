"""Bilingual model and quantity catalog for safe comparisons."""

from __future__ import annotations

from typing import Dict, List, Optional

from .schema import ModelSpec, QuantitySpec


_SPECIES = ("He", "O", "N2", "O2", "Ar", "H", "N", "AnomalousO")

QUANTITIES: Dict[str, QuantitySpec] = {
    "T_local_K": QuantitySpec(
        "T_local_K", "K", "局地温度", "Local temperature", "模型位置的温度", "Temperature at the model location"
    ),
    "T_exo_K": QuantitySpec(
        "T_exo_K", "K", "外逸层温度", "Exospheric temperature", "模型外逸层温度", "Model exospheric temperature"
    ),
    "total_mass_density_kg_m3": QuantitySpec(
        "total_mass_density_kg_m3", "kg/m^3", "总质量密度", "Total mass density"
    ),
    "H2O_cm3": QuantitySpec(
        "H2O_cm3", "cm^-3", "水分子数密度", "H2O number density",
        "由 MLS H2O 体积混合比和 MSIS2 总空气数密度推导。",
        "Derived from MLS H2O volume mixing ratio and MSIS2 total air number density.",
    ),
    "H2O_vmr_ppmv": QuantitySpec(
        "H2O_vmr_ppmv", "ppmv", "水汽体积混合比", "H2O volume mixing ratio",
        "固定多年逐月 MLS 气候态；低于顶部压力边界时为受约束外推。",
        "Fixed multi-year monthly MLS climatology; constrained extrapolation above its pressure ceiling.",
    ),
    "B_north_nT": QuantitySpec("B_north_nT", "nT", "北向磁场", "Northward magnetic field"),
    "B_east_nT": QuantitySpec("B_east_nT", "nT", "东向磁场", "Eastward magnetic field"),
    "B_down_nT": QuantitySpec("B_down_nT", "nT", "向下磁场", "Downward magnetic field"),
    "B_abs_nT": QuantitySpec("B_abs_nT", "nT", "总磁场强度", "Total magnetic field intensity"),
    "H_nT": QuantitySpec("H_nT", "nT", "水平磁场强度", "Horizontal magnetic field intensity"),
    "inclination_deg": QuantitySpec("inclination_deg", "deg", "磁倾角", "Magnetic inclination"),
    "declination_deg": QuantitySpec("declination_deg", "deg", "磁偏角", "Magnetic declination"),
}
for _species in _SPECIES:
    QUANTITIES[_species + "_cm3"] = QuantitySpec(
        _species + "_cm3",
        "cm^-3",
        _species + " 数密度",
        _species + " number density",
    )


_NEUTRAL_INPUTS = (
    "year",
    "day_of_year",
    "utsec",
    "alt_km",
    "lat_deg",
    "lon_deg",
    "f107a",
    "f107",
)
_NEUTRAL_OPTIONAL = ("local_time_hours", "ap7")
_NEUTRAL_VALIDITY = {
    "day_of_year": (1.0, 366.0),
    "utsec": (0.0, 86400.0),
    "lat_deg": (-90.0, 90.0),
    "lon_deg": (-180.0, 360.0),
    "f107a": (0.0, 500.0),
    "f107": (0.0, 500.0),
}
_NEUTRAL_BASE_QUANTITIES = (
    "T_local_K",
    "T_exo_K",
    "He_cm3",
    "O_cm3",
    "N2_cm3",
    "O2_cm3",
    "Ar_cm3",
    "H_cm3",
    "N_cm3",
)
_GEOMAG_INPUTS = ("year", "lat_deg", "lon_deg", "alt_km")
_GEOMAG_QUANTITIES = (
    "B_north_nT",
    "B_east_nT",
    "B_down_nT",
    "B_abs_nT",
    "H_nT",
    "inclination_deg",
    "declination_deg",
)
_GEOMAG_VALIDITY = {
    "lat_deg": (-90.0, 90.0),
    "lon_deg": (-180.0, 360.0),
    "alt_km": (0.0, 1000.0),
}


MODELS: Dict[str, ModelSpec] = {
    "MSIS2": ModelSpec(
        "MSIS2", "neutral_atmosphere", "NRLMSIS 2.0", "NRLMSIS 2.0",
        "现代经验中性大气模型。", "Modern empirical neutral-atmosphere model.",
        _NEUTRAL_INPUTS, _NEUTRAL_OPTIONAL,
        _NEUTRAL_BASE_QUANTITIES + ("AnomalousO_cm3", "total_mass_density_kg_m3"),
        dict(_NEUTRAL_VALIDITY, alt_km=(0.0, 1000.0)),
        ("https://doi.org/10.1029/2020EA001321",),
    ),
    "MSIS2H2O": ModelSpec(
        "MSIS2H2O", "neutral_atmosphere", "NRLMSIS 2.0 + MLS H2O", "NRLMSIS 2.0 + MLS H2O",
        "MSIS2 干大气与 Aura MLS 2005--2024 月度水汽气候态的组合。",
        "MSIS2 dry atmosphere combined with the 2005--2024 monthly Aura MLS H2O climatology.",
        _NEUTRAL_INPUTS, _NEUTRAL_OPTIONAL,
        _NEUTRAL_BASE_QUANTITIES + ("AnomalousO_cm3", "total_mass_density_kg_m3", "H2O_cm3", "H2O_vmr_ppmv"),
        dict(_NEUTRAL_VALIDITY, alt_km=(20.0, 120.0)),
        ("https://doi.org/10.1029/2020EA001321", "https://doi.org/10.5067/Aura/MLS/DATA/3538"),
        (
            "H2O 是固定多年逐月气候态，不是指定年份的逐日观测；MLS 顶部以上为受约束外推。",
        ),
        (
            "H2O is a fixed multi-year monthly climatology, not daily weather for the requested year; values above the MLS ceiling are constrained extrapolations.",
        ),
    ),
    "MSIS00": ModelSpec(
        "MSIS00", "neutral_atmosphere", "NRLMSISE-00", "NRLMSISE-00",
        "NRLMSISE-00 中性大气模型。", "NRLMSISE-00 neutral-atmosphere model.",
        _NEUTRAL_INPUTS, _NEUTRAL_OPTIONAL,
        _NEUTRAL_BASE_QUANTITIES + ("AnomalousO_cm3", "total_mass_density_kg_m3"),
        dict(_NEUTRAL_VALIDITY, alt_km=(0.0, 1000.0)),
        ("https://doi.org/10.1029/2002JA009430",),
    ),
    "MSIS86": ModelSpec(
        "MSIS86", "neutral_atmosphere", "MSIS-86", "MSIS-86",
        "用于 85 km 以上的历史中性大气模型。", "Historical neutral-atmosphere model for altitudes above 85 km.",
        _NEUTRAL_INPUTS, _NEUTRAL_OPTIONAL,
        _NEUTRAL_BASE_QUANTITIES + ("total_mass_density_kg_m3",),
        dict(_NEUTRAL_VALIDITY, alt_km=(85.0, 1000.0)),
        (),
        ("与覆盖低层大气的模型比较时，高度交集从 85 km 开始。",),
        ("Its shared altitude domain starts at 85 km when compared with lower-atmosphere models.",),
    ),
    "MSISE90": ModelSpec(
        "MSISE90", "neutral_atmosphere", "MSISE-90", "MSISE-90",
        "向低层大气延伸的 MSIS-86 模型。", "MSIS-86 extension into the lower atmosphere.",
        _NEUTRAL_INPUTS, _NEUTRAL_OPTIONAL,
        _NEUTRAL_BASE_QUANTITIES + ("total_mass_density_kg_m3",),
        dict(_NEUTRAL_VALIDITY, alt_km=(0.0, 1000.0)),
    ),
    "IGRF": ModelSpec(
        "IGRF", "geomagnetic_internal", "国际地磁参考场", "International Geomagnetic Reference Field",
        "带长期更新的地球内部主磁场参考模型。", "Regularly updated reference model of Earth's internal main field.",
        _GEOMAG_INPUTS, (), _GEOMAG_QUANTITIES,
        dict(_GEOMAG_VALIDITY, year=(1900.0, 2030.0)),
        ("https://www.ncei.noaa.gov/products/international-geomagnetic-reference-field",),
    ),
    "GSFC": ModelSpec(
        "GSFC", "geomagnetic_internal", "GSFC 历史地磁场", "GSFC historical geomagnetic field",
        "仓库提供的 GSFC 80/83/87 历史内部磁场模型。", "Historical GSFC 80/83/87 internal-field models supplied by the repository.",
        _GEOMAG_INPUTS, (), _GEOMAG_QUANTITIES, _GEOMAG_VALIDITY,
        (),
        ("默认构造使用 GSFC-87；年份超出模型历元附近时需谨慎解释。",),
        ("The default constructor uses GSFC-87; interpret years far from its epoch cautiously.",),
    ),
    "JensenCain": ModelSpec(
        "JensenCain", "geomagnetic_internal", "Jensen-Cain 1962", "Jensen-Cain 1962",
        "六阶历史内部磁场模型。", "Historical degree-6 internal-field model.",
        _GEOMAG_INPUTS, (), _GEOMAG_QUANTITIES, _GEOMAG_VALIDITY,
        (),
        ("这是历史历元模型，不应当作现代磁场预报。",),
        ("This is a historical-epoch model, not a modern field forecast.",),
    ),
    "MGST80": ModelSpec(
        "MGST80", "geomagnetic_internal", "MGST 1980", "MGST 1980",
        "基于 MAGSAT 的历史内部磁场模型。", "Historical MAGSAT-based internal-field model.",
        _GEOMAG_INPUTS, (), _GEOMAG_QUANTITIES, _GEOMAG_VALIDITY,
        (),
        ("模型无长期变化项，适用于其历史历元附近。",),
        ("The model has no secular variation and is intended near its historical epoch.",),
    ),
    "MGST81": ModelSpec(
        "MGST81", "geomagnetic_internal", "MGST 1981", "MGST 1981",
        "基于 MAGSAT 的历史内部磁场模型。", "Historical MAGSAT-based internal-field model.",
        _GEOMAG_INPUTS, (), _GEOMAG_QUANTITIES, _GEOMAG_VALIDITY,
        (),
        ("模型无长期变化项，适用于其历史历元附近。",),
        ("The model has no secular variation and is intended near its historical epoch.",),
    ),
}


GROUP_DEFAULT_QUANTITIES = {
    "neutral_atmosphere": ("T_local_K", "T_exo_K"),
    "geomagnetic_internal": ("B_abs_nT",),
}


def get_model_spec(name: str) -> ModelSpec:
    try:
        return MODELS[name]
    except KeyError:
        raise ValueError("分析目录中没有模型 / model is not in analysis catalog: " + name)


def get_quantity_spec(name: str) -> QuantitySpec:
    try:
        return QUANTITIES[name]
    except KeyError:
        raise ValueError("未知统一量 / unknown canonical quantity: " + name)


def list_models(group: Optional[str] = None) -> List[ModelSpec]:
    values = list(MODELS.values())
    if group is not None:
        values = [item for item in values if item.group == group]
    return values


def catalog_dict(language: str = "zh") -> Dict[str, object]:
    return {
        "language": language,
        "models": [item.to_dict() for item in list_models()],
        "quantities": [item.to_dict() for item in QUANTITIES.values()],
        "groups": {
            group: list(defaults) for group, defaults in GROUP_DEFAULT_QUANTITIES.items()
        },
    }
