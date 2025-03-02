"""
Web服务网关接口模块。

配置并启动FastAPI应用，设置依赖注入、路由和中间件。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from injector import Injector

from src.controller.user import UserController, UserControllerModule
from src.dao.impl.user import UserDaoModule
from src.service.impl.user import UserServiceModule

# 创建依赖注入容器
injector = Injector([UserControllerModule(), UserDaoModule(), UserServiceModule()])

app = FastAPI()


def add_routes(engine: FastAPI):
    """
    添加路由到FastAPI应用。

    参数:
        app: FastAPI应用实例

    返回:
        配置好路由的FastAPI应用实例
    """
    user_controller = injector.get(UserController)
    user_controller.register(engine, prefix="/api")


add_routes(app)
# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    根路径处理函数。

    返回:
        包含欢迎消息的字典
    """
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
