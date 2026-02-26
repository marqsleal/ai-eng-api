import httpx
import pytest

from app.core.settings import settings
from app.main import app, app_factory


@pytest.fixture(autouse=True)
def disable_ollama_startup_check(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_STARTUP_CHECK_ENABLED", False)


async def test_swagger_ui_is_available():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(settings.SWAGGER_UI_PATH)

    assert response.status_code == 200
    assert "Swagger UI" in response.text


async def test_openapi_json_is_available():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(settings.OPENAPI_JSON_PATH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == settings.SERVICE_NAME
    assert "paths" in payload


async def test_openapi_includes_standard_error_response_model():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(settings.OPENAPI_JSON_PATH)

    payload = response.json()
    users_path = payload["paths"]["/users/{user_id}"]["get"]
    responses = users_path["responses"]
    assert "404" in responses
    assert responses["404"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )


async def test_openapi_includes_typed_list_query_parameters():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(settings.OPENAPI_JSON_PATH)

    payload = response.json()
    users_list = payload["paths"]["/users"]["get"]
    parameters = {param["name"]: param for param in users_list["parameters"]}
    assert "limit" in parameters
    assert "offset" in parameters
    assert "order_by" in parameters
    assert parameters["order_by"]["schema"]["$ref"] == "#/components/schemas/UsersOrderBy"


async def test_swagger_ui_is_disabled_when_openapi_is_disabled(monkeypatch):
    monkeypatch.setattr(settings, "SWAGGER_UI_ENABLED", True)
    monkeypatch.setattr(settings, "OPENAPI_ENABLED", False)
    custom_app = app_factory()

    transport = httpx.ASGITransport(app=custom_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        docs_response = await client.get(settings.SWAGGER_UI_PATH)
        openapi_response = await client.get(settings.OPENAPI_JSON_PATH)

    assert docs_response.status_code == 404
    assert openapi_response.status_code == 404


async def test_swagger_and_openapi_custom_paths(monkeypatch):
    monkeypatch.setattr(settings, "SWAGGER_UI_ENABLED", True)
    monkeypatch.setattr(settings, "OPENAPI_ENABLED", True)
    monkeypatch.setattr(settings, "SWAGGER_UI_PATH", "/reference")
    monkeypatch.setattr(settings, "OPENAPI_JSON_PATH", "/schema.json")
    custom_app = app_factory()

    transport = httpx.ASGITransport(app=custom_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        docs_response = await client.get("/reference")
        openapi_response = await client.get("/schema.json")

    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text
    assert openapi_response.status_code == 200
