# common/client/token-manager.py

import threading
import time
import logging
from typing import Dict

from common.config.config_loader import config

logger = logging.getLogger(__name__)

class TokenManager:
    """ token管理器 - 支持多线程和并发 """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._tokens = {} # client_name -> token_info
        self._locks = {}   # client_name -> Lock
        self._login_funcs = {} # client_name -> login_function

        self._admin_token = None
        self._admin_token_expire = 0
        self._admin_lock = threading.Lock()

        self._member_token = None
        self._member_token_expire = 0
        self._member_lock = threading.Lock()

        # 配置文件
        self.admin_config = config.get('admin', {})
        self.member_config = config.get('member', {})

        logger.info("TokenManager initialized")

    def register_login_func(self, client_name: str, login_func):
        self._login_funcs[client_name] = login_func

    def get_token(self, client_name: str = 'admin', force_refresh: bool = False) -> str:
        if client_name not in self._locks:
            self._locks[client_name] = threading.Lock()

        with self._locks[client_name]:
            token_info = self._tokens.get(client_name, {})

            if force_refresh or self._is_token_expired(token_info):
                logger.info(f"Getting new token for {client_name}")
                token_info = self._login(client_name)
                self._tokens[client_name] = token_info

            return token_info.get('token', '')

    def _is_token_expired(self, token_info: Dict) -> bool:
        if not token_info:
            return True
        expire_time = token_info.get('expire_time', 0)
        return time.time() >= expire_time - 60

    def _login(self, client_name: str) -> Dict:
        """ 执行登录获取Token """
        login_func = self._login_funcs.get(client_name)
        if not login_func:
            raise ValueError(f"No login function registered for {client_name}")

        result = login_func() # func 哪来的
        token = result.get('token', '')
        expire_in = result.get('expire_time', 7200) # 7200 是什么

        return {
            'token': token,
            'expire_time': time.time() + expire_in,
        }

    def clear_token(self, client_name: str = None):
        if client_name:
            self._tokens.pop(client_name, None)
        else:
            self._tokens.clear()


class AdminTokenManager(TokenManager):

    def __init__(self):
        super().__init__()
        self._admin_token_func = None

    def register_admin_login(self, login_func):
        self.register_login_func("admin", login_func)

    def get_admin_token(self, force_refresh: bool = False) -> str :
        return self.get_token("admin", force_refresh)


class MemberTokenManager(TokenManager):

    def __init__(self):
        super().__init__()

    def register_member_login(self, login_func):
        self.register_login_func("member", login_func)

    def get_member_token(self, force_refresh: bool = False) -> str :
        return self.get_token("member", force_refresh)