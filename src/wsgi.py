"""
Web服务网关接口模块。

配置并启动FastAPI应用，设置依赖注入、路由和中间件。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.cbv import setup_cbv
from src.core.setup import setup_modules

app = FastAPI()
setup_cbv(app, setup_modules(), prefix="/api")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
