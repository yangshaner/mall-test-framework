# common/client/base_client.py

import time
import json
import allure
import requests
from typing import Optional,Dict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import wraps
import sys
import os

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.utils.logger import get_logger
from common.client.token_context import token_context

logger = get_logger(__name__)

def allure_step(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        method = kwargs.get('method', func.__name__.upper())
        url = kwargs.get('url', args[0] if args else '')

        with allure.step(f"{method} {url}"):
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

            if result:
                try:
                    response_data = result.json() if result.text else {}
                    allure.attach(
                        json.dumps(response_data, ensure_ascii=False, indent=2)[:500],
                        name="Response Body",
                        attachment_type=allure.attachment_type.JSON
                    )
                except:
                    pass

                allure.attach(
                    str(result.status_code),
                    name="Response Status",
                    attachment_type=allure.attachment_type.TEXT
                )
            return result
    return wrapper


class BaseClient:

    def __init__(
            self,
            base_url: str,
            timeout: int = 30,
            retry_times: int = 3,
            retry_backoff: float = 1.0,
            verify_ssl: bool = False,
            client_type: str ="default"
    ):

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.client_type = client_type
        self._is_refreshing = False

        self.session = requests.Session()

        retry_strategy = Retry(
            total=retry_times,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MallAPITest/1.0"
        })

        self._token = None
        self._token_type = "Bearer"
        self._token_expire_time = 0

        logger.info(f"BaseClient initialized with base_url: {base_url}, client_type: {client_type}")

    def _refresh_token_callback(self, **kwargs):
        return None

    def _get_auth_header(self) -> Optional[str]:
        return token_context.get_auth_header(self.client_type)

    def set_token(self, token: str, token_type: str = "Bearer", expire_in: int = 7200):
        self._token = token
        self._token_type = token_type
        self._token_expire_time = time.time() + expire_in
        self._update_auth_header()
        logger.info(f"Token set for {self.client_type}, expires in {expire_in}s")

        if token:
            self.session.headers.update({"Authorization": f"{token_type} {token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def get_token(self) -> Optional[str]:
        return self._token

    def _update_auth_header(self):
        if self._token:
            self.session.headers.update({
                "Authorization": f"{self._token_type} {self._token}"
            })
        else:
            self.session.headers.pop("Authorization", None)

    def is_token_expired(self) -> bool:
        if not self._token:
            return True
        return time.time() >= self._token_expire_time - 60 # 提前1min刷新

    def _ensure_token(self):
        pass

    def clear_token(self):
        self._token = None
        self._token_expire_time = 0
        self._update_auth_header()

    def _refresh_token(self):
        if self._is_refreshing:
            logger.warning("Already refreshing, skip recursive refresh")
            return

        self._is_refreshing = True

        try:
            if hasattr(self, '_login'):
                result = self._login()
                token_context.set_token(
                    result.get('token'),
                    client_type=self.client_type,
                    token_type="Bearer",
                    expire_in=result.get('expire_in', 7200)
                )
                self.set_token(result.get('token'))
                logger.info(f"Token refreshed for {self.client_type}")
            else:
                logger.warning(f"No _login method for client_type {self.client_type}, can not refresh")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
        finally:
            self._is_refreshing = False

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
        url = f"{self.base_url}{path}"

        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        if use_token:
            auth_header = self._get_auth_header()
            if auth_header:
                req_headers['Authorization'] = auth_header

        timeout = timeout or self.timeout

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
        url = f"{self.base_url}{path}"

        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)

        if use_token:
            auth_header = self._get_auth_header()
            if auth_header:
                req_headers['Authorization'] = auth_header

        timeout = timeout or self.timeout

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
        response = self._do_request(method, path, params, data, json, files, headers, timeout, usr_token, **kwargs)

        if not self._is_refreshing:
            try:
                resp_json = response.json()
                if resp_json.get('code') == 401:
                    logger.warning(f"业务401：{resp_json.get('message')}, 尝试刷新token")
                    self._refresh_token()
                    response = self._do_request(method, path, params, data, json, files, headers,
                                                timeout, usr_token, **kwargs)
            except (ValueError, AttributeError) as e:
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