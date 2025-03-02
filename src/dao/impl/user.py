"""
用户数据访问对象实现模块。

实现了用户数据的访问操作，包括用户的增删改查。
"""

from typing import Optional

from injector import Binder, Module, singleton
from loguru import logger

from src.core.setup import setup
from src.dao.user_protocol import UserDaoProtocol
from src.model.user import User, UserCreate


@setup(protocol=UserDaoProtocol)
@singleton
class UserDao:
    """
    用户数据访问对象实现。

    实现了用户数据的基本操作方法。
    """

    def __init__(self):
        """
        初始化用户数据访问对象。

        创建示例用户数据。
        """
        # self.db = Database()
        self.users = [
            User(id=1, name="John Doe"),
            User(id=2, name="Jane Doe"),
            User(id=3, name="Jim Doe"),
            User(id=4, name="Jill Doe"),
            User(id=5, name="Jack Doe"),
            User(id=6, name="Jill Doe"),
            User(id=7, name="Jack Doe"),
            User(id=8, name="Jill Doe"),
            User(id=9, name="Jack Doe"),
            User(id=10, name="Jill Doe"),
        ]

    def get_user(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户。

        参数:
            user_id: 用户ID

        返回:
            如果找到用户则返回User对象，否则返回None
        """
        max_id = len(self.users)
        if user_id > max_id:
            logger.warning(f"用户ID {user_id} 超出最大ID {max_id}")
            return None
        logger.info(f"获取用户 {user_id}")
        return self.users[user_id - 1]

    def get_users(self) -> list[User]:
        """
        获取所有用户。

        返回:
            用户列表
        """
        return self.users

    def create_user(self, user: UserCreate) -> User:
        """
        创建新用户。

        参数:
            user: 用户创建模型

        返回:
            创建的用户对象
        """
        new_user = User(id=len(self.users) + 1, name=user.name)
        self.users.append(new_user)
        return new_user

    def update_user(self, user_id: int, user: UserCreate) -> User:
        """
        更新用户信息。

        参数:
            user_id: 用户ID
            user: 用户更新模型

        返回:
            更新后的用户对象

        异常:
            ValueError: 如果用户不存在
        """
        found_user = next((user for user in self.users if user.id == user_id), None)
        if found_user is None:
            raise ValueError("User not found")
        found_user.name = user.name
        return found_user

    def delete_user(self, user_id: int) -> None:
        """
        删除用户。

        参数:
            user_id: 用户ID
        """
        self.users = [user for user in self.users if user.id != user_id]


class UserDaoModule(Module):
    """
    用户数据访问对象模块。

    用于依赖注入配置。
    """

    def configure(self, binder: Binder) -> None:
        """
        配置依赖注入绑定。

        参数:
            binder: 依赖注入绑定器
        """
        binder.bind(UserDaoProtocol, to=UserDao, scope=singleton)
