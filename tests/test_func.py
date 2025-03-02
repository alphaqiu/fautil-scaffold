from loguru import logger

from src.core.setup import setup_modules

# if TYPE_CHECKING:
#     from typing import Iterator, Tuple


def _generate_installed_modules():
    """
    生成已安装的模块, 用于检查依赖.

    返回一个迭代器，包含已安装模块的名称和版本号。

    :returns: 包含模块名称和版本号的迭代器
    :rtype: Iterator[Tuple[str, str]]

    :example:

    .. code-block:: python

        installed_modules = _generate_installed_modules()
        for name, version in installed_modules:
            print(f"{name}=={version}")
    """
    # type: () -> Iterator[Tuple[str, str]]
    try:
        from importlib import metadata

        yielded = set()
        metadata.files
        for dist in metadata.distributions():
            name = dist.metadata.get("Name", None)  # type: ignore[attr-defined]
            # `metadata` values may be `None`, see:
            # https://github.com/python/cpython/issues/91216
            # and
            # https://github.com/python/importlib_metadata/issues/371
            if name is not None:
                normalized_name = _normalize_module_name(name)
                if dist.version is not None and normalized_name not in yielded:
                    yield normalized_name, dist.version
                    yielded.add(normalized_name)

    except ImportError as e:
        # < py3.8 不支持
        raise e


def _normalize_module_name(name):
    # type: (str) -> str
    return name.lower()


def test_generate_installed_modules():
    installed_modules = _generate_installed_modules()
    for name, version in installed_modules:
        print(f"{name}=={version}")


def test_setup_modules():
    """
    TDD 测试, 根据设想，创建测试函数。这里的逻辑如下：
    1. 传入指定的项目根目录，加上需要扫描的包名称
    2. 扫描包下所有模块，查找出含有`@setup`注解的类或函数
    3. 将含有`@setup`注解的类或函数，生成一个继承injector.Module的类，
    自动将含有`@setup`注解的类或函数，作为依赖注入的配置
    """
    package_pattern = "src"
    setup_modules(package_pattern=package_pattern)
