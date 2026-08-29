# testcases/admin/test_login.py
import pytest
import allure

from common.assertions import ApiAssertion
from common.client.admin_client import AdminClient


@allure.feature("后台登录认证")
class TestAdminLogin:
    """ 后台登录、登出、刷新Token等测试 """

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("登录")
    def test_login_success(self, admin_api):
        """ 测试后台管理员登录成功 """
        response = admin_api.login("admin", "macro123")
        result = self.api_assert.assert_success(response, "管理员登录失败", check_response_code=False, check_data=False)
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "token", "缺少token")
        self.api_assert.assert_field_exist(data, "tokenHead", "缺少tokenHead")

        # 验证token格式
        token = data.get('token')
        assert len(token) > 0, "token为空"
        assert data.get('tokenHead') in ['Bearer ', ''], 'tokenHead格式错误'

    @allure.story("登录")
    def test_login_wrong_password(self, admin_api):
        response = admin_api.login("demo", "wrong_password")
        # 预期失败，可能是401或业务错误
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            result = response.json()
            assert result.get('code') != 200, "密码错误不应该返回成功"

    @allure.story("登录")
    def test_login_empty_username(self, admin_api):
        response = admin_api.login("", "demo1234")
        result = response.json()
        assert result.get('code') != 200, "用户名为空应失败"

    @allure.story("登录")
    def test_login_empty_password(self, admin_api):
        response = admin_api.login("demo", "")
        result = response.json()
        assert result.get('code') != 200, "密码为空应失败"

    @allure.story("登出")
    def test_logout(self, admin_client):
        response = admin_client.post("/admin/logout")
        self.api_assert.assert_success(response, "登出失败", check_data=False)

    @allure.story("刷新Token")
    def test_refresh_token(self, admin_client):
        response = admin_client.get("/admin/refreshToken")
        result = self.api_assert.assert_success(response, "刷新token失败")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "token", "刷新后缺少token")
        self.api_assert.assert_field_exist(data, "tokenHead", "刷新后缺少tokenHead")

    @allure.story("获取当前用户信息")
    def test_get_admin_info(self, admin_client):
        response = admin_client.get("/admin/info")
        result = self.api_assert.assert_success(response, "获取用户信息失败")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, "username", "缺少用户名")
        self.api_assert.assert_field_exist(data, "roles", "缺少角色")

    @allure.story("用户注册")
    def test_register_user(self, admin_api, data_generator):
        username = f"test_{data_generator.random_string(6)}"
        data = {
            "username": username,
            "password": "12345678",
            "nickName": f"测试用户_{username}",
            "email": f"{username}@test.com"
        }
        response = admin_api.register(data)
        result = self.api_assert.assert_success(response, "用户注册失败")
        user_data = result.get('data', {})
        self.api_assert.assert_field_exist(user_data, 'id', "缺少用户ID")

        # clear
        user_id = user_data.get('id')
        if user_id:
            admin_api.delete(user_id)
