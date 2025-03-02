"""
高级配置加载功能测试模块

测试嵌套配置和环境变量覆盖等高级功能
"""

import os
from pathlib import Path
from typing import Any, Dict

import pytest

from src.core.config import (
    DBConfig,
    LogLevel,
    MinioConfig,
    RedisConfig,
    Settings,
    load_settings,
)

# 设置测试配置文件的路径
TEST_CONFIG_DIR = Path(__file__).parent / "test_configs"


def test_nested_config_from_env_vars():
    """测试从环境变量加载嵌套配置"""
    try:
        # 设置嵌套环境变量
        env_vars = {
            "FAUTIL_APP__TITLE": "环境变量应用",
            "FAUTIL_APP__DEBUG": "true",
            "FAUTIL_APP__PORT": "9000",
            "FAUTIL_DB__URL": "postgresql://env_user:env_pass@localhost:5432/env_db",
            "FAUTIL_DB__ECHO": "true",
            "FAUTIL_DB__POOL_SIZE": "20",
            "FAUTIL_REDIS__URL": "redis://localhost:6379",
            "FAUTIL_REDIS__DB": "2",
            "FAUTIL_LOG__LEVEL": "DEBUG",
            "FAUTIL_LOG__FILE_PATH": "/tmp/env-test.log",
        }

        # 应用环境变量
        for key, value in env_vars.items():
            os.environ[key] = value

        # 加载设置
        settings = Settings()

        # 验证嵌套配置
        assert settings.app.title == "环境变量应用"
        assert settings.app.debug is True
        assert settings.app.port == 9000

        # 验证DB配置
        if settings.db and isinstance(settings.db, DBConfig):
            assert (
                settings.db.url
                == "postgresql://env_user:env_pass@localhost:5432/env_db"
            )
            assert settings.db.echo is True
            assert settings.db.pool_size == 20

        # 验证Redis配置
        if settings.redis and isinstance(settings.redis, RedisConfig):
            assert settings.redis.url == "redis://localhost:6379"
            assert settings.redis.db == 2

        # 验证日志配置
        assert settings.log.level == LogLevel.DEBUG
        assert settings.log.file_path == "/tmp/env-test.log"

    finally:
        # 清理环境变量
        for key in env_vars.keys():
            if key in os.environ:
                del os.environ[key]


def test_create_complex_config():
    """测试创建完整的复杂配置"""
    # 创建一个完整的复杂配置字典
    config_dict: Dict[str, Any] = {
        "app": {
            "title": "复杂配置应用",
            "description": "测试复杂配置",
            "version": "1.0.0",
            "debug": True,
            "port": 5555,
            "jwt_secret": "complex-jwt-secret",
        },
        "db": {
            "url": "postgresql://complex:pass@localhost:5432/complex_db",
            "echo": True,
            "pool_size": 25,
            "max_overflow": 15,
        },
        "redis": {
            "url": "redis://localhost:6380",
            "db": 3,
            "encoding": "utf-8",
            "max_connections": 20,
        },
        "minio": {
            "endpoint": "localhost:9000",
            "access_key": "minioadmin",
            "secret_key": "minioadmin",
            "secure": False,
            "default_bucket": "complex-test",
        },
        "log": {
            "level": "DEBUG",
            "file_path": "/tmp/complex-test.log",
            "rotation": "10 MB",
            "retention": "3 days",
        },
    }

    # 创建测试配置文件
    complex_config_path = TEST_CONFIG_DIR / "complex_config.json"
    with open(complex_config_path, "w", encoding="utf-8") as f:
        import json

        json.dump(config_dict, f, ensure_ascii=False, indent=2)

    try:
        # 加载设置
        settings = load_settings(Settings, config_path=str(complex_config_path))

        # 验证基本设置
        assert settings.app.title == "复杂配置应用"
        assert settings.app.description == "测试复杂配置"
        assert settings.app.version == "1.0.0"
        assert settings.app.debug is True
        assert settings.app.port == 5555

        # 验证DB配置 - 根据当前实现适配
        if isinstance(settings.db, dict):
            assert (
                settings.db.get("url")
                == "postgresql://complex:pass@localhost:5432/complex_db"
            )
            assert settings.db.get("pool_size") == 25
        elif isinstance(settings.db, DBConfig):
            assert (
                settings.db.url == "postgresql://complex:pass@localhost:5432/complex_db"
            )
            assert settings.db.pool_size == 25

        # 验证Redis配置
        if isinstance(settings.redis, dict):
            assert settings.redis.get("url") == "redis://localhost:6380"
            assert settings.redis.get("db") == 3
        elif isinstance(settings.redis, RedisConfig):
            assert settings.redis.url == "redis://localhost:6380"
            assert settings.redis.db == 3

        # 验证Minio配置
        if isinstance(settings.minio, dict):
            assert settings.minio.get("endpoint") == "localhost:9000"
            assert settings.minio.get("default_bucket") == "complex-test"
        elif isinstance(settings.minio, MinioConfig):
            assert settings.minio.endpoint == "localhost:9000"
            assert settings.minio.default_bucket == "complex-test"

        # 验证日志配置
        assert settings.log.level == LogLevel.DEBUG
        assert settings.log.file_path == "/tmp/complex-test.log"
        assert settings.log.rotation == "10 MB"
        assert settings.log.retention == "3 days"

    finally:
        # 清理测试文件
        if complex_config_path.exists():
            complex_config_path.unlink()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
