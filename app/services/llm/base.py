from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonEmptyString = Annotated[str, Field(min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class LLMGenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response: NonEmptyString
    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    total_tokens: NonNegativeInt | None = None
    latency_ms: NonNegativeInt | None = None


class LLMError(Exception):
    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retriable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.retriable = retriable


class LLMProviderNotSupportedError(LLMError):
    pass


class LLMTransportError(LLMError):
    pass


class LLMResponseValidationError(LLMError):
    pass
