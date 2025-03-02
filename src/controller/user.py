"""
用户控制器模块。

处理用户相关的HTTP请求，包括用户的增删改查操作。
"""

from typing import List

from fastapi import HTTPException
from injector import Binder, Module, inject, singleton
from loguru import logger

from src.core.cbv import APIView, route
from src.core.setup import setup
from src.model.user import User, UserCreate
from src.service.user_protocol import UserServiceProtocol


@setup()
@singleton
class UserController(APIView):
    """
    用户控制器。

    处理用户相关的HTTP请求，提供RESTful API接口。
    """

    path = "/user"
    user_service: UserServiceProtocol

    @inject
    def __init__(self, user_service: UserServiceProtocol):
        """
        初始化用户控制器。

        参数:
            user_service: 用户服务
        """
        self.user_service = user_service

    @route("/", methods=["GET", "OPTIONS"], response_model=List[User])
    async def list_users(self):
        """
        获取所有用户。

        返回:
            用户列表
        """
        logger.info("获取所有用户")
        return self.user_service.get_users()

    @route("/", methods=["POST", "OPTIONS"], status_code=201, response_model=None)
    async def create_user(self, user: UserCreate):
        """
        创建新用户。

        参数:
            user: 用户创建模型

        返回:
            无返回内容，状态码201
        """
        self.user_service.create_user(user)
        return None

    @route("/{user_id}", methods=["GET", "OPTIONS"], response_model=User)
    async def get_user(self, user_id: int):
        """
        根据ID获取用户。

        参数:
            user_id: 用户ID

        返回:
            用户对象

        异常:
            HTTPException: 如果用户不存在，返回404
        """
        user = self.user_service.get_user(user_id)
        if user is None:
            logger.warning(f"用户 {user_id} 不存在")
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @route("/{user_id}", methods=["PUT", "OPTIONS"], response_model=User)
    async def update_user(self, user_id: int, user: UserCreate):
        """
        更新用户信息。

        参数:
            user_id: 用户ID
            user: 用户更新模型

        返回:
            更新后的用户对象

        异常:
            HTTPException: 如果用户不存在，返回404
        """
        updated_user = self.user_service.update_user(user_id, user)
        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user

    @route(
        "/{user_id}",
        methods=["DELETE", "OPTIONS"],
        status_code=204,
        response_model=None,
    )
    async def delete_user(self, user_id: int):
        """
        删除用户。

        参数:
            user_id: 用户ID

        返回:
            无返回内容，状态码204
        """
        self.user_service.delete_user(user_id)
        return None


class UserControllerModule(Module):
    """
    用户控制器模块。

    用于依赖注入配置。
    """

    def configure(self, binder: Binder) -> None:
        """
        配置依赖注入绑定。

        参数:
            binder: 依赖注入绑定器
        """
        binder.bind(UserController, scope=singleton)
