"""
用户API集成测试。

测试所有用户相关的API端点，包括：
- 获取用户列表
- 创建用户
- 获取单个用户
- 更新用户
- 删除用户
"""

import pytest
from fastapi.testclient import TestClient

from src.wsgi import app


@pytest.fixture
def client():
    """创建测试客户端。"""
    return TestClient(app)


def test_user_crud_flow(client):
    """
    测试用户CRUD完整流程。

    按顺序测试：
    1. 获取初始用户列表
    2. 创建新用户
    3. 验证用户创建成功
    4. 获取用户详情
    5. 更新用户信息
    6. 验证用户更新成功
    7. 删除用户
    8. 验证用户删除成功
    """
    # 1. 获取初始用户列表
    response = client.get("/api/user/")
    assert response.status_code == 200
    initial_users = response.json()
    initial_count = len(initial_users)

    # 2. 创建新用户
    new_user_data = {"name": "测试用户"}
    response = client.post("/api/user/", json=new_user_data)
    assert response.status_code == 201

    # 3. 验证用户创建成功（检查用户列表长度增加）
    response = client.get("/api/user/")
    assert response.status_code == 200
    users_after_create = response.json()
    assert len(users_after_create) == initial_count + 1

    # 获取新创建的用户ID
    new_user = next(
        (user for user in users_after_create if user["name"] == new_user_data["name"]),
        None,
    )
    assert new_user is not None
    new_user_id = new_user["id"]

    # 4. 获取用户详情
    response = client.get(f"/api/user/{new_user_id}")
    assert response.status_code == 200
    user_details = response.json()
    assert user_details["id"] == new_user_id
    assert user_details["name"] == new_user_data["name"]

    # 5. 更新用户信息
    updated_user_data = {"name": "已更新用户"}
    response = client.put(f"/api/user/{new_user_id}", json=updated_user_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["id"] == new_user_id
    assert updated_user["name"] == updated_user_data["name"]

    # 6. 验证用户更新成功（通过再次获取用户详情）
    response = client.get(f"/api/user/{new_user_id}")
    assert response.status_code == 200
    user_details = response.json()
    assert user_details["name"] == updated_user_data["name"]

    # 7. 删除用户
    response = client.delete(f"/api/user/{new_user_id}")
    assert response.status_code == 204

    # 8. 验证用户删除成功（检查用户不存在）
    response = client.get(f"/api/user/{new_user_id}")
    assert response.status_code == 404


def test_get_nonexistent_user(client):
    """测试获取不存在的用户。"""
    # 使用一个不太可能存在的用户ID
    nonexistent_id = 9999
    response = client.get(f"/api/user/{nonexistent_id}")
    assert response.status_code == 404


def test_update_nonexistent_user(client):
    """测试更新不存在的用户。"""
    nonexistent_id = 9999
    response = client.put(f"/api/user/{nonexistent_id}", json={"name": "不存在用户"})
    assert response.status_code == 404


def test_delete_nonexistent_user(client):
    """测试删除不存在的用户。"""
    nonexistent_id = 9999
    # 删除不存在的用户应该不会报错，应该返回成功
    response = client.delete(f"/api/user/{nonexistent_id}")
    assert response.status_code == 204


def test_create_user_validation(client):
    """测试创建用户时的数据验证。"""
    # 缺少必需字段的请求
    response = client.post("/api/user/", json={})
    assert response.status_code == 422

    # 包含额外字段的请求（应该被忽略）
    response = client.post(
        "/api/user/", json={"name": "额外字段用户", "extra_field": "额外值"}
    )
    assert response.status_code == 201
