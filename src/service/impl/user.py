"""
用户服务.
"""

from typing import Optional

from injector import Binder, Module, inject, singleton

from src.dao.user_protocol import UserDaoProtocol
from src.model.user import User, UserCreate
from src.service.user_protocol import UserServiceProtocol


@singleton
class UserService(UserServiceProtocol):
    """
    用户服务.
    """

    user_dao: UserDaoProtocol

    @inject
    def __init__(self, user_dao: UserDaoProtocol):
        """
        初始化用户服务.
        """
        self.user_dao = user_dao

    def get_user(self, user_id: int) -> Optional[User]:
        """
        获取用户.
        """
        return self.user_dao.get_user(user_id)

    def get_users(self) -> list[User]:
        """
        获取所有用户.
        """
        return self.user_dao.get_users()

    def create_user(self, user: UserCreate) -> User:
        """
        创建用户.
        """
        return self.user_dao.create_user(user)

    def update_user(self, user_id: int, user: UserCreate) -> User:
        """
        更新用户.
        """
        return self.user_dao.update_user(user_id, user)

    def delete_user(self, user_id: int) -> None:
        """
        删除用户.
        """
        self.user_dao.delete_user(user_id)


class UserServiceModule(Module):
    """
    用户服务模块.
    """

    def configure(self, binder: Binder) -> None:
        """
        配置用户服务模块.
        """
        binder.bind(UserServiceProtocol, to=UserService, scope=singleton)
