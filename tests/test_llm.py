import httpx
import pytest

from app.models.model_version import ModelVersion
from app.services.llm.base import (
    LLMGenerationResult,
    LLMProviderNotSupportedError,
    LLMResponseValidationError,
    LLMTransportError,
)
from app.services.llm.ollama import OllamaLLMClient
from app.services.llm.service import generate_conversation_response, run_ollama_startup_checks


class FakeHTTPResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://localhost:11434/api/generate")
            response = httpx.Response(500)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class FakeAsyncClientSuccess:
    last_url: str | None = None
    last_json: dict | None = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict):
        FakeAsyncClientSuccess.last_url = url
        FakeAsyncClientSuccess.last_json = json
        return FakeHTTPResponse(
            {
                "response": "hello from ollama",
                "prompt_eval_count": 11,
                "eval_count": 7,
                "total_duration": 250_000_000,
            }
        )


class FakeAsyncClientInvalidResponse:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, _url: str, json: dict):
        return FakeHTTPResponse({"prompt_eval_count": 10, "eval_count": 3, "total_duration": 1000})


class FakeAsyncClientTransportError:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, _url: str, json: dict):
        request = httpx.Request("POST", "http://localhost:11434/api/generate")
        raise httpx.ConnectError("connection failed", request=request)


class FakeAsyncClientListModelsSuccess:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url: str):
        return FakeHTTPResponse(
            {
                "models": [
                    {"name": "llama3.2:3b"},
                    {"name": "llama3.1:8b-instruct"},
                ]
            }
        )


class FakeAsyncClientListModelsInvalidResponse:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url: str):
        return FakeHTTPResponse({"models": [{"name": ""}]})


async def test_ollama_generate_success(monkeypatch):
    monkeypatch.setattr("app.services.llm.ollama.httpx.AsyncClient", FakeAsyncClientSuccess)
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout_seconds=10.0)

    result = await client.generate(
        model="llama3.1:8b-instruct",
        prompt="hello",
        temperature=0.3,
        top_p=0.9,
        max_tokens=64,
    )

    assert result == LLMGenerationResult(
        response="hello from ollama",
        input_tokens=11,
        output_tokens=7,
        total_tokens=18,
        latency_ms=250,
    )
    assert FakeAsyncClientSuccess.last_url == "http://localhost:11434/api/generate"
    assert FakeAsyncClientSuccess.last_json is not None
    assert FakeAsyncClientSuccess.last_json["model"] == "llama3.1:8b-instruct"
    assert FakeAsyncClientSuccess.last_json["prompt"] == "hello"
    assert FakeAsyncClientSuccess.last_json["stream"] is False
    assert FakeAsyncClientSuccess.last_json["options"] == {
        "temperature": 0.3,
        "top_p": 0.9,
        "num_predict": 64,
    }


async def test_ollama_generate_invalid_response_raises_validation_error(monkeypatch):
    monkeypatch.setattr("app.services.llm.ollama.httpx.AsyncClient", FakeAsyncClientInvalidResponse)
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout_seconds=10.0)

    with pytest.raises(LLMResponseValidationError) as err:
        await client.generate(model="llama3.1:8b-instruct", prompt="hello")
    assert err.value.provider == "ollama"
    assert err.value.retriable is False


async def test_ollama_generate_transport_error_raises_transport_error(monkeypatch):
    monkeypatch.setattr("app.services.llm.ollama.httpx.AsyncClient", FakeAsyncClientTransportError)
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout_seconds=10.0)

    with pytest.raises(LLMTransportError) as err:
        await client.generate(model="llama3.1:8b-instruct", prompt="hello")
    assert err.value.provider == "ollama"
    assert err.value.retriable is True


async def test_generate_conversation_response_unsupported_provider_raises():
    model_version = ModelVersion(provider="openai", model_name="gpt-4.1", version_tag="v1")

    with pytest.raises(LLMProviderNotSupportedError) as err:
        await generate_conversation_response(
            model_version=model_version,
            prompt="hello",
        )
    assert err.value.provider == "openai"
    assert err.value.retriable is False


async def test_generate_conversation_response_ollama_delegates(monkeypatch):
    async def fake_generate(self, **kwargs):
        assert kwargs["model"] == "llama3.1:8b-instruct"
        assert kwargs["prompt"] == "hello"
        return LLMGenerationResult(response="ok")

    monkeypatch.setattr("app.services.llm.ollama.OllamaLLMClient.generate", fake_generate)
    model_version = ModelVersion(
        provider="ollama",
        model_name="llama3.1:8b-instruct",
        version_tag="v1",
    )

    result = await generate_conversation_response(model_version=model_version, prompt="hello")
    assert result.response == "ok"


async def test_ollama_list_models_success(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm.ollama.httpx.AsyncClient",
        FakeAsyncClientListModelsSuccess,
    )
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout_seconds=10.0)

    models = await client.list_models()
    assert models == ["llama3.2:3b", "llama3.1:8b-instruct"]


async def test_ollama_list_models_invalid_response_raises_validation_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm.ollama.httpx.AsyncClient",
        FakeAsyncClientListModelsInvalidResponse,
    )
    client = OllamaLLMClient(base_url="http://localhost:11434", timeout_seconds=10.0)

    with pytest.raises(LLMResponseValidationError):
        await client.list_models()


async def test_run_ollama_startup_checks_reachability_failure_raises(monkeypatch):
    async def fake_list_models(self):
        raise LLMTransportError("down", provider="ollama", retriable=True)

    monkeypatch.setattr("app.services.llm.ollama.OllamaLLMClient.list_models", fake_list_models)
    monkeypatch.setattr("app.services.llm.service.settings.OLLAMA_STARTUP_CHECK_ENABLED", True)

    with pytest.raises(RuntimeError) as err:
        await run_ollama_startup_checks()
    assert "could not reach Ollama" in str(err.value)


async def test_run_ollama_startup_checks_missing_default_model_raises(monkeypatch):
    async def fake_list_models(self):
        return ["another-model"]

    monkeypatch.setattr("app.services.llm.ollama.OllamaLLMClient.list_models", fake_list_models)
    monkeypatch.setattr("app.services.llm.service.settings.OLLAMA_STARTUP_CHECK_ENABLED", True)
    monkeypatch.setattr("app.services.llm.service.settings.OLLAMA_DEFAULT_MODEL", "llama3.2:3b")

    with pytest.raises(RuntimeError) as err:
        await run_ollama_startup_checks()
    assert "is not available" in str(err.value)
