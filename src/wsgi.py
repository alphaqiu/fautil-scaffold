"""
Web服务网关接口模块。

配置并启动FastAPI应用，设置依赖注入、路由和中间件。
"""

import asyncio
import atexit
import signal
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.requests import Request

from src.core.backoff import backoff_retry, with_timeout
from src.core.cbv import setup_cbv
from src.core.setup import setup_modules

# 全局变量，用于控制优雅停机
SHOULD_EXIT = False
IS_SHUTTING_DOWN = False

# 活跃请求计数器
ACTIVE_REQUESTS = 0

# 启动和关闭配置
STARTUP_RETRY_CONFIG = {
    "max_retries": 5,  # 最多重试5次
    "base_delay": 1.0,  # 起始延迟1秒
    "max_delay": 30.0,  # 最大延迟30秒
    "factor": 2.0,  # 指数增长因子
    "jitter": True,  # 启用随机抖动
}

SHUTDOWN_TIMEOUT = 30.0  # 关闭超时时间（秒）


@backoff_retry(**STARTUP_RETRY_CONFIG)
async def init_database():
    """
    初始化数据库连接。

    使用退避重试机制，在连接失败时自动重试。
    """
    # 这里是实际初始化数据库连接的代码
    # 例如: db.init_engine() 或 engine = create_engine(...)

    # 模拟可能失败的连接
    # 实际代码中，如果连接失败会抛出异常，触发重试机制
    # 删除下面的 return 语句，并添加实际连接代码
    return "数据库连接"


@backoff_retry(**STARTUP_RETRY_CONFIG)
async def init_redis():
    """
    初始化Redis连接。

    使用退避重试机制，在连接失败时自动重试。
    """
    # 这里是实际初始化Redis连接的代码
    # 例如: redis_client = Redis(...)

    # 模拟可能失败的连接
    # 实际代码中，如果连接失败会抛出异常，触发重试机制
    # 删除下面的 return 语句，并添加实际连接代码
    return "Redis连接"


async def startup_app():
    """
    应用程序启动时初始化资源。

    初始化数据库连接、缓存服务等资源。
    使用退避重试机制处理连接失败情况。
    """
    logger.info("应用正在启动...")

    # 并行初始化多个依赖服务
    try:
        # 创建初始化任务
        db_task = asyncio.create_task(init_database())
        redis_task = asyncio.create_task(init_redis())

        # 等待所有任务完成
        tasks_results = await asyncio.gather(
            db_task,
            redis_task,
            return_exceptions=True,  # 允许单个任务失败而不影响其他任务
        )

        # 检查任务结果
        for i, result in enumerate(tasks_results):
            if isinstance(result, Exception):
                service_name = ["数据库", "Redis"][i]
                logger.error(f"{service_name}初始化失败: {result}")
                # 关键服务初始化失败时退出
                if i == 0:  # 数据库是关键服务
                    logger.critical("数据库初始化失败，无法启动应用")
                    sys.exit(1)
    except Exception as e:
        logger.critical(f"应用启动过程中发生严重错误: {e}")
        sys.exit(1)

    logger.info("应用已启动，所有资源已初始化完成")


async def shutdown_resources():
    """
    关闭数据库和其他资源。

    此函数作为单独的任务运行，并设置超时时间。
    """
    # 1. 关闭数据库连接
    try:
        # 关闭SQLAlchemy引擎（如果存在）
        # 例如: db.dispose_engine() 或 engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")

    # 2. 关闭Redis连接（如果存在）
    try:
        # redis_client.close()
        logger.info("Redis连接已关闭")
    except Exception as e:
        logger.error(f"关闭Redis连接时出错: {e}")

    # 3. 关闭其他需要清理的资源

    logger.info("所有资源已释放")


