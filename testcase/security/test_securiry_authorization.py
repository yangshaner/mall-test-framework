# testcase/security/test_security_authorization.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("安全测试-授权与访问控制")
class TestSecurityAuthorization:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("未授权访问后台接口")
    def test_unauthorized_admin_access(self, anon_session, admin_base_url):
        response = anon_session.get(f"{admin_base_url}/product/list", params={"pageNum": 1, "pageSize": 10})
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "未授权访问后台接口应被拒绝"

    @allure.story("未授权访问前台需认证接口")
    @pytest.mark.parametrize("path", [
        "/cart/list",
        "/order/list",
        "/member/coupon/list",
        "/member/productCollection/list",
    ])
    def test_unauthorized_member_protected(self, anon_session, member_base_url, path):
        response = anon_session.get(f"{member_base_url}{path}")
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            f"未授权访问 {path} 应被拒绝"

    @allure.story("公共接口无需认证")
    @pytest.mark.parametrize("path,params", [
        ("/product/search", {"pageNum": 1, "pageSize": 5}),
        ("/home/content", None),
    ])
    def test_public_api_no_auth_needed(self, anon_session, member_base_url, path, params):
        response = anon_session.get(f"{member_base_url}{path}", params=params)
        result = response.json()
        assert response.status_code == 200, f"公开接口 {path} HTTP 状态码异常"
        assert result.get("code") == 200, f"公开接口 {path} 业务码应为 200"

    @allure.story("伪造 Token 访问")
    def test_forged_token_access(self, anon_session, admin_base_url):
        headers = {"Authorization": "Bearer forged.invalid.token.string"}
        response = anon_session.get(
            f"{admin_base_url}/product/list",
            params={"pageNum": 1, "pageSize": 10},
            headers=headers
        )
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "伪造 Token 访问后台接口应被拒绝"

    @allure.story("跨端 Token 不通用")
    def test_member_token_cannot_access_admin(self, member_client, admin_base_url):
        member_token = member_client.get_token()
        if not member_token:
            pytest.skip("会员 Token 未获取")

        import requests
        response = requests.get(
            f"{admin_base_url}/product/list",
            params={"pageNum": 1, "pageSize": 10},
            headers={"Authorization": f"Bearer {member_token}"}
        )
        result = response.json()
        assert response.status_code in (401, 403) or result.get("code") != 200, \
            "前台 Token 不应能访问后台管理接口"

    @allure.story("只读用户越权写操作")
    def test_readonly_user_create_product_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("readonly_user", "readonly")
        except Exception as e:
            pytest.skip(f"只读用户登录失败：{e}")

        product_data = {
            "name": "越权测试商品",
            "productSn": "SEC_TEST_001",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 1,
            "verifyStatus": 1,
        }
        response = client.post("/product/create", json=product_data)
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "只读用户不应能创建商品"

    @allure.story("商品管理员越权操作订单")
    def test_product_admin_access_order_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("product_admin", "prod1234")
        except Exception as e:
            pytest.skip(f"商品管理员登录失败：{e}")

        response = client.get("/order/list", params={"pageNum": 1, "pageSize": 10})
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "商品管理员不应能访问订单列表"

    @allure.story("订单管理员越权操作商品")
    def test_order_admin_create_product_denied(self, admin_client_factory):
        try:
            client = admin_client_factory("order_admin", "order123")
        except Exception as e:
            pytest.skip(f"订单管理员登录失败：{e}")

        product_data = {
            "name": "越权测试商品_订单管理员",
            "productSn": "SEC_TEST_002",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 1,
            "verifyStatus": 1,
        }
        response = client.post("/product/create", json=product_data)
        result = response.json()
        assert result.get("code") != 200 or response.status_code in (401, 403), \
            "订单管理员不应能创建商品"

    @allure.story("已禁用用户登录被拒")
    def test_disabled_user_login_denied(self, admin_base_url):
        import requests
        response = requests.post(
            f"{admin_base_url}/admin/login",
            json={"username": "disabled_user", "password": "macro123"}
        )
        result = response.json()
        assert result.get("code") != 200, "已禁用用户不应能登录成功"

    @allure.story("水平越权-访问他人订单")
    def test_horizontal_privilege_order(self, member_order_api):
        response = member_order_api.detail(999999999)
        result = response.json()
        if result.get("code") == 200:
            data = result.get("data") or {}
            order_items = data.get("orderItemList") or []
            has_order_identity = any(
                data.get(field) for field in ("orderSn", "id", "orderNo", "orderId")
            )
            assert len(order_items) == 0 and not has_order_identity, \
                "访问不存在/非本人订单不应返回有效订单数据"