# common/assertions/redis_assertion.py

import allure
from typing import Optional, Any, List

from .base_assertion import BaseAssertion
from common.db.redis_util import redis_util

class RedisAssertion(BaseAssertion):
    """ Redis断言 """

    def __init__(self):
        super().__init__()
        self._redis = redis_util

    @allure.step("断言Redis键存在")
    def assert_key_exists(self, key: str,
                           message: str = "Redis键不存在",
                          soft: bool = False):
        """ 断言Redis键存在 """
        exists = self._redis.exists(key)
        return self._assert(exists, f"{message}: key={key}",
                            "存在", exists, soft)

    @allure.step("断言Redis键不存在")
    def assert_key_not_exists(self, key: str,
                              message: str = "Redis键存在",
                              soft: bool = False):
        """ 断言Redis键不存在 """
        exists = self._redis.exists(key)
        return self._assert(not exists, f"{message}: key={key}",
                            "不存在", exists, soft)

    @allure.step("断言Redis值相等")
    def assert_value_equals(self, key: str, expected: Any,
                            message: str = "Redis值不匹配",
                            soft: bool = False):
        """ 断言Redis值相等 """
        actual = self._redis.get(key)
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("断言Redis Hash值")
    def assert_hash_field(self, key: str, field: str, expected: Any,
                          message: str = "Hash字段值不匹配",
                          soft: bool = False):
        """ 断言 Redis Hash 字段值 """
        actual = self._redis.hget(key, field)
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("断言Redis Hash存在")
    def assert_hash_exists(self, key: str, field: str,
                           message: str = "Hash字段不存在",
                           soft: bool = False):
        """ 断言Redis Hash字段存在 """
        actual = self._redis.hget(key, field)
        return self.assert_is_not_none(actual, message, soft)

    @allure.step("断言Redis Set包含成员")
    def assert_set_contains(self, key: str, member: Any,
                            message: str = "Set不包含成员",
                            soft: bool = False):
        """ 断言Redis Set包含成员 """
        members = self._redis.smembers(key)
        return self.assert_in(member, members, message, soft)

    @allure.step("断言Redis List长度")
    def assert_list_length(self, ket: str, expected_length: int,
                           message: str = "List长度不匹配",
                           soft: bool = False):
        """ 断言Redis List长度 """
        items = self._redis.lrange(ket, 0, -1)
        return self.assert_equals(len(items), expected_length, message, soft)