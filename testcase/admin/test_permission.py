# testcases/admin/test_permission.py
import pytest
import allure

from common.assertions import ApiAssertion
from common.utils.role_manager import role_manager
from common.client.admin_client import AdminClient


@allure.feature("后台权限管理")
class TestAdminPermission:
    """ 后台权限控制测试 """

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("角色权限配置")
    def test_role_permission_config(self):
        """ 测试角色权限配置是否正确 """
        roles = role_manager.get_all_roles()
        assert len(roles) > 0, "未配置任何角色"

        # 检查超级管理员权限
        admin_role = role_manager.get_role(1)
        assert admin_role, "超级管理员角色不存在"
        # assert "admin:*" in admin_role.permissions, "超级管理员缺少admin:*权限"
        assert 'admin:delete' and 'admin:read' and 'admin:update' and 'admin:write' in admin_role.permissions, "超级管理员缺少admin:*权限"

        # 检查只读用户权限
        readonly_role = role_manager.get_role(4)
        assert readonly_role, "只读用户角色不存在"
        assert "product:read" in readonly_role.permissions, "只读用户缺少product:read权限"

    @allure.story("用户权限获取")
    def test_user_permission(self):
        users = role_manager.get_all_users()
        assert len(users) > 0, "未配置测试用户"

        for user in users:
            perms = role_manager.get_user_permission(user.username)
            assert perms is not None, f"用户{user.username}无权限"

            # 验证用户权限包含其他角色的权限
            for role_id in user.roles: # not users.roles
                role = role_manager.get_role(role_id)
                if role:
                    for perm in role.permissions:
                        assert perm in perms, f"用户{user.username}缺少角色权限{perm}"

    @allure.story("权限检查")
    @pytest.mark.parametrize("username,permission,expected", [
        ("admin", "product:write", True),
        ("admin", "order:delete", True),
        ("product_admin", "product:write", True),
        ("product_admin", "order:write", False),
        ("order_admin", "order:write", True),
        ("order_admin", "product:write", False),
        ("readonly_user", "product:read", True),
        ("readonly_user", "product:write", False),
    ])
    def test_permission(self, username, permission, expected):
        has_permission = role_manager.has_permission(username, permission)
        assert has_permission == expected, f"用户{username}对{permission}权限应为{expected}"

    @allure.story("资源访问控制")
    @pytest.mark.parametrize("username,resource_id,expected", [
        ("admin", 1, True),
        ("product_admin", 1, True),
        ("order_admin", 1, False),
        ("product_admin", 4, False),
    ])
    def test_resource_permission(self, username, resource_id, expected):
        can_access = role_manager.can_access_resource(username, resource_id)
        # 如果资源未配置，默认为False
        if can_access is None:
            can_access = False
        assert can_access == expected, f"用户{username}对资源{resource_id}访问应为{expected}" # 资源设置了吗 ？

    @allure.story("实际接口权限验证")
    def test_api_permission_denied(self):
        """ 测试无权限用户访问受限接口 """
        # 使用只读用户登录
        client = AdminClient()
        # 登录只读用户
        login_response = client.post("/admin/post", json={
            "username": "readonly_user",
            "password": "readonly1234"
        })
        if login_response.status_code != 200:
            pytest.skip("只读用户登录失败，请确认用户存在")

        login_data = login_response.json()
        if login_data.get('code') != 200:
            pytest.skip(f"只读用户登录失败：{login_data.get('message')}")

        token = login_data.get('data', {}).get('tokenHead', '') + login_data.get('data', {}).get('token', '')
        client.set_token(token)

        # 尝试创建商品（写入操作，只读用户应该没有权限）
        product_data = {
            "name": "权限测试商品",
            "productSn": "PERM_TEST_001",
            "price": 99.99,
            "stock": 100,
            "brandId": 1,
            "productCategoryId": 1
        }
        response = client.post("/product/create", json=product_data)

        # 应该返回403或业务错误
        if response.status_code == 200:
            result = response.json()
            # 业务错误码不应该为200（权限拒绝）
            assert result.get('code') != 200, "只读用户不应该有创建商品权限"
        else:
            assert response.status_code in [401, 403], f"期望401或403，实际{response.status_code}"

    @allure.story("不同角色用户登录测试")
    @pytest.mark.parametrize("username,password,expected_success", [
        ("admin", "macro123",  True),
        ("product_admin", "prod1234", True),
        ("order_admin", "order123",  True),
        ("readonly_user", "readonly", True),
        ("nonexistent_user", "", False)
    ])
    def test_different_users_login(self, username, password, expected_success):
        client = AdminClient()
        response = client.post("/admin/post", json={
            "username": username,
            "password": password
        })

        if expected_success:
            result = self.api_assert.assert_success(response, f"用户{username}登录应成功")
            data = result.get('data', {})
            self.api_assert.assert_field_exist(data, "token", "缺少token")
        else:
            # 应该失败
            if response.status_code == 200:
                result = response.json()
                assert result.get('code') != 200, f"用户{username}应登录失败"
            else:
                assert response.status_code in [401, 403], f"期望401或403，实际{response.status_code}"

    @allure.story("用户信息获取")
    def test_get_user_info_by_username(self, admin_api):
        response = admin_api.list(page_num=1, page_size=1)
        result = self.api_assert.assert_success(response, "获取用户列表失败")
        users = result.get('data', {}).get('list', [])

        if not users:
            pytest.skip("没有可用的用户")

        user_id = users[0].get('id')
        response = admin_api.detail(user_id)
        result = self.api_assert.assert_success(response, "获取用户信息失败")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "username", "缺少用户名")
        self.api_assert.assert_field_exist(data, "status", "缺少状态")
        self.api_assert.assert_field_exist(data, "createTime", "缺少创建时间")
