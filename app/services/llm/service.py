from app.core.settings import settings
from app.models.model_version import ModelVersion
from app.services.llm.base import LLMGenerationResult, LLMProviderNotSupportedError
from app.services.llm.ollama import OllamaLLMClient


async def generate_conversation_response(
    model_version: ModelVersion,
    prompt: str,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> LLMGenerationResult:
    provider = model_version.provider.lower()
    if provider != "ollama":
        raise LLMProviderNotSupportedError(
            f"Unsupported LLM provider: {model_version.provider}",
            provider=model_version.provider,
            retriable=False,
        )

    ollama_client = OllamaLLMClient(
        base_url=settings.OLLAMA_BASE_URL,
        timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
    )
    model_name = model_version.model_name.strip() or settings.OLLAMA_DEFAULT_MODEL
    return await ollama_client.generate(
        model=model_name,
        prompt=prompt,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
