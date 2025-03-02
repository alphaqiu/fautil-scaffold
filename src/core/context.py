"""
请求上下文管理模块。

提供请求上下文和跟踪ID的存储和管理功能。
支持在请求处理过程中在不同组件间共享上下文信息。

示例::

    from fastapi import FastAPI, Request, Depends
    from src.core.context import RequestContext, get_request_context, RequestTimer

    app = FastAPI()

    @app.middleware("http")
    async def context_middleware(request: Request, call_next):
        # 生成请求ID
        request_id = RequestContext.generate_request_id()
        # 设置请求ID和请求对象
        RequestContext.set_request_id(request_id)
        RequestContext.set_request(request)

        # 创建计时器
        timer = RequestTimer()

        # 设置自定义上下文数据
        RequestContext.set("client_ip", await get_client_ip(request))

        response = await call_next(request)

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = RequestContext.get_request_id()
        # 添加处理时间到响应头
        response.headers["X-Processing-Time"] = f"{timer.stop():.2f}ms"

        # 请求处理完成后清理上下文
        RequestContext.clear()

        return response
"""

import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from fastapi import Request

# 上下文变量
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_request_var: ContextVar[Optional[Request]] = ContextVar("request", default=None)
_context_storage: ContextVar[Dict[str, Any]] = ContextVar("context_storage", default={})


class RequestContext:
    """
    请求上下文。

    管理请求级别的上下文信息，包括请求ID、路径、方法等。
    提供存储和检索上下文数据的接口。

    示例::

        # 在中间件或依赖项中设置请求上下文
        RequestContext.set_request_id("unique-request-id")
        RequestContext.set_request(request)

        # 在业务逻辑中存储和检索上下文数据
        RequestContext.set("user_id", 12345)
        user_id = RequestContext.get("user_id")

        # 获取所有上下文数据
        all_context = RequestContext.get_all()

        # 请求处理完成后清理上下文
        RequestContext.clear()
    """

    @staticmethod
    def get_request_id() -> str:
        """
        获取当前请求ID。

        Returns:
            当前请求ID，如果不存在则返回空字符串

        示例::

            # 获取当前请求ID
            request_id = RequestContext.get_request_id()

            # 在日志中使用请求ID
            logger.info(f"处理请求 [{request_id}]")

            # 添加到响应头
            response.headers["X-Request-ID"] = RequestContext.get_request_id()
        """
        return _request_id_var.get()

    @staticmethod
    def set_request_id(request_id: str) -> None:
        """
        设置当前请求ID。

        Args:
            request_id: 请求ID

        示例::

            # 在中间件中设置请求ID
            @app.middleware("http")
            async def request_middleware(request: Request, call_next):
                # 从请求头获取请求ID或生成新的
                request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
                RequestContext.set_request_id(request_id)
                return await call_next(request)

            # 手动设置请求ID
            RequestContext.set_request_id("manual-request-id-12345")
        """
        _request_id_var.set(request_id)

    @staticmethod
    def get_request() -> Optional[Request]:
        """
        获取当前请求对象。

        Returns:
            当前请求对象，如果不存在则返回None

        示例::

            # 获取请求对象
            request = RequestContext.get_request()
            if request:
                # 访问请求的属性和方法
                path = request.url.path
                method = request.method
                headers = request.headers
            else:
                # 处理请求不可用的情况
                logger.warning("当前上下文中没有请求对象")
        """
        return _request_var.get()

    @staticmethod
    def set_request(request: Request) -> None:
        """
        设置当前请求对象。

        Args:
            request: 请求对象

        示例::

            # 在中间件中设置请求对象
            @app.middleware("http")
            async def request_middleware(request: Request, call_next):
                RequestContext.set_request(request)
                return await call_next(request)

            # 在依赖项中设置请求对象
            def set_request_in_context(request: Request):
                RequestContext.set_request(request)
                return request

            @app.get("/api/endpoint")
            async def endpoint(request: Request = Depends(set_request_in_context)):
                # 请求已经存储在上下文中
                return {"message": "ok"}
        """
        _request_var.set(request)

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """
        获取上下文数据。

        Args:
            key: 数据键
            default: 默认值

        Returns:
            上下文数据值，如果不存在则返回默认值

        示例::

            # 获取上下文中的用户ID
            user_id = RequestContext.get("user_id")

            # 使用默认值
            language = RequestContext.get("language", "zh-CN")

            # 条件检查
            if RequestContext.get("is_admin", False):
                # 执行管理员特权操作
                pass
        """
        storage = _context_storage.get()
        return storage.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """
        设置上下文数据。

        Args:
            key: 数据键
            value: 数据值

        示例::

            # 设置当前用户ID
            RequestContext.set("user_id", 12345)

            # 存储用户角色
            RequestContext.set("roles", ["admin", "editor"])

            # 存储客户端信息
            RequestContext.set("client_info", {
                "ip": "127.0.0.1",
                "user_agent": "Mozilla/5.0...",
                "language": "zh-CN"
            })

            # 在认证中间件中设置用户信息
            async def auth_middleware(request: Request, call_next):
                user = await authenticate_user(request)
                if user:
                    RequestContext.set("user", user)
                return await call_next(request)
        """
        storage = _context_storage.get().copy()
        storage[key] = value
        _context_storage.set(storage)

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """
        获取所有上下文数据。

        Returns:
            所有上下文数据的副本

        示例::

            # 获取并记录所有上下文数据
            context_data = RequestContext.get_all()
            logger.debug(f"当前请求上下文: {context_data}")

            # 复制上下文数据到响应中
            @app.get("/api/context")
            async def get_context():
                return {
                    "request_id": RequestContext.get_request_id(),
                    "context": RequestContext.get_all()
                }
        """
        return _context_storage.get().copy()

    @staticmethod
    def clear() -> None:
        """
        清除上下文数据。

        示例::

            # 请求处理完成后清理上下文
            @app.middleware("http")
            async def context_middleware(request: Request, call_next):
                try:
                    # 设置上下文
                    RequestContext.set_request(request)
                    response = await call_next(request)
                    return response
                finally:
                    # 确保上下文被清理
                    RequestContext.clear()

            # 手动清理上下文
            def cleanup_context():
                RequestContext.clear()
                logger.debug("已清理请求上下文")
        """
        _context_storage.set({})

    @staticmethod
    def generate_request_id() -> str:
        """
        生成新的请求ID。

        Returns:
            生成的请求ID

        示例::

            # 生成并设置请求ID
            request_id = RequestContext.generate_request_id()
            RequestContext.set_request_id(request_id)

            # 在中间件中使用
            @app.middleware("http")
            async def request_id_middleware(request: Request, call_next):
                # 从请求头获取或生成新的请求ID
                request_id = request.headers.get(
                    "X-Request-ID",
                    RequestContext.generate_request_id()
                )
                RequestContext.set_request_id(request_id)

                response = await call_next(request)

                # 添加到响应头
                response.headers["X-Request-ID"] = request_id
                return response
        """
        return str(uuid.uuid4())


