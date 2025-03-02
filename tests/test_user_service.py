import pytest

from src.dao.impl.user import UserDao
from src.model.user import UserCreate
from src.service.impl.user import UserService


@pytest.fixture
def user_service():
    user_dao = UserDao()
    return UserService(user_dao)


def test_get_user(user_service):
    user = user_service.get_user(1)
    assert user is not None
    assert user.name == "John Doe"


def test_create_user(user_service):
    new_user = UserCreate(name="Alice")
    created_user = user_service.create_user(new_user)
    assert created_user.id == 11
    assert created_user.name == "Alice"
