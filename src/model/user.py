"""
用户模型模块。

定义了用户相关的数据模型，包括User和UserCreate。
"""

from pydantic import BaseModel


class User(BaseModel):
    """
    用户模型。

    属性:
        id: 用户ID
        name: 用户名称
    """

    id: int
    name: str


class UserCreate(BaseModel):
    """
    用户创建模型。

    属性:
        name: 用户名称
    """

    name: str