def get_request_context() -> RequestContext:
    """
    获取当前请求上下文。

    Returns:
        RequestContext: 当前请求上下文

    示例::

        # 获取请求上下文
        context = get_request_context()

        # 使用上下文访问信息
        request_id = context.get_request_id()
        user_id = context.get("user_id")

        # 在FastAPI依赖项中使用
        def get_current_user_id():
            context = get_request_context()
            user_id = context.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="需要认证")
            return user_id

        @app.get("/api/profile")
        async def get_profile(user_id: int = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    return RequestContext()


def has_request_context() -> bool:
    """
    检查是否存在请求上下文。

    Returns:
        bool: 如果存在请求上下文则返回True，否则返回False

    示例::

        # 检查是否在请求上下文中运行
        if has_request_context():
            # 在请求上下文中执行的代码
            request_id = RequestContext.get_request_id()
            logger.info(f"处理请求 [{request_id}]")
        else:
            # 不在请求上下文中执行的代码
            logger.info("在请求上下文外执行")

        # 在后台任务中使用
        async def background_task():
            if has_request_context():
                # 使用请求上下文中的信息
                user_id = RequestContext.get("user_id")
            else:
                # 不依赖请求上下文的处理逻辑
                pass
    """
    return bool(_request_var.get())


class RequestTimer:
    """
    请求计时器。

    跟踪请求处理时间。

    示例::

        # 中间件中使用计时器
        @app.middleware("http")
        async def timing_middleware(request: Request, call_next):
            timer = RequestTimer()

            response = await call_next(request)

            # 计算处理时间并添加到响应头
            elapsed = timer.stop()
            response.headers["X-Process-Time"] = f"{elapsed:.2f}ms"

            # 记录处理时间
            logger.info(f"请求处理完成，耗时: {elapsed:.2f}ms")

            return response

        # 分段计时
        timer = RequestTimer()
        # 执行第一阶段
        phase1_result = await do_phase1()
        phase1_time = timer.elapsed_ms()
        logger.debug(f"阶段1完成，耗时: {phase1_time:.2f}ms")

        # 执行第二阶段
        phase2_result = await do_phase2()
        total_time = timer.stop()
        logger.debug(f"阶段2完成，总耗时: {total_time:.2f}ms")
    """

    __slots__ = ("start_time", "end_time")

    def __init__(self):
        """初始化计时器。"""
        self.start_time = time.time()
        self.end_time: Optional[float] = None

    def stop(self) -> float:
        """
        停止计时。

        Returns:
            处理时间（毫秒）

        示例::

            # 创建并使用计时器
            timer = RequestTimer()

            # 执行一些操作
            result = do_some_work()

            # 停止计时并获取耗时
            elapsed_ms = timer.stop()
            logger.info(f"操作耗时: {elapsed_ms:.2f}ms")
        """
        self.end_time = time.time()
        return self.elapsed_ms()

    def elapsed_ms(self) -> float:
        """
        获取已经过时间（毫秒）。

        Returns:
            已经过时间（毫秒）

        示例::

            # 创建计时器
            timer = RequestTimer()

            # 执行部分操作
            part1 = do_part1()
            logger.debug(f"部分1耗时: {timer.elapsed_ms():.2f}ms")

            # 继续执行
            part2 = do_part2()
            logger.debug(f"总耗时: {timer.elapsed_ms():.2f}ms")

            # 检查是否超过阈值
            if timer.elapsed_ms() > 1000:  # 超过1秒
                logger.warning("操作耗时过长")
        """
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


async def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址。

    首先尝试从X-Forwarded-For头获取，然后从请求中获取。

    Args:
        request: 请求对象

    Returns:
        客户端IP地址

    示例::

        # 在路由处理程序中使用
        @app.get("/api/info")
        async def get_info(request: Request):
            client_ip = await get_client_ip(request)
            return {
                "client_ip": client_ip,
                "timestamp": datetime.now().isoformat()
            }

        # 在中间件中存储到上下文
        @app.middleware("http")
        async def ip_middleware(request: Request, call_next):
            client_ip = await get_client_ip(request)
            RequestContext.set("client_ip", client_ip)

            # 记录请求来源
            logger.info(f"收到来自 {client_ip} 的请求: {request.method} {request.url.path}")

            return await call_next(request)

        # 结合地理位置服务
        async def get_client_location(request: Request):
            ip = await get_client_ip(request)
            location = await geo_service.lookup(ip)
            return location
    """
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[0].strip()

    if hasattr(request, "client") and request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"
