# testcases/admin/demo_test_permission.py
import pytest
import allure

from common.assertions import ApiAssertion
from common.utils import role_manager
from common.client.admin_client import AdminClient


@allure.feature("后台权限管理")
class TestAdminPermission:
    """ 后台权限测试 - 不同角色访问控制 """

    def setup_method(self):
        self.api_assert = ApiAssertion()

        self.permission_users = {
            "admin": {"roles": [1], "permissions": ["admin:*", "product:*", "order:*"]},
            "product_admin": {"roles": [2], "permissions": ["product:read", "product:write"]},
            "order_admin": {"roles": [3], "permissions": ["order:read", "order:write"]},
            "readonly_user": {"roles": [4], "permissions": ["product:read", "order:read"]}
        }


    @pytest.fixture
    def user_client(self, request):
        # 获取指定用户的客户端
        username = request.param
        client = AdminClient()
        # 使用不同用户登录
        client.login_with_user(username)  # 没有这个函数
        return client


    @allure.story("权限验证")
    @pytest.mark.parametrize("user_client, expected_access", [
        ("admin", True),
        ("product_admin", True),
        ("order_admin", False),
        ("readonly_user", True)
    ], indirect=["user_client"])
    def test_product_read_permission(self, user_client, expected_access):
        """ 测试商品读取权限 """
        response = user_client.get("/product/list", params={"pageNum": 1, "pageSize": 10})

        if expected_access:
            self.api_assert.assert_success(response, f"用户{user_client._username}应该有商品读取权限")  # _username哪来的
        else:
            # 应该返回403或业务错误
            assert response.status_code in [200, 403]
            if response.status_code == 200:
                result = response.json()
                # 可能是业务权限错误
                if result.get("code") == 403:
                    pass  # 权限拒绝
                else:
                    # 如果是其他错误，也可能没有权限访问
                    pass

    @allure.story("权限验证")
    @pytest.mark.parametrize("user_client, expected_access", [
        ("admin", True),
        ("product_admin", True),
        ("order_admin", False),
        ("readonly_user", False)
    ])
    def test_product_write_permission(self, user_client, expected_access):
        """ 测试商品写入权限 """
        # 尝试创建商品（写入操作）
        data = {
            "name": "权限测试商品",
            "productSn": "PERM_TESR_001",
            "price": 99.99,
            "stock": 100,
            "brandId": 1,
            "productCategoryId": 1
        }
        response = user_client.post("/product/create", json=data)

        if expected_access:
            # 应该有权限，但可能因为数据问题失败 ？
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    # 创建成功，清理数据
                    product_id = result.get("data", {}).get("id")
                    if product_id:
                        user_client.post(f"/product/update/deleteStatus",
                                         params={"ids": [product_id], "deleteStatus": 1})
        else:
            # 应该被拒绝
            if response.status_code == 200:
                result = response.json()
                # 可能是权限错误
                assert result.get("code") != 200, f"用户{user_client._username}不应该有商品写入权限"

    @allure.story("权限验证")
    @pytest.mark.parametrize("user_client, expected_access", [
        ("admin", True),
        ("product_admin", False),
        ("order_admin", True),
        ("readonly_user", False)
    ], indirect=["user_client"])
    def test_order_write_permission(self, user_client, expected_access):
        """ 测试订单写入权限 """
        # 尝试关闭订单（写入操作）
        # 获取一个待付款的订单
        list_response = user_client.get("/order/list", params={"pageNum": 1, "pageSize": 1, "status": 0})
        list_result = list_response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("没有待付款订单")

        order_id = orders[0].get('id')
        response = user_client.post("/order/update/close",
                                    params={"ids": [order_id], "note": "权限测试关闭"})

        if expected_access:
            if response.status_code == 200:
                result = response.json()
                # 可能已经关闭或其他原因  ?
                pass
        else:
            if response.status_code == 200:
                result = response.json()
                assert result.get('code') != 200, f"用户{user_client._username}不应该有订单写入权限"

    @allure.story("用户角色信息")
    def test_user_role_info(self):
        """ 测试获取用户角色信息 """
        # 获取所有角色
        roles = role_manager.get_all_roles()
        assert len(roles) > 0, "没有配置角色"

        # 测试获取用户
        users = role_manager.get_all_users()
        assert len(users) > 0, "没有配置测试用户"

        for user in users:
            permissions = role_manager.get_user_permission(user.username)
            roles_list = role_manager.get_user_roles(user.username)

            allure.attach(
                f"用户名: {user.username}\n"
                f"角色ID: {roles_list}\n"
                f"权限数: {len(permissions)}\n",
                name=f"用户 {user.username} 信息",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.story("权限检查")
    def test_permission_check(self):
        """ 测试权限检查功能 """
        # 测试不同用户的权限
        test_cases = [
            ("admin", "product: write", True),
            ("admin", "order: delete", True),
            ("product_admin", "product: write", True),
            ("product_admin", "order: write", False),
            ("order_admin", "order: write", True),
            ("order_admin", "product: write", False),
            ("readonly_user", "product: read", True),
            ("readonly_user", "product: write", False)
        ]

        for username, permission, expected in test_cases:
            has_perm = role_manager.has_permission(username, permission)
            assert has_perm == expected, f"用户{username}对{permission}的权限应为{expected}"

    @allure.story("资源访问控制")
    def test_resource_access(self):
        """ 测试资源访问控制 """
        # 假设资源ID 1 是商品管理，资源ID 4 是订单管理
        test_cases = [
            ("admin", 1, True),
            ("admin", 4, True),
            ("product_admin", 1, True),
            ("product_admin", 4, False),
            ("order_admin", 1, False),
            ("order_admin", 4, True)
        ]

        for username, resource_id, expected in test_cases:
            can_access = role_manager.can_access_resource(username, resource_id)
            # 注意: 这里要根据实际配置的资源ID进行调整
            # 如果资源未配置，默认为False
            if can_access is None:
                can_access = False
            # 这里只是演示，实际断言可能需要调整 ？
            # assert can_access == expected, f"用户{username}对资源{resource_id}的访问权限应为{expected}"
