# common/client/member_client.py

from common.client.base_client import BaseClient
# from common.client.token_manager import MemberTokenManager
from common.client.token_context import token_context
from common.config.config_loader import config
import logging
import requests

logger = logging.getLogger(__name__)


class MemberClient(BaseClient):
    """ 前台客户端 - 支持多用户切换（前台为什么要用户切换，是不同用户之间的切换吗，不应该是后台用户切换吗） """

    def __init__(self, base_url: str = None, username: str = None):
        base_url = base_url or config.get("member", {}).get("base_url")
        super().__init__(base_url, client_type="member")

        # 注册登录函数
        # self.token_manager.register_member_login(self._login)

        self._username = username or config.get("member", {}).get("username", "test_user")
        self._password = config.get("member", {}).get("password", "123456")
        print("username:", self._username, "password:", self._password)

        # 注册Token刷新回调
        # token_context.register_refresh_callback("member", self._refresh_callback)

    def _ensure_token(self):
        """ 确保Token有效 """
        #if self.is_token_expired():
        #    logger.info(f"Token expired for {self._username}, refreshing...")

        token_info = token_context.get_token_info("member")
        if not token_info or token_info.is_expired():
            logger.info(f"Token expired for {self._username}, refreshing...")
            self._login()

    # 原来的_Login
    def old_login(self) -> dict:
        """ 执行前台登录 - 使用requests直接请求，避免递归 """
        """
        member_config = config.get("member", {})
        response = self.post(
            '/member/login',
            json={
                'username': member_config.get("username", 'test_user'),
                'password': member_config.get("password", '123456')
            }
        )
        """
        try:
            # 直接使用requests发送登录请求
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
            # self.set_token(token)  # set_token哪来的 ？
            token_head = data.get('data', {}).get('tokenHead', '')

            # 处理token（可能有前缀）
            if token_head and not token.startswith(token_head):
                token = token_head + token

            # 设置token
            self.set_token(token)

            # 保存到上下文
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
        """ 执行登录，返回token信息 """
        response = self._do_request(
            "POST",
            "/sso/login",
            params={'username': self._username, 'password': self._password}  # 这里是params而不是和admin一样用json
        )
        # response.raise_for_status()

        # 打印响应内容编译调试
        logger.info(f"Login response status: {response.status_code}, body: {response.text[:200]}")

        # 检查HTTP状态
        if response.status_code != 200:
            raise Exception(f"Login http error: {response.status_code}: {response.text}")

        # 检查业务状态
        data = response.json()
        if data.get('code') != 200:
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
        token_data = data.get('data', {})
        # token = token_data.get('tokenHead', '') + token_data.get('token', '')
        token = token_data.get('token', '')  # 这里先不要加上tokenHead
        if not token:
            raise Exception(f"Login response missing token")

        # 更新当前token
        self.set_token(token)
        return {'token': token, 'expire_in': 7200}

    def _refresh_callback(self, **kwargs) -> dict:
        """ Token刷新回调 """
        username = kwargs.get("username", self._username)
        # 如果是切换用户，重新登录
        if username != self._username:
            self._username = username
        return self._login()

    def login_with_user(self, username: str, password: str = None):
        """ 使用指定用户登录 - 切换用户登录 """
        self._username = username
        if password:
            self._password = password

        # 清除旧token
        self.client_token()
        return self._login()

        #result = self._login()
        # 更新Token上下文
        #token_context.set_token(
        #    result.get("token"),
        #    client_type="member",
        #    user_info={'username': username}
        #)
        #return result

    def client_token(self):
        """ 清除Token """
        super().clear_token()
        token_context.clear_token("member")

    """
    def ensure_token(self):
        if self.is_token_expired():
            self._login()
    """

    def request(self, method: str, path: str, **kwargs):
        """  重写request，确保token有效"""
        """
        self.ensure_token()
        return super().request(method, path, **kwargs)
        """

        # 从上下文中获取Token
        auth_header = token_context.get_auth_header("member")
        if auth_header:
            self.session.headers['Authorization'] = auth_header

        # 检查Token有效性
        token_info = token_context.get_token_info('member')
        if not token_info or token_info.is_expired():
            logger.info("Token expired, refreshing...")
            self._login()
            auth_header = token_context.get_auth_header("member")
            if auth_header:
                self.session.headers['Authorization'] = auth_header
        return super().request(method, path, **kwargs)


