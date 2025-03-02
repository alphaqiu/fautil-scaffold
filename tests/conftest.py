"""
pytest配置文件，用于控制测试行为
"""

# 定义要忽略的模块或文件列表
collect_ignore = []
collect_ignore_glob = []


# 对测试文件中以Test开头但不是测试类的类进行特殊处理
def pytest_collection_modifyitems(items):
    """
    修改已收集的测试项

    过滤掉特定类的测试
    """
    # 过滤掉和TestServiceProtocol, TestEntity相关的测试项
    skip_classes = ["TestServiceProtocol", "TestEntity"]
    for item in items[:]:
        for class_name in skip_classes:
            # 检查测试项是否属于需要跳过的类
            if class_name in item.nodeid:
                items.remove(item)
                break
