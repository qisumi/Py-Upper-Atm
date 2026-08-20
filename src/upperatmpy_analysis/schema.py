"""Strict, JSON-serializable schemas for atmospheric analyses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


SUPPORTED_LANGUAGES = ("zh", "en")
SUPPORTED_METRICS = (
    "bias",
    "mae",
    "rmse",
    "max_abs_difference",
    "mean_relative_difference_percent",
    "mean_ratio",
)


@dataclass(frozen=True)
class QuantitySpec:
    """Definition of one canonical output quantity."""

    name: str
    unit: str
    title_zh: str
    title_en: str
    description_zh: str = ""
    description_en: str = ""

    def title(self, language: str) -> str:
        return self.title_zh if language == "zh" else self.title_en

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelSpec:
    """Machine-readable metadata used to validate and execute a model."""

    name: str
    group: str
    title_zh: str
    title_en: str
    description_zh: str
    description_en: str
    required_inputs: Tuple[str, ...]
    optional_inputs: Tuple[str, ...]
    quantities: Tuple[str, ...]
    validity: Mapping[str, Tuple[float, float]]
    citations: Tuple[str, ...] = ()
    notes_zh: Tuple[str, ...] = ()
    notes_en: Tuple[str, ...] = ()

    def title(self, language: str) -> str:
        return self.title_zh if language == "zh" else self.title_en

    def description(self, language: str) -> str:
        return self.description_zh if language == "zh" else self.description_en

    def notes(self, language: str) -> Tuple[str, ...]:
        return self.notes_zh if language == "zh" else self.notes_en

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["validity"] = {
            key: [float(bounds[0]), float(bounds[1])]
            for key, bounds in self.validity.items()
        }
        return value


@dataclass
class AnalysisPlan:
    """A validated, reproducible plan for deterministic model comparison."""

    models: List[str]
    inputs: Dict[str, Any]
    quantities: List[str] = field(default_factory=list)
    baseline: Optional[str] = None
    metrics: List[str] = field(default_factory=lambda: list(SUPPORTED_METRICS))
    language: str = "zh"
    title: Optional[str] = None

    def __post_init__(self) -> None:
        self.models = [str(item) for item in self.models]
        self.inputs = dict(self.inputs)
        self.quantities = [str(item) for item in self.quantities]
        self.metrics = [str(item) for item in self.metrics]
        self.language = str(self.language).lower()
        if self.baseline is None and self.models:
            self.baseline = self.models[0]
        self.validate_basic()

    def validate_basic(self) -> None:
        if len(self.models) < 2:
            raise ValueError("模型比较至少需要两个模型 / comparison needs at least two models")
        if len(set(self.models)) != len(self.models):
            raise ValueError("models 不得重复 / models must be unique")
        if not self.inputs:
            raise ValueError("inputs 不得为空 / inputs must not be empty")
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError("language 必须为 zh 或 en")
        if self.baseline not in self.models:
            raise ValueError("baseline 必须包含在 models 中 / baseline must be in models")
        if not self.metrics:
            raise ValueError("metrics 不得为空 / metrics must not be empty")
        unknown_metrics = sorted(set(self.metrics) - set(SUPPORTED_METRICS))
        if unknown_metrics:
            raise ValueError("不支持的指标 / unsupported metrics: " + ", ".join(unknown_metrics))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "models": list(self.models),
            "inputs": _json_compatible(self.inputs),
            "quantities": list(self.quantities),
            "baseline": self.baseline,
            "metrics": list(self.metrics),
            "language": self.language,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AnalysisPlan":
        allowed = {
            "models",
            "inputs",
            "quantities",
            "baseline",
            "metrics",
            "language",
            "title",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError("AnalysisPlan 包含未知字段: " + ", ".join(unknown))
        if "models" not in value or "inputs" not in value:
            raise ValueError("AnalysisPlan 必须包含 models 和 inputs")
        return cls(
            models=list(value["models"]),
            inputs={key: item for key, item in dict(value["inputs"]).items() if item is not None},
            quantities=list(value.get("quantities", [])),
            baseline=value.get("baseline"),
            metrics=list(value.get("metrics", SUPPORTED_METRICS)),
            language=str(value.get("language", "zh")),
            title=value.get("title"),
        )


def analysis_plan_json_schema() -> Dict[str, Any]:
    """Return the strict JSON Schema used by optional AI planners."""

    number_or_grid: Dict[str, Any] = {
        "anyOf": [
            {"type": "number"},
            {"type": "array", "items": {"type": "number"}, "minItems": 1},
            {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "stop": {"type": "number"},
                    "step": {"type": ["number", "null"]},
                    "num": {"type": ["integer", "null"], "minimum": 2},
                },
                "required": ["start", "stop", "step", "num"],
                "additionalProperties": False,
            },
            {"type": "null"},
        ]
    }
    canonical_inputs = (
        "year",
        "day_of_year",
        "utsec",
        "alt_km",
        "lat_deg",
        "lon_deg",
        "f107a",
        "f107",
        "local_time_hours",
        "ap7",
    )
    return {
        "type": "object",
        "properties": {
            "models": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
            },
            "inputs": {
                "type": "object",
                "properties": {name: number_or_grid for name in canonical_inputs},
                "required": list(canonical_inputs),
                "additionalProperties": False,
            },
            "quantities": {"type": "array", "items": {"type": "string"}},
            "baseline": {"type": "string"},
            "metrics": {
                "type": "array",
                "items": {"type": "string", "enum": list(SUPPORTED_METRICS)},
                "minItems": 1,
            },
            "language": {"type": "string", "enum": list(SUPPORTED_LANGUAGES)},
            "title": {"type": ["string", "null"]},
        },
        "required": [
            "models",
            "inputs",
            "quantities",
            "baseline",
            "metrics",
            "language",
            "title",
        ],
        "additionalProperties": False,
    }


def _json_compatible(value: Any) -> Any:
    """Convert array-like and scalar-like values without importing NumPy."""

    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_compatible(value.tolist())
    if hasattr(value, "item"):
        return value.item()
    return value


def ensure_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Sequence):
        return value
    return [value]
