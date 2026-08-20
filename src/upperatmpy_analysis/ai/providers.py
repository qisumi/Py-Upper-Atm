"""Optional AI providers. Importing this module never imports an AI SDK."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional, Protocol


class AIProvider(Protocol):
    """Minimal interface used by the planner and evidence explainer."""

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Mapping[str, Any],
        schema_name: str,
    ) -> Dict[str, Any]:
        ...

    def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        ...


class OpenAIProvider:
    """OpenAI Responses API adapter loaded only when explicitly instantiated."""

    def __init__(
        self,
        *,
        model: str,
        api_key: Optional[str] = None,
        client: Any = None,
    ) -> None:
        if not model:
            raise ValueError("OpenAI model 不得为空 / model must not be empty")
        self.model = model
        if client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "请安装 upperatmpy[ai] 以启用 OpenAI / install upperatmpy[ai]"
                )
            client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.client = client

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Mapping[str, Any],
        schema_name: str,
    ) -> Dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": dict(schema),
                    "strict": True,
                }
            },
            store=False,
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise RuntimeError("OpenAI Responses API 未返回结构化文本")
        value = json.loads(output_text)
        if not isinstance(value, dict):
            raise ValueError("结构化响应必须为 JSON 对象")
        return value

    def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            store=False,
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise RuntimeError("OpenAI Responses API 未返回文本")
        return str(output_text).strip()
