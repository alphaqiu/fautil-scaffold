import pytest

from src.dao.impl.user import UserDao
from src.model.user import UserCreate


@pytest.fixture
def user_dao():
    return UserDao()


def test_get_user(user_dao):
    user = user_dao.get_user(1)
    assert user is not None
    assert user.name == "John Doe"


def test_create_user(user_dao):
    new_user = UserCreate(name="Alice")
    created_user = user_dao.create_user(new_user)
    assert created_user.id == 11
    assert created_user.name == "Alice"