async def shutdown_app():
    """
    应用程序关闭时清理资源。

    关闭数据库连接、缓存连接等资源，确保优雅停机。
    使用超时机制确保在规定时间内完成关闭。
    """
    logger.info("应用正在关闭...")

    # 1. 将应用标记为关闭状态，拒绝新的请求
    global IS_SHUTTING_DOWN
    IS_SHUTTING_DOWN = True

    # 2. 等待活跃请求处理完成
    if ACTIVE_REQUESTS > 0:
        logger.info(f"等待 {ACTIVE_REQUESTS} 个活跃请求完成处理...")
        wait_seconds = 0
        max_wait = 30  # 最长等待30秒

        while ACTIVE_REQUESTS > 0 and wait_seconds < max_wait:
            await asyncio.sleep(1)
            wait_seconds += 1
            if wait_seconds % 5 == 0:
                logger.info(
                    f"仍在等待 {ACTIVE_REQUESTS} 个请求完成，已等待 {wait_seconds} 秒"
                )

        if ACTIVE_REQUESTS > 0:
            logger.warning(
                f"在 {max_wait} 秒内仍有 {ACTIVE_REQUESTS} 个请求未完成，将强制关闭"
            )
    else:
        logger.info("没有活跃的请求，立即进行资源清理")

    # 3. 使用超时机制关闭资源
    try:
        await with_timeout(
            shutdown_resources(),
            timeout=SHUTDOWN_TIMEOUT,
            message=f"资源关闭操作在 {SHUTDOWN_TIMEOUT} 秒内未完成，将强制关闭",
            on_timeout=lambda: logger.warning("资源关闭超时，可能存在资源泄漏"),
        )
    except asyncio.TimeoutError:
        # 超时错误已在 with_timeout 中处理
        pass

    logger.info("应用已完全关闭")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    应用程序生命周期管理器。

    在应用启动时初始化资源，在应用关闭时清理资源。
    这是FastAPI推荐的生命周期管理方式，优于on_event处理器。
    """
    # 启动：初始化资源
    await startup_app()

    yield  # 应用正常运行阶段

    # 关闭：清理资源
    await shutdown_app()


# 创建应用实例，使用lifespan上下文管理器
app = FastAPI(
    title="用户管理系统",
    description="RESTful API 用户管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 设置路由
setup_cbv(app, setup_modules(), prefix="/api")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    请求中间件。

    1. 跟踪活跃请求数量
    2. 在应用关闭时返回503状态码
    3. 记录请求处理时间
    """
    global ACTIVE_REQUESTS
    request_id = id(request)
    start_time = time.time()

    # 如果应用正在关闭，拒绝新的请求
    if IS_SHUTTING_DOWN:
        logger.warning(f"应用正在关闭，拒绝请求: {request.url}")

        return JSONResponse(
            status_code=503, content={"detail": "服务正在关闭，请稍后重试"}
        )

    # 增加活跃请求计数
    ACTIVE_REQUESTS += 1
    logger.debug(
        f"请求开始 [{request_id}]: {request.method} {request.url.path} (活跃请求: {ACTIVE_REQUESTS})"
    )

    try:
        # 处理请求
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.debug(
            f"请求完成 [{request_id}]: {request.method} "
            f"{request.url.path} - {response.status_code} ({process_time:.4f}s)"
        )
        return response
    except Exception as e:
        logger.error(
            f"请求处理异常 [{request_id}]: {request.method} {request.url.path} - {str(e)}"
        )
        raise
    finally:
        # 减少活跃请求计数
        ACTIVE_REQUESTS -= 1


def handle_signals(sig, frame):
    """
    处理停止信号。

    参数:
        sig: 信号值
        frame: 当前栈帧
    """
    global SHOULD_EXIT
    if not SHOULD_EXIT:
        logger.info(f"收到 {signal.Signals(sig).name} 信号，开始优雅停机")
        SHOULD_EXIT = True


def run_app():
    """
    运行FastAPI应用程序。

    配置uvicorn运行参数，设置优雅停机相关配置。
    """
    # 配置uvicorn
    config = uvicorn.Config(
        app="src.wsgi:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        # 设置较长的优雅停机超时时间
        timeout_graceful_shutdown=30,  # 默认是30秒，可根据需要调整
    )
    server = uvicorn.Server(config)

    # 设置自定义信号处理程序
    for signal_name in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(signal_name, handle_signals)

    # 注册退出处理
    def exit_handler():
        logger.info("Python解释器退出，确保资源已正确清理")

    atexit.register(exit_handler)

    # 启动服务
    server.run()


if __name__ == "__main__":
    run_app()
