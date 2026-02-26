from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import TextClause

from app.api.endpoints.conversations import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    patch_conversation,
)
from app.api.endpoints.model_versions import (
    create_model_version,
    delete_model_version,
    get_model_version,
    list_model_versions,
    patch_model_version,
)
from app.api.endpoints.users import create_user, delete_user, get_user, patch_user
from app.api.schemas.conversation import ConversationCreate, ConversationPatch
from app.api.schemas.model_version import ModelVersionCreate, ModelVersionPatch
from app.api.schemas.user import UserCreate, UserPatch
from app.models.conversation import Conversation
from app.models.model_version import ModelVersion
from app.models.user import User


class FakeResultScalars:
    def __init__(self, data: list[object]) -> None:
        self._data = data

    def all(self):
        return list(self._data)


class FakeResult:
    def __init__(self, data: list[object]) -> None:
        self._data = data

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None

    def scalars(self):
        return FakeResultScalars(self._data)


class FakeAsyncDB:
    def __init__(self) -> None:
        self.users: list[User] = []
        self.model_versions: list[ModelVersion] = []
        self.conversations: list[Conversation] = []
        self._pending: list[object] = []

    def add(self, obj: object) -> None:
        self._pending.append(obj)

    async def commit(self) -> None:
        now = datetime.now(UTC)
        for obj in self._pending:
            if isinstance(obj, User):
                if any(existing.email == obj.email for existing in self.users):
                    raise IntegrityError("duplicate email", {}, Exception("duplicate email"))
                if getattr(obj, "id", None) is None:
                    obj.id = uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = now
                if getattr(obj, "is_active", None) is None:
                    obj.is_active = True
                self.users.append(obj)
            elif isinstance(obj, ModelVersion):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = now
                if getattr(obj, "is_active", None) is None:
                    obj.is_active = True
                self.model_versions.append(obj)
            elif isinstance(obj, Conversation):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid4()
                if getattr(obj, "created_at", None) is None:
                    obj.created_at = now
                if getattr(obj, "is_active", None) is None:
                    obj.is_active = True
                self.conversations.append(obj)
        self._pending.clear()

    async def rollback(self) -> None:
        self._pending.clear()

    async def refresh(self, _obj: object) -> None:
        return None

    async def execute(self, statement):
        if isinstance(statement, TextClause):
            return FakeResult([])

        model = statement.column_descriptions[0]["entity"]
        if model is User:
            source = self.users
        elif model is ModelVersion:
            source = self.model_versions
        else:
            source = self.conversations

        data = list(source)
        for condition in statement._where_criteria:
            right = getattr(condition, "right", None)
            target_value = getattr(right, "value", None)
            if target_value is None:
                right_text = str(right).lower()
                if right_text == "true":
                    target_value = True
                elif right_text == "false":
                    target_value = False
            column_name = getattr(getattr(condition, "left", None), "name", None)
            if target_value is not None and column_name:
                data = [item for item in data if getattr(item, column_name, None) == target_value]

        return FakeResult(data)


@pytest.fixture
def fake_db():
    return FakeAsyncDB()


async def test_create_user_and_get_user(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)
    assert user.email == "ana@example.com"
    assert user.id is not None

    loaded = await get_user(user.id, fake_db)
    assert loaded.email == "ana@example.com"


async def test_create_user_duplicate_email_returns_409(fake_db: FakeAsyncDB):
    await create_user(UserCreate(email="ana@example.com"), fake_db)

    with pytest.raises(HTTPException) as err:
        await create_user(UserCreate(email="ana@example.com"), fake_db)
    assert err.value.status_code == 409
    assert err.value.detail == "Email already exists"


async def test_create_and_list_model_versions(fake_db: FakeAsyncDB):
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )
    assert model_version.id is not None
    assert model_version.provider == "openai"

    listed = await list_model_versions(fake_db)
    assert len(listed) == 1

    loaded = await get_model_version(model_version.id, fake_db)
    assert loaded.id == model_version.id


async def test_create_conversation_and_filter_by_user(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    conversation = await create_conversation(
        ConversationCreate(
            user_id=user.id,
            model_version_id=model_version.id,
            prompt="hello",
            response="world",
            temperature=0.1,
        ),
        fake_db,
    )
    assert conversation.id is not None
    assert conversation.prompt == "hello"

    filtered = await list_conversations(fake_db, user_id=user.id)
    assert len(filtered) == 1
    assert filtered[0].id == conversation.id

    loaded = await get_conversation(conversation.id, fake_db)
    assert loaded.response == "world"


async def test_create_conversation_missing_user_returns_404(fake_db: FakeAsyncDB):
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    with pytest.raises(HTTPException) as err:
        await create_conversation(
            ConversationCreate(
                user_id=uuid4(),
                model_version_id=model_version.id,
                prompt="hello",
                response="world",
            ),
            fake_db,
        )
    assert err.value.status_code == 404
    assert err.value.detail == "User not found"


async def test_get_missing_conversation_returns_404(fake_db: FakeAsyncDB):
    with pytest.raises(HTTPException) as err:
        await get_conversation(uuid4(), fake_db)
    assert err.value.status_code == 404
    assert err.value.detail == "Conversation not found"


async def test_patch_user_updates_email(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)

    updated = await patch_user(user.id, UserPatch(email="bea@example.com"), fake_db)

    assert updated.email == "bea@example.com"


async def test_patch_model_version_updates_version_tag(fake_db: FakeAsyncDB):
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    updated = await patch_model_version(
        model_version.id, ModelVersionPatch(version_tag="2026-02-26"), fake_db
    )

    assert updated.version_tag == "2026-02-26"


async def test_patch_conversation_updates_prompt_and_temperature(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )
    conversation = await create_conversation(
        ConversationCreate(
            user_id=user.id,
            model_version_id=model_version.id,
            prompt="old",
            response="world",
            temperature=0.1,
        ),
        fake_db,
    )

    updated = await patch_conversation(
        conversation.id,
        ConversationPatch(prompt="new", temperature=0.3),
        fake_db,
    )

    assert updated.prompt == "new"
    assert updated.temperature == 0.3


async def test_patch_missing_user_returns_404(fake_db: FakeAsyncDB):
    with pytest.raises(HTTPException) as err:
        await patch_user(uuid4(), UserPatch(email="x@example.com"), fake_db)
    assert err.value.status_code == 404
    assert err.value.detail == "User not found"


async def test_delete_user_soft_deletes(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)

    await delete_user(user.id, fake_db)

    assert user.is_active is False


async def test_delete_model_version_soft_deletes(fake_db: FakeAsyncDB):
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    await delete_model_version(model_version.id, fake_db)

    assert model_version.is_active is False


async def test_delete_conversation_soft_deletes(fake_db: FakeAsyncDB):
    user = await create_user(UserCreate(email="ana@example.com"), fake_db)
    model_version = await create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )
    conversation = await create_conversation(
        ConversationCreate(
            user_id=user.id,
            model_version_id=model_version.id,
            prompt="hello",
            response="world",
        ),
        fake_db,
    )

    await delete_conversation(conversation.id, fake_db)

    assert conversation.is_active is False
