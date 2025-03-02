"""
配置管理模块

提供从多种来源加载配置的功能，支持配置文件（YAML/JSON）、环境变量和.env文件，
并按照优先级加载配置。

环境变量命名和配置映射规则：
1. 基本规则：
   - 所有环境变量均以 `FAUTIL_` 前缀开头
   - 环境变量名称全部大写，下划线分隔单词
   - 配置属性通常采用小写下划线命名法

2. 顶级配置项映射：
   - 格式：FAUTIL_<配置项>_<属性名>
   - 示例：FAUTIL_APP_TITLE 映射到 settings.app.title

3. 嵌套配置项映射：
   - 格式：FAUTIL_<配置项>__<属性名>（注意是双下划线）
   - 示例：FAUTIL_DB__URL 映射到 settings.db.url

4. 类型转换规则：
   - 布尔值：字符串 "true", "1", "yes", "y", "t" (不区分大小写) 均被转换为 True
   - 整数：自动转换为 int 类型
   - 浮点数：自动转换为 float 类型
   - 列表：逗号分隔的字符串自动转换为列表，如 "item1,item2,item3"

5. 配置优先级（从高到低）：
   - 环境变量（最高优先级）
   - .env 文件中的设置
   - 配置文件（YAML/JSON）中的设置
   - 默认值（最低优先级）
"""

import json
import logging
import os
import platform
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# 定义类型变量用于泛型函数
T = TypeVar("T", bound="BaseSettings")

CONVENTION_DIRECTORY_NAME = ".fautil"


def locate_config_file(
    file_name: Optional[str] = "config.json",
    explicit_path: Optional[str] = None,
) -> Optional[Path]:
    """查找配置文件路径

    按照以下优先级查找配置文件：
    1. 明确指定的路径
    2. 当前工作目录
    3. 用户主目录下的.fautil目录
    4. 如果是Windows系统，则查找%APPDATA%目录下的.fautil目录
    5. 如果是Linux系统，则查找/etc/fautil目录

    :param file_name: 配置文件名
    :param explicit_path: 明确指定的路径
    :return: 配置文件路径，如果未找到则返回None
    :rtype: Optional[Path]
    """
    # 如果明确指定了路径，则优先使用
    if explicit_path:
        path = Path(explicit_path)
        if path.is_file():
            return path
        if path.is_dir():
            path = path / file_name
            if path.exists():
                return path

    # 检查当前工作目录
    cwd = Path.cwd() / file_name
    if cwd.exists():
        return cwd

    # 检查家目录下的.fautil目录
    home_dir = Path.home() / CONVENTION_DIRECTORY_NAME / file_name
    if home_dir.exists():
        return home_dir

    # 检查Windows系统下的%APPDATA%目录
    if platform.system() == "Windows":
        appdata_path = os.getenv("APPDATA")
        if appdata_path:
            win_config_path = Path(appdata_path) / CONVENTION_DIRECTORY_NAME / file_name
            if win_config_path.exists():
                return win_config_path

    # 检查Linux系统下的/etc/fautil目录
    if platform.system() == "Linux":
        linux_config_path = Path("/etc/fautil") / file_name
        if linux_config_path.exists():
            return linux_config_path

    return None


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """加载YAML配置文件

    :param file_path: 配置文件路径
    :return: 配置字典
    :rtype: Dict[str, Any]
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error("解析YAML配置文件失败: %s", e)
            return {}


def load_json_config(file_path: Path) -> Dict[str, Any]:
    """加载JSON配置文件

    :param file_path: 配置文件路径
    :return: 配置字典
    :rtype: Dict[str, Any]
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("解析JSON配置文件失败: %s", e)
            return {}


