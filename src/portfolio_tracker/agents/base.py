"""Minimal Gemini JSON agent wrapper."""

from __future__ import annotations

import json
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class _GeminiModels(Protocol):
    def generate_content(self, **kwargs: object): ...


class _GeminiClient(Protocol):
    models: _GeminiModels


class GeminiJsonAgent(Generic[SchemaT]):
    def __init__(
        self,
        *,
        name: str,
        model: str,
        prompt: str,
        output_schema: type[SchemaT],
        client: _GeminiClient,
    ) -> None:
        self.name = name
        self.model = model
        self.prompt = prompt
        self.output_schema = output_schema
        self.client = client

    def run(self, input_payload: Any) -> SchemaT:
        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(input_payload),
            config={
                "response_mime_type": "application/json",
                "response_schema": self.output_schema.model_json_schema(),
            },
        )
        return self.output_schema.model_validate(json.loads(response.text))

    def _contents(self, input_payload: Any) -> str:
        if isinstance(input_payload, str):
            serialized_input = input_payload
        else:
            serialized_input = json.dumps(input_payload, default=str)
        return f"{self.prompt}\n\nInput:\n{serialized_input}"
