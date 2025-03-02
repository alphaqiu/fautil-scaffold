"""
用户服务协议模块。

定义了用户服务的接口协议，规定了用户服务的方法。
"""

from typing import Optional, Protocol

from src.model.user import User, UserCreate


class UserServiceProtocol(Protocol):
    """
    用户服务协议。

    定义了用户服务的基本操作方法。
    """

    def get_user(self, user_id: int) -> Optional[User]:
        """
        根据用户ID获取用户。

        参数:
            user_id: 用户ID

        返回:
            Optional[User]: 用户对象或None
        """

    def get_users(self) -> list[User]:
        """
        获取所有用户。

        返回:
            list[User]: 用户列表
        """

    def create_user(self, user: UserCreate) -> User:
        """
        创建新用户。

        参数:
            user: UserCreate对象

        返回:
            User: 创建的用户对象
        """

    def update_user(self, user_id: int, user: UserCreate) -> User:
        """
        更新用户信息。

        参数:
            user_id: 用户ID
            user: UserCreate对象

        返回:
            User: 更新后的用户对象
        """

    def delete_user(self, user_id: int) -> None:
        """
        删除用户。

        参数:
            user_id: 用户ID
        """
