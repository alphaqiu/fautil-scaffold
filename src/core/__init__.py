"""
核心模块包。

包含框架核心功能，如基于类的视图（CBV）、依赖注入设置和路由装饰器等基础功能。
这个包是应用程序的核心部分，提供了构建 RESTful API 的基础组件。
"""

from .cbv import APIView, route, setup_cbv
from .config import (
    AppConfig,
    DBConfig,
    KafkaConfig,
    LogConfig,
    LogLevel,
    MinioConfig,
    RedisConfig,
    Settings,
    load_settings,
)
from .context import (
    RequestContext,
    RequestTimer,
    get_client_ip,
    get_request_context,
    has_request_context,
)
from .setup import setup, setup_modules

__all__ = [
    "setup",
    "APIView",
    "setup_cbv",
    "route",
    "load_settings",
    "setup_modules",
    "RequestContext",
    "RequestTimer",
    "get_request_context",
    "has_request_context",
    "get_client_ip",
    "LogLevel",
    "AppConfig",
    "DBConfig",
    "KafkaConfig",
    "LogConfig",
    "MinioConfig",
    "RedisConfig",
    "Settings",
]
