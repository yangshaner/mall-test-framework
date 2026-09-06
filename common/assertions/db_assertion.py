# common/assertion/db_assertion.py
import  allure
from typing import Optional, Any, List, Tuple

from .base_assertion import BaseAssertion
from common.db.mysql_util import mysql


class DBAssertion(BaseAssertion):
    """ 数据库断言 """

    def __init__(self):
        super().__init__()
        self._mysql = mysql

    @allure.step("断言数据库存在")
    def assert_exists(self, table: str, condition: str,
                     params: Optional[Tuple] = None,
                     message: str = "数据不存在",
                     soft: bool = False):
        """ 断言数据存在 """
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self._assert(
            count > 0,
            f"{message}: {table} WHERE {condition}",
            "存在",
            count,
            soft
        )

    @allure.step("断崖数据不存在")
    def assert_not_exists(self, table: str, condition: str,
                         params: Optional[Tuple] = None,
                         message: str = "数据存在",
                         soft: bool = False):
        """ 断言数据不存在 """
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self._assert(
            count == 0,
            f"{message}: {table} WHERE {condition}",
            "不存在",
            count,
            soft
        )

    @allure.step("断言字段值相等")
    def assert_field_value(self, table: str, field: str,
                           expected: Any, condition: str,
                           params: Optional[Tuple] = None,
                           message: str = f"字段值不匹配",
                           soft: bool = False):
        """ 断言字段值相等 """
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"未找到数据: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        print(f"actual:{actual}, actual_type:{type(actual)}, expected:{expected}, expected_type:{type(expected)}")
        message = f"{field}"+message
        return self.assert_equals(actual, expected, message, soft)

    @allure.step("断言字段值在列表中")
    def assert_field_in_list(self, table: str, field: str,
                             expected_list: List[Any], condition: str,
                             params: Optional[Tuple] = None,
                             message: str = "字段值不在列表中",
                             soft: bool = False):
        """ 断言字段值在列表中 """
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"未找到数据：{table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_in(actual, expected_list, message, soft)

    @allure.step("断言记录数")
    def assert_count(self, table: str, expected_count: int,
                     condition: Optional[str] = None,
                     params: Optional[Tuple] = None,
                     message: str = "记录数不匹配",
                     soft: bool = False):
        """ 断崖记录数 """
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        if condition:
            sql += f" WHERE {condition}"
        result = self._mysql.query(sql, params)
        count = result[0].get("cnt", 0) if result else 0
        return self.assert_equals(count, expected_count, message, soft)

    @allure.step("断言查询结果不为空")
    def assert_query_result(self, sql: str,
                            params: Optional[Tuple] = None,
                            message: str = "查询结果为空",
                            soft: bool = False):
        """ 断言查询结果不为空 """
        result = self._mysql.query(sql, params)
        return self._assert(bool(result), message, "非空结果", result, soft)

    @allure.step("断言查询结果为空")
    def assert_query_empty(self, sql: str,
                           params: Optional[Tuple] = None,
                           message: str = "查询结果应为空",
                           soft: bool = False):
        """ 断言查询结果为空 """
        result = self._mysql.query(sql, params)
        return self._assert(not result, message, "空结果", result, soft)

    @allure.step("断言字段非空")
    def assert_field_not_null(self, table: str, field: str,
                               condition: str, params: Optional[Tuple] = None,
                               message: str = "字段为空",
                               soft: bool = False):
        """ 断言字段非空 """
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"未找到数据: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_is_not_none(actual, message, soft)

    @allure.step("断言字段为空")
    def assert_field_null(self, table: str, field: str,
                          condition: str, params: Optional[Tuple] = None,
                          message: str = "字段为空", soft: bool = False):
        """ 断言字段为空 """
        sql = f"SELECT {field} FROM {table} WHERE {condition}"
        result = self._mysql.query(sql, params)
        if not result:
            return self._assert(False, f"未找到数据: {table} WHERE {condition}", soft=soft)

        actual = result[0].get(field)
        return self.assert_is_none(actual, message, soft)