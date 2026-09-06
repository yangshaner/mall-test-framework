# common/client/base_client.py

import time
import json
import allure
import requests
from typing import Optional,Dict,Any,Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps
import sys
import os

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # ?

from common.utils.logger import get_logger
from common.config.config_loader import config
from common.client.token_context import token_context

logger = get_logger(__name__)

def allure_step(func):
    """ Allure 步骤装饰器 """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        method = kwargs.get('method', func.__name__.upper())
        url = kwargs.get('url', args[0] if args else '')

        with allure.step(f"{method} {url}"):
            # 记录请求参数
            if kwargs.get('params'):
                allure.attach(
                    json.dumps(kwargs['params'], ensure_ascii=False, indent=2),
                    name="Request params",
                    attachment_type=allure.attachment_type.JSON
                )
            if kwargs.get('json'):
                allure.attach(
                    json.dumps(kwargs['json'], ensure_ascii=False, indent=2),
                    name="Request Body",
                    attachment_type=allure.attachment_type.JSON
                )
            result = func(self, *args, **kwargs)

            # 记录响应
            if result:
                try:
                    response_data = result.json() if result.text else {}
                    allure.attach(
                        json.dumps(response_data, ensure_ascii=False, indent=2)[:500],
                        name="Request Body",
                        attachment_type=allure.attachment_type.JSON
                    )
                except:
                    pass

                allure.attach(
                    str(result.status_code),
                    name="Request Status",
                    attachment_type=allure.attachment_type.TEXT
                )
            return result
    return wrapper


