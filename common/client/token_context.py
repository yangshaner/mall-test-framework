# common/client/token_context.py
import threading
import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """ Token信息 """
    token: str
    token_type: str
    expire_at: float
    refresh_token: Optional[str] = None
    user_info: Optional[Dict] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """ 判断Token是否过期（带缓冲） """
        if self.expire_at == 0:
            return True
        return time.time() >= self.expire_at - buffer_seconds  # ?

    def remaining_seconds(self) -> int:
        """ 剩余有效秒数 """
        if self.expire_at == 0:
            return 0
        return max(0, int(self.expire_at - time.time()))  # ?

    def to_dict(self) -> Dict:
        """ 转为字典 """
        return {
            'token': self.token,
            'token_type': self.token_type,
            'expire_at': self.expire_at,
            'refresh_token': self.refresh_token,
            'user_info': self.user_info,
            'created_at': self.created_at
        }

class TokenContext:
    """ Token上下文管理器 - 支持线程隔离 """

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

        # 线程本地存储
        self._local = threading.local()

        # 默认Token配置
        self._default_token = None
        self._default_token_type = "Bearer"

        # Token刷新回调
        self._refresh_callbacks = {}

        # 锁
        self._locks = {}
        self._global_lock = threading.Lock()

        logger.info("TokenContext initialized")

    def _get_lock(self, client_type: str = "default") -> threading.Lock:
        """ 获取客户端锁 """
        with self._global_lock:
            if client_type not in self._locks:
                self._locks[client_type] = threading.Lock()
            return self._locks[client_type]

    def _get_thread_token(self, client_type: str = "default") -> Optional[TokenInfo]:
        """ 获取当前线程的token """
        if not hasattr(self._local, 'tokens'):
            self._local.tokens = {}
        return self._local.tokens.get(client_type)

    def _set_thread_token(self, client_type: str, token_info: TokenInfo):
        """ 设置当前线程的Token """
        if not hasattr(self._local, 'tokens'):
            self._local.tokens = {}
        self._local.tokens[client_type] = token_info

    def set_token(self, token: str, client_type: str = "default",
                  token_type: str = "Bearer", expire_in: int = 7200,
                  refresh_token: Optional[str] = None,
                  user_info: Optional[Dict] = None):
        """ 设置Token（当前线程） """
        with self._get_lock(client_type):
            token_info = TokenInfo(
                token=token,
                token_type=token_type,
                expire_at=time.time() + expire_in,
                refresh_token=refresh_token,
                user_info=user_info or {}
            )
        self._set_thread_token(client_type, token_info)
        logger.info(f"Token set for {client_type}, expire in: {expire_in}")

    def get_token(self, client_type: str = "default") -> Optional[str]:
        """ 获取Token（当前线程） """
        token_info = self._get_thread_token(client_type)
        if not token_info:
            return self._default_token
        return token_info.token

    def get_token_info(self, client_type: str = "default") -> Optional[TokenInfo]:
        """ 获取Token信息（当前线程） """
        return self._get_thread_token(client_type)

    def get_auth_header(self, client_type: str = "default") -> Optional[str]:
        """ 获取认证头 """
        token_info = self._get_thread_token(client_type)
        if token_info:
            return f"{token_info.token_type} {token_info.token}"
        if self._default_token:

            return f"{self._default_token.type} {self._default_token.token}"
        return None

    def is_token_valid(self, client_type: str = "default") -> bool:
        """ 检查Token是否有效 """
        token_info = self._get_thread_token(client_type)
        if not token_info:
            return False
        return token_info.is_expired()

    def refresh_token(self, client_type: str = "default") -> Optional[str]:
        """ 刷新Token """
        callback = self._refresh_callbacks.get(client_type)
        if not callback:
            logger.warning(f"No refresh callback for {client_type}")
            return None

        with self._get_lock(client_type):
            try:
                result = callback()
                if result:
                    self.set_token(
                        result["token"],
                        client_type,
                        result.get("expire_type", "Bearer"),
                        result.get("expire_in", 7200),
                        result.get("refresh_token", None)
                    )
                    logger.info(f"Token refreshed for {client_type}")
                    return result.get("token")
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return None

    def register_refresh_callback(self, client_type: str, callback):
        """ 注册Token刷新回调 """
        self._refresh_callbacks[client_type] = callback

    @contextmanager
    def switch_user(self, username: str, client_type: str = "default"):
        """ 切换用户上下文 """
        # 保存当前Token
        old_token = self._get_thread_token(client_type)

        # 获取新用户的Token（通过刷新回调）
        callback = self._refresh_callbacks.get(client_type)
        if callback:
            try:
                # 传入用户名获取对应的Token
                result = callback(username=username)
                if result:
                    self.set_token(
                        result.get("token"),
                        client_type,
                        result.get("token_type", "Bearer"),
                        result.get("expire_in", 7200)
                    )
                    logger.info(f"Switched to user {username}")
            except Exception as e:
                logger.error(f"Switch user failed: {e}")

        try:
            yield self
        finally:
            # 恢复之前的Token
            if old_token:
                self._set_thread_token(client_type, old_token)
                logger.info(f"Restored previous token for {client_type}")

    @contextmanager
    def temp_token(self, token: str, client_type: str = "default",
                   token_type: str = "Bearer", expire_in: int = 7200):
        """ 临时Token上下文 """
        # 保存当前Token
        old_token = self._get_thread_token(client_type)

        # 临时设置Token
        self.set_token(token, client_type, token_type, expire_in)

        try:
            yield self
        finally:
            # 恢复之前的Token
            if old_token:
                self._set_thread_token(client_type, old_token)
            else:
                if hasattr(self._local, "tokens"):
                    self._local.tokens.pop(client_type, None)
            logger.info(f"Temp token cleared for {client_type}")

    def clear_token(self, client_type: str = "default"):
        """ 清除Token """
        if hasattr(self._local, 'tokens'):
            self._local.tokens.pop(client_type, None)
        logger.info(f"Token cleared for {client_type}")

    def clear_all_token(self):
        """ 清除所有Token """
        if hasattr(self._local, 'tokens'):
            self._local.tokens.clear()
        logger.info(f"All Token cleared")

    def set_default_token(self, token: str, token_type: str = "Bearer"):
        """ 设置默认Token """
        self._default_token = token
        self._default_token_type = token_type

# 全局Token上下文实例
token_context = TokenContext()