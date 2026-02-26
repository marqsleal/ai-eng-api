import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.errors import register_exception_handlers


class _Payload(BaseModel):
    value: int


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/http-error")
    async def http_error_route():
        raise HTTPException(status_code=404, detail="User not found")

    @app.post("/validation")
    async def validation_route(payload: _Payload):
        return payload.model_dump()

    @app.get("/boom")
    async def boom_route():
        raise RuntimeError("unexpected failure")

    return app


async def test_http_exception_uses_standard_error_contract():
    app = _build_test_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/http-error")

    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "message": "User not found",
        "details": None,
    }


async def test_validation_exception_uses_standard_error_contract():
    app = _build_test_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/validation", json={})

    payload = response.json()
    assert response.status_code == 422
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Request validation failed"
    assert isinstance(payload["details"], list)
    assert len(payload["details"]) > 0


async def test_unexpected_exception_uses_standard_error_contract():
    app = _build_test_app()
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error",
        "message": "Internal Server Error",
        "details": None,
    }