def load_config_from_file(
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """从配置文件加载配置

    :param config_path: 配置文件路径，如果未指定则按优先级自动查找
    :return: 配置字典
    :rtype: Dict[str, Any]
    """
    config_dict: Dict[str, Any] = {}

    # 尝试查找yaml配置文件
    yaml_path = locate_config_file("config.yaml", config_path)
    if yaml_path:
        config_dict.update(load_yaml_config(yaml_path))
        logger.info("已从 %s 加载YAML配置", yaml_path)
        return config_dict

    # 尝试查找json配置文件
    json_path = locate_config_file("config.json", config_path)
    if json_path:
        config_dict.update(load_json_config(json_path))
        logger.info("已从 %s 加载JSON配置", json_path)
        return config_dict

    logger.warning("未找到配置文件，将使用环境变量和默认值")
    return config_dict


class LogLevel(str, Enum):
    """日志级别枚举"""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogConfig(BaseSettings):
    """日志配置"""

    level: LogLevel = LogLevel.INFO
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    file_path: Optional[str] = None
    rotation: str = "20 MB"
    retention: str = "1 week"
    compression: str = "zip"
    serialize: bool = False

    model_config = {"env_prefix": "FAUTIL_LOG_"}


class DBConfig(BaseSettings):
    """数据库配置"""

    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    table_prefix: str = ""

    model_config = {"env_prefix": "FAUTIL_DB_"}


class RedisConfig(BaseSettings):
    """Redis配置"""

    url: str
    password: Optional[str] = None
    db: int = 0
    encoding: str = "utf-8"
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 10

    model_config = {"env_prefix": "FAUTIL_REDIS_"}


class KafkaConfig(BaseSettings):
    """Kafka配置"""

    bootstrap_servers: str
    client_id: Optional[str] = None
    group_id: str
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    max_poll_records: int = 500
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 10000
    consumer_timeout_ms: int = 1000
    api_version: Optional[str] = None

    model_config = {"env_prefix": "FAUTIL_KAFKA_"}


class MinioConfig(BaseSettings):
    """Minio配置"""

    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = True
    region: Optional[str] = None
    default_bucket: str = "default"

    model_config = {"env_prefix": "FAUTIL_MINIO_"}

    def get_endpoint_url(self) -> str:
        """获取完整的端点URL

        :return: 完整的端点URL
        :rtype: str
        """
        scheme = "https" if self.secure else "http"
        return f"{scheme}://{self.endpoint}"


class AppConfig(BaseSettings):
    """应用配置"""

    title: str = "FastAPI Application"
    description: str = "FastAPI Application"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    jwt_secret: str = "your-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expires_seconds: int = 3600
    log_level: LogLevel = LogLevel.INFO

    model_config = {"env_prefix": "FAUTIL_APP_"}


class Settings(BaseSettings):
    """应用的设置项"""

    app: AppConfig = Field(default_factory=AppConfig)
    db: Optional[DBConfig] = None
    redis: Optional[RedisConfig] = None
    kafka: Optional[KafkaConfig] = None
    minio: Optional[MinioConfig] = None
    log: LogConfig = Field(default_factory=LogConfig)

    model_config = {
        "env_nested_delimiter": "__",
        "case_sensitive": False,
        "env_prefix": "FAUTIL_",
    }

    @property
    def is_debug(self) -> bool:
        """是否为调试模式

        :return: 是否为调试模式
        :rtype: bool
        """
        return self.app.debug


def load_settings(
    settings_class: Type[T],
    config_path: Optional[str] = None,
    env_file: Optional[str] = None,
) -> T:
    """加载应用设置，按照优先级从配置文件、.env文件和环境变量加载

    该函数是配置加载的主入口点，支持多种配置来源，可以同时加载。加载过程中会
    按照优先级顺序应用配置，确保环境变量能够覆盖配置文件中的值。

    .env文件的查找顺序如下：
    1. 明确指定的路径
    2. 当前工作目录
    3. 用户主目录下的.fautil目录
    4. 如果是Windows系统，则查找%APPDATA%目录下的.fautil目录
    5. 如果是Linux系统，则查找/etc/fautil目录

    配置文件的查找顺序与.env文件相同，优先查找YAML文件（config.yaml），
    如果不存在则查找JSON文件（config.json）。

    配置属性的覆盖顺序如下（优先级从低到高）：
    1. 模型类的默认值
    2. 配置文件中的属性
    3. .env文件中的属性
    4. 环境变量中的属性

    环境变量映射示例：
    - FAUTIL_APP_TITLE -> settings.app.title
    - FAUTIL_DB_URL -> settings.db.url
    - FAUTIL_APP__DEBUG -> settings.app.debug (使用双下划线表示嵌套配置)

    类型转换会自动应用，例如：
    - FAUTIL_APP_PORT=8000 会被转换为整数
    - FAUTIL_APP_DEBUG=true 会被转换为布尔值
    - FAUTIL_APP_CORS_ORIGINS=http://localhost,https://example.com 会被转换为列表

    :param settings_class: 设置类型，必须继承自BaseSettings
    :param config_path: 配置文件路径，如果未指定则按优先级自动查找
    :param env_file: .env文件路径，如果未指定则按优先级自动查找
    :return: 设置实例，完全配置好的配置对象
    :rtype: T
    """
    # 1. 加载.env文件
    _load_dotenv_file(env_file)

    # 2. 从配置文件加载
    config_dict = load_config_from_file(config_path)

    # 3. 创建设置实例
    settings = settings_class()

    # 4. 应用配置文件设置（优先级低）
    if config_dict:
        _apply_config_dict(settings, config_dict)

    # 5. 应用环境变量设置（优先级高）
    _apply_environment_variables(settings)

    logger.info("配置加载完成")
    return settings


def _load_dotenv_file(env_file: Optional[str] = None) -> None:
    """加载.env文件

    加载.env文件中的环境变量设置。.env文件是一种常用的存储环境变量的文本文件，
    每行一个键值对，格式为KEY=VALUE。

    查找顺序如下：
    1. 如果指定了env_file参数，直接加载该文件
    2. 否则按照以下优先级自动查找.env文件：
       - 当前工作目录
       - 用户主目录下的.fautil目录
       - Windows系统下的%APPDATA%/.fautil目录
       - Linux系统下的/etc/fautil目录

    加载成功后，环境变量将被设置到当前进程的环境中，
    可以通过os.environ或os.getenv访问。

    :param env_file: .env文件路径，如果未指定则按优先级自动查找
    """
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("已加载环境变量文件: %s", env_path)
    else:
        env_path = locate_config_file(".env")
        if env_path:
            load_dotenv(env_path)
            logger.info("已加载环境变量文件: %s", env_path)


def _apply_config_dict(settings: BaseSettings, config_dict: Dict[str, Any]) -> None:
    """应用配置字典到设置对象

    将配置字典中的值应用到设置对象中，支持嵌套的配置对象。
    处理流程如下：
    1. 遍历配置字典中的每个键值对
    2. 如果设置对象没有对应的属性，则跳过
    3. 对于嵌套配置（字典类型值映射到BaseModel类型属性），递归处理每个嵌套属性
    4. 否则，直接设置属性值

    :param settings: 设置对象，通常是Settings实例
    :param config_dict: 配置字典，包含从配置文件加载的配置项
    """
    for key, value in config_dict.items():
        if not hasattr(settings, key):
            continue

        # 处理嵌套配置对象
        if isinstance(value, dict) and isinstance(getattr(settings, key), BaseModel):
            nested_config = getattr(settings, key)
            for nested_key, nested_value in value.items():
                if hasattr(nested_config, nested_key):
                    setattr(nested_config, nested_key, nested_value)
        else:
            setattr(settings, key, value)


def _apply_environment_variables(settings: BaseSettings) -> None:
    """应用环境变量到设置对象

    将环境变量中的值应用到设置对象中，支持两种格式的环境变量：
    1. FAUTIL_KEY=VALUE - 用于设置顶级属性
    2. FAUTIL_SECTION__KEY=VALUE - 用于设置嵌套配置属性（注意是双下划线）

    处理流程如下：
    1. 遍历设置对象的所有顶级属性
    2. 对于嵌套配置对象（BaseModel类型），调用_handle_nested_config处理
    3. 对于普通属性，直接从环境变量中查找并设置
    4. 环境变量值会根据目标属性类型自动转换

    :param settings: 设置对象，通常是Settings实例
    """
    # 处理所有顶级配置项
    for key in dir(settings):
        # 跳过私有属性和方法
        if key.startswith("_") or not hasattr(settings, key):
            continue

        # 获取属性值
        attr_value = getattr(settings, key)

        # 处理嵌套配置对象
        if isinstance(attr_value, BaseModel):
            _handle_nested_config(key, attr_value)
        else:
            # 处理顶级环境变量
            env_name = f"FAUTIL_{key.upper()}"
            if env_name in os.environ:
                # 根据字段类型转换值
                env_value = _convert_env_value(os.environ[env_name], type(attr_value))
                setattr(settings, key, env_value)

    # 特殊处理：检查是否存在数据库URL环境变量
    # if os.environ.get("FAUTIL_DB_URL") and settings.db is None:
    #     settings.db = DBConfig(url=os.environ["FAUTIL_DB_URL"])


def _handle_nested_config(config_name: str, config_obj: BaseModel) -> None:
    """处理嵌套配置对象的环境变量

    处理特定嵌套配置对象（如app、db、redis等）的环境变量设置。
    环境变量命名格式为：FAUTIL_配置名称__属性名

    例如：
    - FAUTIL_APP__TITLE 会映射到 settings.app.title
    - FAUTIL_DB__URL 会映射到 settings.db.url

    处理流程：
    1. 遍历配置对象的所有属性
    2. 构造对应的环境变量名（使用双下划线分隔配置名和属性名）
    3. 如果环境变量存在，获取属性的类型信息并进行类型转换
    4. 将转换后的值设置到配置对象中

    :param config_name: 配置名称，如"app"、"db"等
    :param config_obj: 配置对象，如AppConfig、DBConfig等实例
    """
    # 处理嵌套的每个属性
    for key in dir(config_obj):
        # 跳过私有属性和方法
        if key.startswith("_") or not hasattr(config_obj, key):
            continue

        # 构造环境变量名
        env_name = f"FAUTIL_{config_name.upper()}__{key.upper()}"
        if env_name in os.environ:
            # 从字段定义获取类型信息
            field_info = config_obj.model_fields.get(key)
            if field_info and field_info.annotation:
                # 使用字段定义的类型注解
                field_type = field_info.annotation
                env_value = _convert_env_value(os.environ[env_name], field_type)
                setattr(config_obj, key, env_value)
            else:
                # 如果没有类型注解，使用字符串
                setattr(config_obj, key, os.environ[env_name])


def _convert_env_value(value: str, target_type: Type) -> Any:
    """转换环境变量值到指定类型

    根据目标类型将环境变量字符串值转换为相应的Python类型。
    支持以下类型转换：
    - bool: "true", "1", "yes", "y", "t" (不区分大小写) 转换为 True
    - int: 转换为整数
    - float: 转换为浮点数
    - list/List: 按逗号分隔转换为列表
    - 其他类型: 保持字符串不变

    示例：
    - "8000" -> 8000 (当目标类型为int)
    - "true" -> True (当目标类型为bool)
    - "item1,item2,item3" -> ["item1", "item2", "item3"] (当目标类型为list)

    :param value: 环境变量值，字符串格式
    :param target_type: 目标类型
    :return: 转换后的值
    """
    if target_type is bool:
        return value.lower() in ("true", "1", "yes", "y", "t")

    if target_type is int:
        return int(value)

    if target_type is float:
        return float(value)

    if target_type is list or target_type is List:
        return [item.strip() for item in value.split(",")]

    return value
