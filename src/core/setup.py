"""
依赖注入设置模块
==============

提供依赖注入系统的核心功能，包括装饰器、模块绑定和自动扫描注册等功能。
该模块是应用程序框架的基础，负责管理对象的创建和依赖关系。

主要功能:
    - 自动扫描并注册带有 ``@setup`` 装饰器的类和函数
    - 管理类型与实现之间的映射关系
    - 提供依赖注入容器及绑定对象的查询功能

示例::

    from src.core.setup import setup, setup_modules

    # 定义服务及其协议
    class UserServiceProtocol(Protocol):
        def get_user(self, user_id: int) -> dict: ...

    @setup(protocol=UserServiceProtocol)
    class UserService:
        def get_user(self, user_id: int) -> dict:
            return {"id": user_id, "name": "User"}

    # 启动依赖注入
    injector = setup_modules("src")
"""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type

from injector import Binder, Injector, Module
from loguru import logger

# 全局变量，用于跟踪所有注册的模块
_registered_modules: Dict[Type, Any] = {}


def get_registered_modules() -> Dict[Type, Any]:
    """
    获取所有已注册的模块

    返回所有通过 @setup 装饰器注册的模块类型到实现的映射。

    :return: 字典，键为模块类型，值为模块实例

    示例::

        # 获取所有注册的模块
        modules = get_registered_modules()

        # 检查特定类型是否已注册
        if UserServiceProtocol in modules:
            print(f"UserServiceProtocol 已注册，实现类: {modules[UserServiceProtocol].__name__}")
    """
    return _registered_modules


def setup(protocol: Optional[Type[Any]] = None):
    """
    依赖注入装饰器

    用于标记类或函数，使其被依赖注入系统自动注册和管理。
    当提供了 protocol 参数时，将实现类绑定到指定的协议接口。

    :param protocol: 可选的协议类型，类型将被绑定到该协议
    :return: 装饰器函数

    使用示例::

        # 无协议绑定,绑定到类本身 => a: SimpleService = SimpleService()
        @setup()
        class SimpleService:
            def process(self):
                return "处理完成"

        # 绑定到协议 => a: ServiceProtocol = ServiceImpl()
        @setup(protocol=ServiceProtocol)
        class ServiceImpl:
            def method(self):
                return "实现方法"
    """

    def decorator(target: Type):
        target.__setup__ = {
            "protocol": protocol,
        }
        return target

    return decorator


def _is_setup_decorated(obj):
    """
    检查对象是否有 @setup 装饰器

    :param obj: 要检查的对象
    :return: 如果对象有 __setup__ 属性则返回 True，否则返回 False
    """
    return hasattr(obj, "__setup__")


def _scan_module(module_name) -> dict[str, Any]:
    """
    扫描模块中带有 @setup 装饰器的类或函数

    遍历指定模块中的所有成员，找出被 @setup 装饰器标记的类或函数，
    并构建绑定类型到实现对象的映射。

    :param module_name: 要扫描的模块名称
    :return: 字典，键为绑定类型，值为实现类或函数
    :raises ImportError: 当模块导入失败时抛出
    """
    try:
        module = importlib.import_module(module_name)
        setup_objects = {}

        for name, obj in inspect.getmembers(module):
            if not inspect.isclass(obj) and not inspect.isfunction(obj):
                continue
            if not _is_setup_decorated(obj):
                continue
            binding_type = obj.__setup__["protocol"]
            if binding_type is None:
                binding_type = obj
            if binding_type not in setup_objects:
                setup_objects[binding_type] = obj
                logger.debug(
                    f"Found setup object: {binding_type.__name__}({name})",
                    f" in {module_name}",
                )

        return setup_objects
    except ImportError as e:
        logger.error(f"Error importing module {module_name}: {e}")
        return {}


