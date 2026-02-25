from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.endpoints.conversations import (
    create_conversation,
    get_conversation,
    list_conversations,
)
from app.api.endpoints.model_versions import (
    create_model_version,
    get_model_version,
    list_model_versions,
)
from app.api.endpoints.users import create_user, get_user
from app.api.schemas.conversation import ConversationCreate
from app.api.schemas.model_version import ModelVersionCreate
from app.api.schemas.user import UserCreate
from app.models.conversation import Conversation
from app.models.model_version import ModelVersion
from app.models.user import User


class FakeQuery:
    def __init__(self, data: list[object]) -> None:
        self._data = data

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, *conditions):
        for condition in conditions:
            target_value = getattr(getattr(condition, "right", None), "value", None)
            left = getattr(condition, "left", None)
            column_name = getattr(left, "name", None)
            if target_value is not None and column_name:
                self._data = [
                    item for item in self._data if getattr(item, column_name, None) == target_value
                ]
        return self

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return list(self._data)


class FakeDB:
    def __init__(self) -> None:
        self.users: list[User] = []
        self.model_versions: list[ModelVersion] = []
        self.conversations: list[Conversation] = []
        self._pending: list[object] = []

    def add(self, obj: object) -> None:
        self._pending.append(obj)

    def commit(self) -> None:
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

    def rollback(self) -> None:
        self._pending.clear()

    def refresh(self, _obj: object) -> None:
        return None

    def get(self, model: type, model_id):
        if model is User:
            source = self.users
        elif model is ModelVersion:
            source = self.model_versions
        elif model is Conversation:
            source = self.conversations
        else:
            source = []
        return next((item for item in source if item.id == model_id), None)

    def query(self, model: type) -> FakeQuery:
        if model is User:
            return FakeQuery(self.users)
        if model is ModelVersion:
            return FakeQuery(self.model_versions)
        return FakeQuery(self.conversations)


@pytest.fixture
def fake_db():
    return FakeDB()


def test_create_user_and_get_user(fake_db: FakeDB):
    user = create_user(UserCreate(email="ana@example.com"), fake_db)
    assert user.email == "ana@example.com"
    assert user.id is not None

    loaded = get_user(user.id, fake_db)
    assert loaded.email == "ana@example.com"


def test_create_user_duplicate_email_returns_409(fake_db: FakeDB):
    create_user(UserCreate(email="ana@example.com"), fake_db)

    with pytest.raises(HTTPException) as err:
        create_user(UserCreate(email="ana@example.com"), fake_db)
    assert err.value.status_code == 409
    assert err.value.detail == "Email already exists"


def test_create_and_list_model_versions(fake_db: FakeDB):
    model_version = create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )
    assert model_version.id is not None
    assert model_version.provider == "openai"

    listed = list_model_versions(fake_db)
    assert len(listed) == 1

    loaded = get_model_version(model_version.id, fake_db)
    assert loaded.id == model_version.id


def test_create_conversation_and_filter_by_user(fake_db: FakeDB):
    user = create_user(UserCreate(email="ana@example.com"), fake_db)
    model_version = create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    conversation = create_conversation(
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

    filtered = list_conversations(fake_db, user_id=user.id)
    assert len(filtered) == 1
    assert filtered[0].id == conversation.id

    loaded = get_conversation(conversation.id, fake_db)
    assert loaded.response == "world"


def test_create_conversation_missing_user_returns_404(fake_db: FakeDB):
    model_version = create_model_version(
        ModelVersionCreate(provider="openai", model_name="gpt-4.1", version_tag="2026-02-25"),
        fake_db,
    )

    with pytest.raises(HTTPException) as err:
        create_conversation(
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


def test_get_missing_conversation_returns_404(fake_db: FakeDB):
    with pytest.raises(HTTPException) as err:
        get_conversation(uuid4(), fake_db)
    assert err.value.status_code == 404
    assert err.value.detail == "Conversation not found"
