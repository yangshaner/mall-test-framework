# testcases/member/test_login.py
import pytest
import allure

from common.assertions import ApiAssertion

@allure.feature("前台会员登录")
class TestMemberLogin:
    """ 会员登录测试 """

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("会员登录")
    def test_login_success(self, member_login_api):
        """ 测试会员登录成功 """
        response = member_login_api.login("test_user", "test1234")
        result = self.api_assert.assert_success(response, "会员登录失败")

        # 验证返回token
        token_data = result.get('data', {})
        self.api_assert.assert_field_exist(token_data, "token", "缺少token")
        self.api_assert.assert_field_exist(token_data, "tokenHead", "缺少tokenHead")  # ？

    @allure.story("会员登录")
    def test_login_wrong_password(self, member_login_api):
        """ 测试密码错误登录 """
        response = member_login_api.login("test_user", "wrong_password")
        # 应该返回业务错误
        result = response.json()
        assert result.get('code') != 200, "密码错误应该登录失败"

    @allure.story("会员登录")
    def test_login_empty_username(self, member_login_api):
        """ 测试用户名为空 """
        response = member_login_api.login("", "123456")
        result = response.json()
        assert result.get('code') != 200, "用户名为空应该登录失败"

    @allure.story("获取验证码")
    def test_get_auth_code(self, member_login_api):
        """ 测试获取验证码 """
        response = member_login_api.get_auth_code("13800138000")
        self.api_assert.assert_success(response, "获取验证码失败")

        # 验证验证码是否存入Redis
        # 实际测试中可以通过Redis查询验证（代码如何实现呢） ？

    @allure.story("获取会员信息")
    def test_get_member_info(self, member_login_api):
        """ 测试获取会员信息 """
        response = member_login_api.get_info()
        result = self.api_assert.assert_success(response, "获取会员信息失败")

        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, 'username', "缺少用户名")
        self.api_assert.assert_field_exist(data, 'status', "缺少状态")

    @allure.story("刷新Token")
    def test_refresh_token(self, member_login_api):
        """ 测试刷新Token """
        response = member_login_api.refresh_token()
        result = self.api_assert.assert_success(response, "刷新Token失败")

        token_data = result.get('data', {})
        self.api_assert.assert_field_exist(token_data, 'token', "缺少新token")
