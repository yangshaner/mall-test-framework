# common/client/admin_client.py
import requests

from common.client.base_client import BaseClient
from common.config.config_loader import config
from common.client.token_context import token_context


class AdminClient(BaseClient):

    def __init__(self, base_url: str = None, username: str = None):
        base_url = base_url or config.get("admin", {}).get("base_url")
        super().__init__(base_url)

        self._username = username or  config.get("admin", {}).get("username", "admin")
        self._password = config.get("admin", {}).get("password", "123456")

        # 注册Token刷新回调
        # token_context.register_refresh_callback("admin", self._refresh_callback)

    # 原来的_login
    def old_login(self) -> dict:
        admin_config = config.get("admin", {})
        login_url = f"{self.base_url}/admin/login"

        # 先清除旧token
        self.clear_token()

        response = requests.post(
            login_url,
            json={
                'username': admin_config.get("username", 'admin'),
                'password': admin_config.get("password", 'macro123')
            }
        )
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 200:
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")

        token_data = data.get("data", {})
        # token = token_data.get("tokenHead", '') + token_data.get('token', '') # tokenHead 是什么
        token = token_data.get('token', '') # tokenHead 是什么
        print("admin token:", token)


        self.set_token(token, expire_in=7200)
        self._is_logged_in = True
        print("set self admin token,", self._token)
        # 需要和member_client.py一样也设置token_context吗  应该不用吧，因为用不到多线程

        """
        token_context.set_token(
            token,
            client_type="admin",
            token_type="Bearer",
            expire_in=7200,
            user_info={"username": self._username}
        )
        """


        return {
            'token': token,
            'expire_in': 7200,
             'user_info':{'username': admin_config.get("username", 'admin')} #
        }


    def _login(self) -> dict:
        """ 执行登录，返回token信息 """
        response = self._do_request(
            "post",
            "/admin/login",
            json={"username": self._username, "password": self._password}
        )
        response.raise_for_status()
        data = response.json()
        if data.get('code') != 200:
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
        token_data = data.get("data", {})
        # token = token_data.get('tokenHead', '') + token_data.get('token', '')
        token = token_data.get('token', '') # tokenHead在set_token那里去设置
        # 更新当前session
        self.set_token(token)
        return {'token': token, 'expire_in': 7200}


    def login_with_user(self, username: str, password: str = None):
        """ 使用指定用户登录 - 切换用户登录 """
        self._username = username
        if password:
            self._password = password
        return self._login()

    def _refresh_callback(self, **kwargs) -> dict:
        """ Token刷新回调 """
        username = kwargs.get("username", self._username)
        if username != self._username:
            self._username = username
        return self._login()

    def ensure_token(self):
        if not self._is_logged_in or self.is_token_expired():
            self._login()

"""
    def request(self, method: str, path: str, **kwargs):
        # 重写request，确保token有效
        self.ensure_token()

        # 打印当前token状态
        print(f"Requesting {method} {path}, token present: {bool(self._token)}")
        if self._token:
            print(f"Authorization header: {self.session.headers.get('Authorization', 'Not Set')[:30]}...")


        # 从上下文获取Token并设置到headers
        #auth_header = token_context.get_auth_header('admin')
        #if auth_header:
        #    self.session.headers['Authorization'] = auth_header

        # 确保认证头存在
        self._update_auth_header()

        return super().request(method, path, **kwargs)
"""