def _scan_package(package_name) -> dict[str, Any]:
    """
    递归扫描包中所有模块

    导入指定的包，然后递归扫描该包下的所有子包和模块，
    查找所有带有 @setup 装饰器的类和函数。

    :param package_name: 要扫描的包名称
    :return: 字典，键为绑定类型，值为实现类或函数
    :raises ImportError: 当包导入失败时抛出
    :raises AttributeError: 当访问包属性失败时抛出
    :raises (FileNotFoundError, PermissionError, OSError): 当文件系统操作失败时抛出
    """
    try:
        logger.debug(f"尝试导入包: {package_name}")
        package = importlib.import_module(package_name)
        setup_objects = _scan_module(package_name)

        # 获取包的路径
        if hasattr(package, "__path__"):
            # 初始化package_path为None
            package_path = None

            # 检查是否有__file__属性
            if hasattr(package, "__file__") and package.__file__ is not None:
                # 使用物理文件系统扫描以确保发现所有子包
                package_path = Path(package.__file__).parent

            # 只有当package_path被成功赋值时才继续
            if package_path is not None:
                # 直接遍历文件系统来查找子包和模块
                for item in package_path.iterdir():
                    if item.is_dir() and (item / "__init__.py").exists():
                        # 是一个子包
                        subpackage_name = f"{package_name}.{item.name}"
                        setup_objects.update(_scan_package(subpackage_name))
                    elif (
                        item.is_file()
                        and item.suffix == ".py"
                        and item.name != "__init__.py"
                    ):
                        # 是一个模块
                        module_name = f"{package_name}.{item.stem}"
                        setup_objects.update(_scan_module(module_name))

        return setup_objects
    except ImportError as e:
        logger.error(f"导入包 {package_name} 时出错: {e}")
        return {}
    except (AttributeError, FileNotFoundError, PermissionError, OSError) as e:
        # 捕获更具体的文件系统和属性访问异常
        logger.error(f"扫描包 {package_name} 时发生错误: {e}", exc_info=True)
        return {}


def _create_module_class(setup_objects):
    """
    创建一个继承 injector.Module 的类，配置依赖注入

    根据扫描到的对象创建一个 Module 子类，用于配置依赖注入绑定。

    :param setup_objects: 扫描到的对象字典，键为绑定类型，值为实现类或函数
    :return: 配置了绑定关系的 Module 子类
    """

    class SetupModule(Module):
        """
        依赖注入配置模块类

        负责将标记了 @setup 装饰器的类和函数绑定到依赖注入容器中。
        这个类处理 Protocol 与实现类的映射，以及绑定名称的记录。

        :ivar binder: 依赖注入绑定器
        """

        def configure(self, binder: Binder):
            """
            配置依赖注入绑定

            将所有标记了 @setup 装饰器的对象绑定到依赖注入容器中。
            对于设置了 protocol 的对象，将它们绑定到相应的协议类型。
            将所有注册的对象保存到全局变量中以便后续查询。

            :param binder: 依赖注入绑定器实例
            """
            # 将所有注册的对象保存到全局变量中
            # pylint: disable=global-variable-not-assigned
            global _registered_modules
            _registered_modules.update(setup_objects)

            for _, obj in setup_objects.items():
                if obj.__setup__["protocol"] is not None:
                    binder.bind(obj.__setup__["protocol"], to=obj)
                else:
                    binder.bind(obj)

    return SetupModule


def get_all_bindings(injector: Injector) -> Dict[Type, Any]:
    """
    从 Injector 实例中获取所有已绑定的类型及其实例

    这个函数使用全局变量 _registered_modules 中的类型作为键，
    尝试从 injector 中获取每种类型的实例。

    :param injector: 依赖注入容器实例
    :return: 字典，键为绑定的类型，值为其实例
    :raises KeyError: 当绑定类型未找到时抛出
    :raises TypeError: 当类型不匹配时抛出
    :raises ValueError: 当值无效时抛出
    :raises AttributeError: 当访问属性失败时抛出

    示例::

        injector = setup_modules("src")

        # 获取所有绑定的实例
        bindings = get_all_bindings(injector)

        # 使用特定类型的服务
        if UserServiceProtocol in bindings:
            user_service = bindings[UserServiceProtocol]
            user = user_service.get_user(1)
    """
    result = {}
    for binding_type in _registered_modules:
        try:
            # 尝试从 injector 获取该类型的实例
            instance = injector.get(binding_type)
            result[binding_type] = instance
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            # 捕获依赖注入过程中可能出现的具体异常
            logger.warning(f"无法获取类型 {binding_type.__name__} 的实例: {e}")
    return result


