# common/client/admin_client.py
import requests

from common.client.base_client import BaseClient
from common.config.config_loader import config


class AdminClient(BaseClient):

    def __init__(self, base_url: str = None, username: str = None):
        base_url = base_url or config.get("admin.base_url")
        super().__init__(base_url)

        self._username = username or  config.get("admin", {}).get("username", "admin")
        self._password = config.get("admin", {}).get("password", "123456")

    def old_login(self) -> dict:
        admin_config = config.get("admin", {})
        login_url = f"{self.base_url}/admin/login"

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
        token = token_data.get('token', '')

        self.set_token(token, expire_in=7200)
        self._is_logged_in = True

        return {
            'token': token,
            'expire_in': 7200,
             'user_info':{'username': admin_config.get("username", 'admin')} #
        }

    def _login(self) -> dict:
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
        token = token_data.get('token', '')
        self.set_token(token)
        return {'token': token, 'expire_in': 7200}

    def login_with_user(self, username: str, password: str = None):
        self._username = username
        if password:
            self._password = password
        return self._login()

    def _refresh_callback(self, **kwargs) -> dict:
        username = kwargs.get("username", self._username)
        if username != self._username:
            self._username = username
        return self._login()

    def ensure_token(self):
        if not self._is_logged_in or self.is_token_expired():
            self._login()