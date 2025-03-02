"""
核心模块包。

包含框架核心功能，如基于类的视图（CBV）、依赖注入设置和路由装饰器等基础功能。
这个包是应用程序的核心部分，提供了构建 RESTful API 的基础组件。
"""

from .cbv import APIView, route, setup_cbv
from .setup import setup

__all__ = ["setup", "APIView", "setup_cbv", "route"]