class BaseClient:
    """ HTTP 客户端基类 - 整个框架的核心 """

    def __init__(
            self,
            base_url: str,
            timeout: int = 30,
            retry_times: int = 3,
            retry_backoff: float = 1.0, # ?
            verify_ssl: bool = False,
            client_type: str ="default"
    ):

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.client_type = client_type
        self._is_refreshing = False # 防止刷新循环

        # 创建 Session
        self.session = requests.Session()

        # 配置重试
        retry_strategy = Retry(
            total=retry_times,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 502, 503, 504], # 移除500，让500直接抛出
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 默认 Headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MallAPITest/1.0"
        })

        # Token管理
        self._token = None
        self._token_type = "Bearer"
        self._token_expire_time = 0

        # 注册Token刷新回调 ？
        # token_context.register_refresh_callback(client_type, self._refresh_token_callback)

        logger.info(f"BaseClient initialized with base_url: {base_url}, client_type: {client_type}")

    def _refresh_token_callback(self, **kwargs):
        """ Token刷新回调 - 子类重写 """
        return None

    def _get_auth_header(self) -> Optional[str]:
        """ 获取认证头（从Token上下文） """
        return token_context.get_auth_header(self.client_type)
        #if self._token:
        #    return f"{self._token_type} {self._token}"

    def set_token(self, token: str, token_type: str = "Bearer", expire_in: int = 7200):
        # 设置token
        self._token = token
        self._token_type = token_type
        self._token_expire_time = time.time() + expire_in
        self._update_auth_header()
        logger.info(f"Token set for {self.client_type}, expires in {expire_in}s")

        """ 更新当前Session的Authorization头，并更新上下文 """
        if token:
            self.session.headers.update({"Authorization": f"{token_type} {token}"})
            print("token update")
            # 同时更新上下文（实际Token信息由上下文管理 ？）
            # 但我们不在这里设置过期时间，由调用方或者_login设置
        else:
            self.session.headers.pop("Authorization", None)

    def get_token(self) -> Optional[str]:
        """ 获取当前token """
        return self._token


    def _update_auth_header(self):
        # 更新默认头
        if self._token:
            self.session.headers.update({
                "Authorization": f"{self._token_type} {self._token}"
            })
        else:
            self.session.headers.pop("Authorization", None)


    def is_token_expired(self) -> bool:
        """ 检查Token是否过期 """
        if not self._token:
            return True
        return time.time() >= self._token_expire_time - 60 # 提前1min刷新

    def _ensure_token(self):
        """ 确保Token有效 - 子类重写 """
        pass


    def clear_token(self):
        self._token = None
        self._token_expire_time = 0
        self._update_auth_header()


    def _refresh_token(self):
        """ 刷新Token - 子类可重写 """
        if self._is_refreshing:
            logger.warning("Already refreshing, skip recursive refresh")
            return

        self._is_refreshing = True

        try:
            if hasattr(self, '_login'):
                result = self._login()
                # 更新token上下文
                token_context.set_token(
                    result.get('token'),
                    client_type=self.client_type,
                    token_type="Bearer",
                    expire_in=result.get('expire_in', 7200)
                )
                # 更新当前session
                self.set_token(result.get('token'))
                logger.info(f"Token refreshed for {self.client_type}")
            else:
                logger.warning(f"No _login method for client_type {self.client_type}, can not refresh")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
        finally:
            self._is_refreshing = False

    # 核心底层请求方式（不处理401）
    def _execute_request(
            self,
            method: str,
            path: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            json: Optional[Dict] = None,
            files: Optional[Dict] = None,
            headers: Optional[Dict] = None,
            timeout: Optional[int] = None,
            use_token: bool = True,
            **kwargs
    ) -> requests.Response:
        """
        执行底层HTTP请求，不进行401自动刷新
        用于登录等需要绕过认证逻辑的场景
        """
        url = f"{self.base_url}{path}"

        # 合并headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        # 自动添加token
        if use_token:
            auth_header = self._get_auth_header()
            if auth_header:
                req_headers['Authorization'] = auth_header

        timeout = timeout or self.timeout

        # 记录请求日志
        auth_info = "Bearer ***" if self._token else "No Auth"
        logger.info(f"Request: {method} {url} [Auth: {auth_info}]")
        if params:
            logger.debug(f"Params: {params}")
        if json:
            logger.debug(f"JSON: {json}")
        if data:
            logger.debug(f"Data: {data}")

        start_time = time.time()
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                files=files,
                headers=req_headers,
                timeout=timeout,
                verify=self.verify_ssl,
                **kwargs
            )

            elapsed = time.time() - start_time
            logger.info(f"Response: {response.status_code} ({elapsed:.3f} s)")
            if response.text:
                logger.debug(f"Response body: {response.text[:500]}")

            with allure.step(f"Response: {response.status_code}"):
                allure.attach(
                    str(elapsed),
                    name="Response Time(s)",
                    attachment_type=allure.attachment_type.TEXT
                )

            return response

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {method} {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def _do_request(
            self,
            method: str,
            path: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            json: Optional[Dict]  = None,
            files: Optional[Dict] = None,
            headers: Optional[Dict] = None,
            timeout: Optional[int] = None,
            use_token: bool = True,
            **kwargs
    ) -> requests.Response:
        """ 实际执行HTTP请求 """
        url = f"{self.base_url}{path}"

        # 合并headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        # 自动添加token
        if use_token:
            auth_header = self._get_auth_header()
            if auth_header:
                req_headers['Authorization'] = auth_header

        timeout = timeout or self.timeout

        # 记录请求日志
        auth_info = "Bearer ***" if self._token else "No Auth"
        logger.info(f"Request: {method} {url} [Auth: {auth_info}]")
        if params:
            logger.debug(f"Params: {params}")
        if json:
            logger.debug(f"JSON: {json}")
        if data:
            logger.debug(f"Data: {data}")

        start_time = time.time()
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                files=files,
                headers=req_headers,
                timeout=timeout,
                verify=self.verify_ssl,
                **kwargs
            )

            elapsed = time.time() - start_time
            logger.info(f"Response: {response.status_code} ({elapsed:.3f} s)")
            if response.text:
                logger.debug(f"Response body: {response.text[:500]}")

            with allure.step(f"Response: {response.status_code}"):
                allure.attach(
                    str(elapsed),
                    name="Response Time(s)",
                    attachment_type=allure.attachment_type.TEXT
                )

            return response

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {method} {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    @allure_step
    def request(
            self,
            method: str,
            path: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
            json: Optional[Dict] = None,
            files: Optional[Dict] = None,
            headers: Optional[Dict] = None,
            timeout: Optional[int] = None,
            usr_token: bool =True,
            **kwargs
    ) -> requests.Response:
        """ 统一请求入口，自动处理401 """

        # 确保认证头存在
        #if self._token:
        #    self._update_auth_header()

        # 第一次请求
        response = self._do_request(method, path, params, data, json, files, headers, timeout, usr_token, **kwargs)

        # 如果返回业务401且未在刷新中，则刷新token并重试（只重试一次）
        if not self._is_refreshing:
            try:
                resp_json = response.json()
                if resp_json.get('code') == 401:
                    logger.warning(f"业务401：{resp_json.get('message')}, 尝试刷新token")
                    self._refresh_token()
                    # 重试请求（关闭递归标志）
                    response = self._do_request(method, path, params, data, json, files, headers,
                                                timeout, usr_token, **kwargs)
            except (ValueError, AttributeError) as e:
                # 非JSON响应或解析失败，不处理
                pass
        return response

    def get(self, path: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, data: Optional[Dict] = None, json: Optional[Dict] =None,
             files:Optional[Dict] = None, **kwargs ) -> requests.Response:
        return self.request("POST", path, data=data, json=json, files=files, **kwargs)

    def put(self, path: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
            **kwargs ) -> requests.Response:
        return self.request("PUT", path, data=data, json=json, **kwargs)

    def delete(self, path: str, **kwargs ) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    def patch(self, path: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
              **kwargs ) -> requests.Response:
        return self.request("PATCH", path, data=data, json=json, **kwargs)

    def upload_file(self, path: str, file_path: str, field_name: str = 'file',
                    **kwargs ) -> requests.Response:
        with open(file_path, 'rb') as f:
            files = {field_name: (file_path, f, 'multipart/form-data')}
            return self.request("POST", path, files=files, **kwargs)

    def download_file(self, path: str, save_path: str, **kwargs ) -> str:
        response = self.get(path, stream=True, **kwargs)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Download file: {save_path}")
        return save_path