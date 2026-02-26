import httpx

from app.core.settings import settings
from app.main import app, app_factory


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
