# common/assertion/soft_assertion.py
import allure
from contextlib import contextmanager
from typing import Any

from .base_assertion import BaseAssertion
from .api_assertion import ApiAssertion
from .db_assertion import DBAssertion
from .redis_assertion import RedisAssertion

class SoftAssertion():
    """ 软断言上下文管理器 """

    def __init__(self):
        self.errors = []
        self.api = ApiAssertion()
        self.db = DBAssertion()
        self.redis = RedisAssertion()

    @contextmanager
    def context(self):
        """ 软断言上下文 """
        # 清空之前的错误
        self.errors = []
        self.api.clear_soft_errors()
        self.db.clear_soft_errors()
        self.redis.clear_soft_errors()

        try:
            yield self
        finally:
            # 收集所有断言错误
            self.errors.extend(self.api.get_soft_errors())
            self.errors.extend(self.db.get_soft_errors())
            self.errors.extend(self.redis.get_soft_errors())

            if self.errors:
                error_msg = "\n".join(self.errors)
                allure.attach(error_msg, name="软断言失败总汇",
                              attachment_type=allure.attachment_type.TEXT)

    def flush(self):
        """ 抛出所有软断言错误 """
        if self.errors:
            errors = "\n".join(self.errors)
            self.errors = []
            raise AssertionError(f"软断言失败：\n{errors}")

    def assert_success(self, response, message: str = "API请求失败"):
        """ 软断言API成功 """
        return self.api.assert_success(response, message, soft=True)

    def assert_field_equals(self, response, field: str, expected: Any,
                            message: str = "字段值不匹配"):
        """ 软断言字段值 """
        data = response.json().get('data', {})
        return self.api.assert_field_equals(data, field, expected, message, soft=True)

    def assert_db_exists(self, table: str, condition: str, params=None,
                         message: str = "数据不存在"):
        """ 软断言数据库数据存在 """
        return self.db.assert_exists(table, condition, params, message, soft=True)

    def assert_db_field(self, table: str, field: str, expected: Any,
                        condition: str, params=None, message: str = "字段值不匹配"):
        """ 软断言数据库字段值 """
        return self.db.assert_field_value(table, field, expected, condition, params, message, soft=True)

    def assert_redis_value(self, key: str, expected: Any,
                           message: str = "Redis值不匹配"):
        """ 软断言Redis值"""
        return self.redis.assert_value_equals(key, expected, message, soft=True)