def get_bindings_by_category(
    injector: Injector, base_class: Optional[Type] = None
) -> Dict[str, Dict[Type, Any]]:
    """
    按类型或类别获取所有绑定

    这个函数可以将所有绑定按照它们的类别进行分组。
    如果提供了 base_class，只返回继承自该基类的绑定。

    :param injector: 依赖注入容器实例
    :param base_class: 可选的基类筛选器，只返回此类型的子类
    :return: 按类别分组的绑定字典，格式为 {类别名称: {类型: 实例, ...}, ...}

    示例::

        injector = setup_modules("src")

        # 获取所有按类别分组的绑定
        categories = get_bindings_by_category(injector)

        # 输出每个类别下的绑定
        for category, bindings in categories.items():
            print(f"类别: {category}, 绑定数量: {len(bindings)}")
            for binding_type, instance in bindings.items():
                print(f"  - {binding_type.__name__}")

        # 只获取服务类的绑定
        from src.service.base import BaseService
        service_bindings = get_bindings_by_category(injector, BaseService)
    """
    all_bindings = get_all_bindings(injector)
    result = {}

    for binding_type, instance in all_bindings.items():
        # 如果指定了基类且当前类型不是其子类，则跳过
        if base_class and not issubclass(binding_type, base_class):
            continue

        # 获取类别名称 - 更健壮的方式
        try:
            parts = binding_type.__module__.split(".")
            # 如果模块名称至少有两部分，取倒数第二个，否则使用模块名称本身
            category = parts[-2] if len(parts) >= 2 else parts[0]
        except (IndexError, AttributeError):
            # 如果出现异常，使用默认类别名称
            category = "default"

        if category not in result:
            result[category] = {}

        result[category][binding_type] = instance

    return result


def setup_modules(package_pattern: Optional[str] = "src") -> Injector:
    """
    扫描包下所有模块，查找和注册含有 ``@setup`` 装饰器的类或函数

    此函数是依赖注入系统的入口点，它会：

    1. 扫描指定包路径下的所有模块
    2. 查找带有 ``@setup`` 装饰器的类和函数
    3. 创建一个 Injector 实例并配置绑定关系
    4. 返回配置好的 Injector 实例以供应用使用

    :param package_pattern: 包名称模式，例如："src.controller"
    :return: 配置好的 Injector 实例
    :raises ImportError: 当包导入失败时抛出

    使用示例::

        # 扫描整个src包
        injector = setup_modules("src")

        # 只扫描控制器包
        injector = setup_modules("src.controller")

        # 获取特定服务实例
        user_service = injector.get(UserServiceProtocol)
        result = user_service.get_user(1)

        # 应用程序启动时配置
        app = FastAPI()
        injector = setup_modules("src")

        # 配置路由等
        setup_cbv(app, injector)
    """
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent.parent
    logger.debug(f"Root directory: {root_dir}")

    # 将项目根目录添加到sys.path
    if str(root_dir) not in sys.path:
        logger.debug(f"Add root directory to sys.path: {root_dir}")
        sys.path.insert(0, str(root_dir))

    setup_objects = _scan_package(package_pattern)
    logger.debug(f"Setup objects: {setup_objects}")

    module_class = _create_module_class(setup_objects)
    logger.debug(f"Module class: {module_class}")

    return Injector([module_class])
