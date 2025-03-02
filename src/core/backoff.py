"""
重试和退避模块。

提供指数退避策略的重试机制，用于处理可能暂时失败的操作。
支持同步和异步函数，可配置重试次数、等待时间和抖动。

使用示例:

1. 作为装饰器使用:
```python
from src.core.backoff import backoff_retry

# 简单使用，默认配置
@backoff_retry()
async def fetch_data():
    # 可能失败的操作
    response = await make_request()
    return response

# 自定义配置
@backoff_retry(
    max_retries=5,
    base_delay=1.0,
    max_delay=30.0,
    factor=2.0,
    jitter=True,
    exceptions=(ConnectionError, TimeoutError)
)
def connect_database():
    # 可能失败的操作
    db = create_connection()
    return db
```

2. 带超时的异步操作:
```python
from src.core.backoff import with_timeout
import asyncio

async def main():
    try:
        # 使用5秒超时执行任务
        result = await with_timeout(
            long_running_task(),
            timeout=5.0,
            message="操作超时",
            on_timeout=lambda: print("任务已超时，正在清理资源")
        )
    except asyncio.TimeoutError:
        # 处理超时情况
        print("任务超时")
```
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Optional, Type, TypeVar, cast

from loguru import logger

T = TypeVar("T")


def backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    装饰器：使用指数退避策略进行重试。

    参数:
        max_retries: 最大重试次数
        base_delay: 初始延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        factor: 延迟时间递增因子
        jitter: 是否添加随机抖动以避免请求风暴
        exceptions: 触发重试的异常类型

    返回:
        装饰后的函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # 计算延迟时间
                        delay = min(base_delay * (factor ** (attempt - 1)), max_delay)
                        # 添加抖动（0.5-1.5倍）
                        if jitter:
                            delay = delay * (0.5 + random.random())

                        logger.info(
                            f"重试 {func.__name__} ({attempt}/{max_retries})，延迟 {delay:.2f}秒"
                        )
                        await asyncio.sleep(delay)

                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} 第{attempt + 1}次执行失败: {str(e)}"
                    )
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 已达到最大重试次数 ({max_retries})，放弃重试"
                        )
                        raise

            # 这里理论上不会执行到，因为最后一次失败会直接抛出异常
            assert last_exception is not None
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # 计算延迟时间
                        delay = min(base_delay * (factor ** (attempt - 1)), max_delay)
                        # 添加抖动（0.5-1.5倍）
                        if jitter:
                            delay = delay * (0.5 + random.random())

                        logger.info(
                            f"重试 {func.__name__} ({attempt}/{max_retries})，延迟 {delay:.2f}秒"
                        )
                        time.sleep(delay)

                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"{func.__name__} 第{attempt + 1}次执行失败: {str(e)}"
                    )
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 已达到最大重试次数 ({max_retries})，放弃重试"
                        )
                        raise

            # 这里理论上不会执行到，因为最后一次失败会直接抛出异常
            assert last_exception is not None
            raise last_exception

        return cast(Callable[..., T], async_wrapper if is_async else sync_wrapper)

    return decorator


async def with_timeout(
    coro: asyncio.Future,
    timeout: float,
    message: str = "操作超时",
    on_timeout: Optional[Callable[[], None]] = None,
) -> Any:
    """
    在指定超时时间内运行协程。

    参数:
        coro: 要执行的协程
        timeout: 超时时间（秒）
        message: 超时时发出的错误消息
        on_timeout: 超时时要执行的回调函数

    返回:
        协程的结果

    抛出:
        asyncio.TimeoutError: 如果协程在超时时间内未完成
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(message)
        if on_timeout:
            on_timeout()
        raise
