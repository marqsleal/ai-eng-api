import httpx
import pytest
from fastapi import FastAPI

from app.api.endpoints.conversations import conversations_router
from app.api.endpoints.model_versions import model_versions_router
from app.api.endpoints.users import users_router
from app.core.errors import register_exception_handlers
from app.core.settings import settings
from app.database.dependencies import get_db


class _DummyDB:
    pass


@pytest.fixture
def contract_app():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(users_router)
    app.include_router(model_versions_router)
    app.include_router(conversations_router)
    return app


@pytest.fixture(autouse=True)
def override_db_dependency(contract_app):
    async def _override_get_db():
        yield _DummyDB()

    contract_app.dependency_overrides[get_db] = _override_get_db
    yield
    contract_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def disable_ollama_startup_check(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_STARTUP_CHECK_ENABLED", False)


@pytest.fixture
def transport(contract_app, disable_ollama_startup_check):
    return httpx.ASGITransport(app=contract_app)


@pytest.fixture(autouse=True)
def stub_list_repositories(monkeypatch):
    async def fake_users_list_active(self, *, limit=50, offset=0, order_by="created_at_desc"):
        return []

    async def fake_model_versions_list_active(
        self, *, limit=50, offset=0, order_by="created_at_desc"
    ):
        return []

    async def fake_conversations_list_active(
        self, *, user_id=None, limit=50, offset=0, order_by="created_at_desc"
    ):
        return []

    monkeypatch.setattr(
        "app.repositories.user.UserRepository.list_active",
        fake_users_list_active,
    )
    monkeypatch.setattr(
        "app.repositories.model_version.ModelVersionRepository.list_active",
        fake_model_versions_list_active,
    )
    monkeypatch.setattr(
        "app.repositories.conversation.ConversationRepository.list_active",
        fake_conversations_list_active,
    )


async def test_users_list_default_query_values_are_applied(monkeypatch, transport):
    captured: dict[str, object] = {}

    async def fake_list_active(self, *, limit=50, offset=0, order_by="created_at_desc"):
        captured.update({"limit": limit, "offset": offset, "order_by": order_by})
        return []

    monkeypatch.setattr("app.repositories.user.UserRepository.list_active", fake_list_active)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")

    assert response.status_code == 200
    assert response.json() == []
    assert captured == {"limit": 50, "offset": 0, "order_by": "created_at_desc"}


async def test_users_list_valid_query_values_are_applied(monkeypatch, transport):
    captured: dict[str, object] = {}

    async def fake_list_active(self, *, limit=50, offset=0, order_by="created_at_desc"):
        captured.update({"limit": limit, "offset": offset, "order_by": order_by})
        return []

    monkeypatch.setattr("app.repositories.user.UserRepository.list_active", fake_list_active)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users?limit=20&offset=5&order_by=email_desc")

    assert response.status_code == 200
    assert captured == {"limit": 20, "offset": 5, "order_by": "email_desc"}


async def test_model_versions_list_valid_query_values_are_applied(monkeypatch, transport):
    captured: dict[str, object] = {}

    async def fake_list_active(self, *, limit=50, offset=0, order_by="created_at_desc"):
        captured.update({"limit": limit, "offset": offset, "order_by": order_by})
        return []

    monkeypatch.setattr(
        "app.repositories.model_version.ModelVersionRepository.list_active",
        fake_list_active,
    )

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/model-versions?limit=10&offset=2&order_by=model_name_asc")

    assert response.status_code == 200
    assert captured == {"limit": 10, "offset": 2, "order_by": "model_name_asc"}


async def test_conversations_list_valid_query_values_are_applied(monkeypatch, transport):
    captured: dict[str, object] = {}

    async def fake_list_active(
        self, *, user_id=None, limit=50, offset=0, order_by="created_at_desc"
    ):
        captured.update(
            {"user_id": str(user_id), "limit": limit, "offset": offset, "order_by": order_by}
        )
        return []

    monkeypatch.setattr(
        "app.repositories.conversation.ConversationRepository.list_active",
        fake_list_active,
    )

    user_id = "11111111-1111-1111-1111-111111111111"
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/conversations?user_id={user_id}&limit=15&offset=3&order_by=created_at_asc"
        )

    assert response.status_code == 200
    assert captured == {
        "user_id": user_id,
        "limit": 15,
        "offset": 3,
        "order_by": "created_at_asc",
    }


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/users", "order_by=invalid"),
        ("/users", "limit=0"),
        ("/users", "limit=101"),
        ("/users", "offset=-1"),
        ("/model-versions", "order_by=invalid"),
        ("/conversations", "order_by=invalid"),
    ],
)
async def test_list_routes_invalid_query_params_return_422_contract(path, query, transport):
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{path}?{query}")

    payload = response.json()
    assert response.status_code == 422
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Request validation failed"
    assert isinstance(payload["details"], list)
    assert len(payload["details"]) > 0


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/users", "limit=1&offset=0&order_by=created_at_desc"),
        ("/users", "limit=100&offset=0&order_by=email_asc"),
        ("/model-versions", "limit=1&offset=0&order_by=created_at_desc"),
        ("/model-versions", "limit=100&offset=0&order_by=model_name_desc"),
        ("/conversations", "limit=1&offset=0&order_by=created_at_desc"),
        ("/conversations", "limit=100&offset=0&order_by=latency_ms_desc"),
    ],
)
async def test_list_routes_boundary_query_values_are_accepted(path, query, transport):
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"{path}?{query}")

    assert response.status_code == 200
