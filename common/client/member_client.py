# common/client/member_client.py

from common.client.base_client import BaseClient
from common.client.token_context import token_context
from common.config.config_loader import config
import logging
import requests

logger = logging.getLogger(__name__)


class MemberClient(BaseClient):

    def __init__(self, base_url: str = None, username: str = None):
        base_url = base_url or config.get("member", {}).get("base_url")
        super().__init__(base_url, client_type="member")

        self._username = username or config.get("member", {}).get("username", "test_user")
        self._password = config.get("member", {}).get("password", "123456")

    def _ensure_token(self):

        token_info = token_context.get_token_info("member")
        if not token_info or token_info.is_expired():
            logger.info(f"Token expired for {self._username}, refreshing...")
            self._login()

    def old_login(self) -> dict:
        try:
            login_url= f"{self.base_url}/sso/login"
            response = requests.post(
                login_url,
                params={
                    "username": self._username,
                    "password": self._password
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 200:
                raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")

            token = data.get('data', {}).get('token', '')
            token_head = data.get('data', {}).get('tokenHead', '')

            if token_head and not token.startswith(token_head):
                token = token_head + token

            self.set_token(token)

            token_context.set_token(
                token,
                client_type="member",
                expire_in=7200,
                user_info={'username': self._username}
            )

            logger.info(f"Member login success: {self._username}")

            return {
                'token': token,
                'expire_in': 7200,
                "use_info": {"username": self._username}
            }
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise


    def _login(self) -> dict:
        response = self._do_request(
            "POST",
            "/sso/login",
            params={'username': self._username, 'password': self._password}  # 这里是params而不是和admin一样用json
        )

        logger.info(f"Login response status: {response.status_code}, body: {response.text[:200]}")

        if response.status_code != 200:
            raise Exception(f"Login http error: {response.status_code}: {response.text}")

        data = response.json()
        if data.get('code') != 200:
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
        token_data = data.get('data', {})
        token = token_data.get('token', '')
        if not token:
            raise Exception(f"Login response missing token")

        self.set_token(token)
        return {'token': token, 'expire_in': 7200}

    def _refresh_callback(self, **kwargs) -> dict:
        username = kwargs.get("username", self._username)
        if username != self._username:
            self._username = username
        return self._login()

    def login_with_user(self, username: str, password: str = None):
        self._username = username
        if password:
            self._password = password

        self.client_token()
        return self._login()

    def client_token(self):
        super().clear_token()
        token_context.clear_token("member")

    def request(self, method: str, path: str, **kwargs):
        auth_header = token_context.get_auth_header("member")
        if auth_header:
            self.session.headers['Authorization'] = auth_header

        token_info = token_context.get_token_info('member')
        if not token_info or token_info.is_expired():
            logger.info("Token expired, refreshing...")
            self._login()
            auth_header = token_context.get_auth_header("member")
            if auth_header:
                self.session.headers['Authorization'] = auth_header
        return super().request(method, path, **kwargs)