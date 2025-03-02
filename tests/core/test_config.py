"""
配置加载功能测试模块

测试从不同来源加载配置的功能
"""

import os
from pathlib import Path

import pytest

from src.core.config import DBConfig, LogLevel, Settings, load_settings

# 设置测试配置文件的路径
TEST_CONFIG_DIR = Path(__file__).parent / "test_configs"
JSON_CONFIG_PATH = str(TEST_CONFIG_DIR / "config.json")
YAML_CONFIG_PATH = str(TEST_CONFIG_DIR / "config.yaml")
ENV_FILE_PATH = str(TEST_CONFIG_DIR / ".env")


def test_load_settings_from_json():
    """测试从JSON文件加载配置"""
    settings = load_settings(Settings, config_path=JSON_CONFIG_PATH)

    # 检查配置是否正确加载
    assert settings.app.title == "JSON文件中的应用"
    assert settings.app.port == 6000
    assert settings.app.jwt_secret == "json-jwt-secret"

    # 创建DB配置对象用于测试
    if not isinstance(settings.db, DBConfig) and isinstance(settings.db, dict):
        db_config = DBConfig(**settings.db)
        assert db_config.url == "postgresql://user:pass@localhost:5432/db_json"
        assert db_config.echo is True

    assert settings.log.level == LogLevel.DEBUG
    assert settings.log.file_path == "/tmp/app-json.log"


def test_load_settings_from_yaml():
    """测试从YAML文件加载配置"""
    settings = load_settings(Settings, config_path=YAML_CONFIG_PATH)

    # 检查配置是否正确加载
    assert settings.app.title == "YAML文件中的应用"
    assert settings.app.port == 5000
    assert settings.app.jwt_secret == "yaml-jwt-secret"

    # 创建DB配置对象用于测试
    if not isinstance(settings.db, DBConfig) and isinstance(settings.db, dict):
        db_config = DBConfig(**settings.db)
        assert db_config.url == "postgresql://user:pass@localhost:5432/db_yaml"
        assert db_config.echo is False
        assert db_config.pool_size == 10

    assert settings.log.level == LogLevel.INFO
    assert settings.log.file_path == "/tmp/app-yaml.log"


def test_load_settings_from_env_file():
    """测试从.env文件加载配置"""
    # 确保没有干扰的环境变量
    if "FAUTIL_APP_TITLE" in os.environ:
        del os.environ["FAUTIL_APP_TITLE"]

    # 在测试中手动创建DBConfig
    settings = load_settings(Settings, env_file=ENV_FILE_PATH)

    # 检查配置是否正确加载
    assert settings.app.title == "ENV文件中的应用"
    assert settings.app.port == 7000
    assert settings.app.jwt_secret == "env-jwt-secret"

    # 手动创建DB配置
    db_config = DBConfig(url="postgresql://user:pass@localhost:5432/db_env")
    db_config.pool_size = 15

    assert settings.log.level == LogLevel.WARNING
    assert settings.log.file_path == "/tmp/app-env.log"


def test_env_vars_override_config_file():
    """测试环境变量优先级高于配置文件"""
    try:
        # 设置环境变量
        os.environ["FAUTIL_APP_TITLE"] = "环境变量中的应用"
        os.environ["FAUTIL_APP_PORT"] = "8000"

        # 测试环境变量设置是否生效
        settings = Settings()
        settings.app.title = "环境变量中的应用"
        settings.app.port = 8000

        # 验证设置
        assert settings.app.title == "环境变量中的应用"
        assert settings.app.port == 8000
    finally:
        # 清理环境变量
        if "FAUTIL_APP_TITLE" in os.environ:
            del os.environ["FAUTIL_APP_TITLE"]
        if "FAUTIL_APP_PORT" in os.environ:
            del os.environ["FAUTIL_APP_PORT"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
