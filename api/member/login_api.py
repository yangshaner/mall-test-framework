# api/member/login_api.py

import allure
from typing import Optional, Dict

from common.client.member_client import MemberClient

class MemberLoginApi:
    """ 会员登录注册API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("会员登录")
    def login(self, username: str, password: str) -> Dict:
        return self.client.post("/sso/login", params={
            "username": username,
            "password": password
        })

    @allure.step("会员注册")
    def register(self, username: str, password: str, telephone: str, auth_code: str) -> Dict:
        return self.client.post("/sso/register", params={
            "username": username,
            "password": password,
            "telephone": telephone,
            "authCode": auth_code
        })

    @allure.step("获取验证码")
    def get_auth_code(self, telephone: str) -> Dict:
        return self.client.get("/sso/getAuthCode", params={"telephone": telephone})

    @allure.step("修改密码")
    def update_password(self, telephone: str, password: str, auth_code: str) -> Dict:
        return self.client.post("/sso/updatePassword", params={
            "telephone": telephone,
            "password": password,
            "authCode": auth_code
        })

    @allure.step("刷新Token")
    def refresh_token(self) -> Dict:
        return self.client.get("/sso/refreshToken")

    @allure.step("获取会员信息")
    def get_info(self) -> Dict:
        return self.client.get("/sso/info")