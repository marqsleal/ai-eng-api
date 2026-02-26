import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.llm.base import (
    LLMGenerationResult,
    LLMResponseValidationError,
    LLMTransportError,
)


class OllamaOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    num_predict: int | None = Field(default=None, ge=1)


class OllamaGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    stream: bool = False
    options: OllamaOptions | None = None


class OllamaGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    response: str = Field(min_length=1)
    prompt_eval_count: int | None = Field(default=None, ge=0)
    eval_count: int | None = Field(default=None, ge=0)
    total_duration: int | None = Field(default=None, ge=0)


class OllamaLLMClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMGenerationResult:
        options_data: dict[str, float | int] = {}
        if temperature is not None:
            options_data["temperature"] = temperature
        if top_p is not None:
            options_data["top_p"] = top_p
        if max_tokens is not None:
            options_data["num_predict"] = max_tokens

        options = OllamaOptions.model_validate(options_data) if options_data else None
        payload = OllamaGenerateRequest(
            model=model,
            prompt=prompt,
            stream=False,
            options=options,
        ).model_dump(exclude_none=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as err:
            raise LLMTransportError(
                "Failed to call Ollama API",
                provider="ollama",
                retriable=True,
            ) from err

        try:
            parsed_response = OllamaGenerateResponse.model_validate(response.json())
        except (ValidationError, ValueError) as err:
            raise LLMResponseValidationError(
                "Invalid response from Ollama API",
                provider="ollama",
                retriable=False,
            ) from err

        input_tokens = parsed_response.prompt_eval_count
        output_tokens = parsed_response.eval_count
        total_tokens = None
        if input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens

        latency_ms = None
        total_duration_ns = parsed_response.total_duration
        if total_duration_ns is not None:
            latency_ms = int(total_duration_ns / 1_000_000)

        return LLMGenerationResult(
            response=parsed_response.response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )
