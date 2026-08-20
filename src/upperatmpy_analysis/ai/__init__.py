"""Optional AI planning and evidence explanation."""

from .explainer import explain_report
from .planner import detect_language, plan_from_text
from .providers import AIProvider, OpenAIProvider

__all__ = [
    "AIProvider",
    "OpenAIProvider",
    "detect_language",
    "plan_from_text",
    "explain_report",
]
