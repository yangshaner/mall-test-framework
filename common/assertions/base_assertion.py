# common/assertion/base_assertion.py

import json
import logging
import allure
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
import pytest

logger = logging.getLogger(__name__)

class AssertionError(Exception):
    """ 自定义断言错误 """
    pass

def soft_assert(func):
    """ 软断言装饰器 - 收集所有断言错误，最后统一抛出 """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_soft_assert'):
            self._soft_assert = []

        try:
            result = func(self, *args, **kwargs)
            return result
        except AssertionError as e:
            self._soft_assert.append(str(e))
            logger.warning(f"软断言失败：{e}")
            return None
        except Exception as e:
            self._soft_assert.append(f"断言异常：{e}")
            logger.error(f"断言异常:{e}")
            return None

    return wrapper

class BaseAssertion:
    """ 断言基类 """

    def __init__(self):
        self._soft_errers = []

    def _assert(self, condition: bool, message: str,
                expected: Any = None, actual: Any = None,
                soft: bool = False,
                expected_label: str = "期望值",
                actual_label: str = "实际值"):
        """
        核心断言方法
        Args:
            condition: 断言条件
            message: 错误消息前缀
            expected: 期望值
            actual: 实际值
            soft: 是否为软断言
            expected_label: 期望值的显示标签
            actual_label: 实际值的显示标签
        """
        if not condition:
            full_message = message
            if expected is not None and actual is not None:
                full_message = f"{message}\n{expected_label}:{expected}\n{actual_label}:{actual}"
            elif expected is not None:
                full_message = f"{message}\n{expected_label}: {expected}"
            elif actual is not None:
                full_message = f"{message}\n{actual_label}:{actual}"

            # soft 是什么
            if soft:
                self._soft_errers.append(full_message)
                logger.warning(f"软断言失败: {full_message}")
            else:
                # Allure附件
                allure.attach(
                    full_message,
                    name="断言失败详情",
                    attachment_type=allure.attachment_type.TEXT)
                raise AssertionError(full_message)
        return True

    def assert_equals(self, expected: Any, actual: Any,
        message: str = "值不相等", soft: bool = False):
        """ 断言相等 """
        return self._assert(
            actual == expected,
            message,
            expected,
            actual,
            soft
        )

    def assert_not_equals(self, actual: Any, expected: Any,
                         message: str = "值不应相等", soft: bool = False):  # ？
        """ 断言不相等 """
        return self._assert(
            actual != expected,
            message,
            expected,
            actual,
            soft
        )

    def assert_true(self, condiction: bool, message: str = "条件不为True",
                    soft: bool = False):
        """ 断言为 True """
        return self._assert(condiction, message, True, condiction, soft)

    def assert_false(self, condiction: bool, message: str = "条件不为False",
                     soft: bool = False):
        """ 断言为 False """
        return self._assert(not condiction, message, False, condiction, soft)

    def assert_is_none(self, obj: Any, message: str = "对象不为None",
                       soft: bool = False):
        """ 断言为None """
        return self._assert(obj is None, message, None, obj, soft)

    def assert_is_not_none(self, obj: Any, message: str = "对象为None",
                           soft: bool = False):
        """ 断言不为None """
        return self._assert(obj is not None, message, "not None", obj, soft)

    def assert_in(self, member: Any, container: Union[list, tuple, set, dict, str],
                  message: str = "成员不在容器中", soft: bool = False):
        """ 断言成员在容器中 """
        return self._assert(member in container, message, container, member, soft)

    def assert_not_in(self, member: Any, container: Union[list, tuple, set, dict, str],
                      message: str = "成员在容器中", soft: bool = False):
        """ 断言成员不在容器中 """
        return self._assert(member not in container, message, container, member, soft)

    def assert_greater(self, actual: Union[int, float], expected: Union[int, float],
                       message: str = "实际值不大于期望值", soft: bool = False):
        """ 断言大于 """
        return self._assert(actual > expected, message, expected, actual, soft)

    def assert_greater_equal(self, actual: Union[int, float], expected: Union[int, float],
                             message: str = "实际值不小于期望值", soft: bool = False):
            """ 断言大于等于 """
            return self._assert(actual >= expected, message, expected, actual, soft)

    def assert_less(self, actual: Union[int, float], expected: Union[int, float],
                    message: str = "实际值不小于期望值", soft: bool = False):
        """ 断言小于 """
        return self._assert(actual < expected, message, expected, actual, soft)

    def assert_less_equal(self, actual: Union[int, float], expected: Union[int, float],
                          message: str = "实际值不大于期望值", soft: bool = False):
        """ 断言小于等于 """
        return self._assert(actual <= expected, message, expected, actual, soft)

    def assert_between(self, value: Union[int, float], min_val: Union[int, float],
                       max_val: Union[int, float], message: str = "值不在范围内", soft: bool = False):
        """ 断言值在范围内 """
        return self._assert(min_val <= value <= max_val, message, f"范围：[{min_val},{max_val}]", value, soft)

    def assert_type(self, obj: Any, expected_type: type, message: str = "类型不匹配", soft: bool = False):
        """ 断言类型 """
        return self._assert(isinstance(obj, expected_type), message,
                            expected_type.__name__, type(obj).__name__, soft,
                            expected_label="期望类型",
                            actual_label="实际类型"
                        )

    def assert_contains(self, container: Union[list, tuple, dict, str], item: Any,
                       message: str = "容器中不包含目标元素", soft: bool = False):
        """ 断言包含 """
        if isinstance(container, dict):
            contains = item in container or item in container.values()
        else:
            contains = item in container
        return self._assert(contains, message, container, item, soft,
                            expected_label="容器内容",
                            actual_label="目标元素")

    def assert_length(self, container: Union[list, tuple, dict, str], expected_length: int,
                      message: str = "长度不匹配", soft: bool = False):
        """ 断言长度 """
        actual_length = len(container)
        return self._assert(actual_length == expected_length, message, expected_length, actual_length, soft)

    def assert_regex_match(self, text: str, pattern: str,
                           message: str = "正则表达式不匹配", soft: bool = False ):
        """ 断言正则匹配 """
        import re
        return self._assert(re.search(pattern, text) is not None, message, pattern, text, soft,
                            expected_label="正则模式",
                            actual_label="文本内容")

    def assert_json_equals(self, actual: Union[str, dict], expected: Union[str, dict],
                           message: str = "JSON不相等", soft: bool = False):
        """ 断言JSON相等 """
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)
        return self.assert_equals(actual, expected, message, soft)

    def assert_json_contains(self, actual: Union[str, dict], expected: Union[str, dict],
                             message: str = "JSON不包含目标内容", soft: bool = False):
        """ 断言JSON包含 """
        if isinstance(actual, str):
            actual = json.loads(actual)
        if isinstance(expected, str):
            expected = json.loads(expected)

        def _deep_contains(a, b):
            if isinstance(b, dict):
                for k, v in b.items():
                    if k not in a:
                        return False
                    if not _deep_contains(a[k], v):
                        return False
                return True
            elif isinstance(b, list):
                for item in b:
                    if item not in a:
                        return False
                return True
            else:
                return b == a
        return self._assert(_deep_contains(actual, expected), message, expected, actual, soft,
                            expected_label="期望包含的内容",
                            actual_label="实际JSON")

    def assert_field_exist(self, obj: dict, required_fields: Union[List[str], str],
                            message: str = "缺少必要字段", soft: bool = False):
        """
        断言字段存在
        Args:
            obj: 要检查的字典
            required_fields: 必需的字段名（字符串或字符串列表）
            message: 错误消息前缀
            soft: 是否为软断言
        """
        # 确保 required_fields 是列表
        if isinstance(required_fields, str):
            required_fields = [required_fields]

        missing_fields = [f for f in required_fields if f not in obj]
        # return self._assert(len(missing_fields) == 0, f"{message}： 缺少字段{missing_fields}",
        #                    required_fields, list(obj.keys()), soft)
        if missing_fields:
            error_msg = f"{message}: 缺少字段 {missing_fields}"
            error_msg += f"\n实际存在的字段：{list(obj.keys())}"

            if soft:
                self._soft_errers.append(error_msg)
                logger.warning(f"软断言失败：{error_msg}")
                return False
            else:
                raise AssertionError(error_msg)
        return True

    def assert_field_type(self, obj: dict, field: str, expected_types: type,
                          message: str = "字段类型不匹配", soft: bool = False):
        """ 断言字段类型 """
        if field not in obj:
            error_msg = f"字段 '{field}' 不存在"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

            # return self._assert(False, f"字段 {field}", soft=soft)
        # return self._assert(obj[field], expected_types, message, soft)
        return self.assert_type(obj[field], expected_types, message, soft)

    def assert_field_equals(self, obj: dict, field: str, expected: Any,
                            message: str = "字段值不匹配", soft: bool = False):
        """
        断言字段值相等
        Args:
            obj: 要检查的字典
            field: 字段名
            expected: 期望值
            message: 错误消息前缀
            soft: 是否为软断言
        """
        if field not in obj:
            error_msg = f"字段 '{field}' 不存在"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(actual == expected,
                            f"{message} (字段：{field})",
                            expected,
                            actual,
                            soft,
                            expected_label="期望值",
                            actual_label="实际值")

            # return self._assert(False, f"字段 {field} 不存在", soft=soft)
        # return self._assert(obj[field], expected, expected, soft)


    def assert_filed_not_equals(self, obj: dict, field: str, expected: Any,
                                message: str = "字段值不应相等", soft: bool = False):
        """ 断言字段值不相等 """
        if field not in obj:
            error_msg = f"字段 '{field}' 不存在"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual != expected,
        f"{message} (字段:f{field})",
            expected,
            actual,
            soft,
            expected_label="期望不等于的值",
            actual_label="实际值")

    def assert_filed_greater(self, obj: dict, field: str, expected: Union[int, float],
                                message: str = "字段值不大于期望值", soft: bool = False):
        """ 断言字段值大于 """
        if field not in obj:
            error_msg = f"字段 '{field}' 不存在"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual > expected,
           f"{message} (字段:'{field}')",
            expected,
            actual,
            soft,
            expected_label="期望值大于的值",
            actual_label="实际值"
        )


    def assert_field_less(self, obj: dict, field: str, expected: Union[int, float],
                          message: str = "字段值不小于期望值", soft: bool = False):
        """ 断言字段值小于 """
        if field not in obj:
            error_msg = f"字段 '{field}' 不存在"
            if soft:
                self._soft_errers.append(error_msg)
                return False
            else:
                raise AssertionError(error_msg)

        actual = obj[field]
        return self._assert(
            actual < expected,
            f"{message} (字段: {field})",
            expected,
            actual,
            soft,
            expected_label="期望小于的值",
            actual_label="实际值"
        )

    def assert_response_status(self, response, expected_status: int = 200,
                               message: str = "HTTP状态码不匹配", soft: bool = False):
        """ 断言HTTP 状态码 """
        # return self.assert_equals(response.status_code, expected_status, message, soft)
        return self._assert(
            response.status_code == expected_status,
            message,
            expected_status,
            response.status_code,
            soft,
            expected_label="期望HTTP状态码",
            actual_label="实际HTTP状态码"
        )

    def assert_response_code(self, response, expected_code: int = 200,
                             message: str = "业务状态码不匹配", soft: bool = False):
        """ 断言业务状态码 """
        # data = response.json()
        # return self.assert_equals(data.get('code'), expected_code, message, soft)

        try:
            data = response.json()
            actual_code = data.get('code')
        except:
            actual_code = None

        return self._assert(
            actual_code == expected_code,
            message,
            expected_code,
            actual_code,
            soft,
            expected_label="期望业务状态码",
            actual_label="实际业务状态码"
        )

    def assert_response_massage(self, response, expected_message: str,
                                message: str = "响应消息不匹配", soft: bool = False):
        """ 断言响应消息 """
        #data = response.json()
        #return self.assert_equals(data.get('message'), expected_message, message, soft)
        try:
            data = response.json()
            actual_message = data.get('message')
        except:
            actual_message = None

        return self._assert(
            actual_message == expected_message,
            message,
            expected_message,
            actual_message,
            soft,
            expected_label="期望响应消息",
            actual_label="实际响应消息"
        )

    def assert_response_has_data(self, response, message: str = "响应缺少data字段", soft: bool = False):
        """ 断言响应包含 data """
        """
        data = response.json()
        return self._assert(
            'data' in data and data['data'] is not None,
            message,
            "data存在且不为空",
            data.get('data'),
            soft
        )
        """

        try:
            data = response.json()
            has_data = 'data' in data and data['data'] is not None
            actual_data = data.get('data')
        except:
            has_data = False
            actual_data = None

        return self._assert(
            has_data,
            message,
            "data存在且不为空",
            actual_data,
            soft,
            expected_label="期望条件",
            actual_label="实际data值"
        )


    def assert_response_data_not_empty(self, response,
                                       message: str = "响应data为空", soft: bool = False):
        """ 断言响应data不为空 """
        try:
            data = response.json().get('data')
            is_not_empty = bool(data)
        except:
            is_not_empty = False
            data = None

        return self._assert(
            is_not_empty,
            message,
            "非空数据",
            data,
            soft,
            expected_label="期望条件",
            actual_label="实际data值"
        )

    def get_soft_errors(self) -> List[str]:
        """ 获取所有软断言错误 """
        return self._soft_errers

    def has_soft_errors(self) -> bool:
        """ 是否有软断言错误 """
        return len(self._soft_errers) > 0

    def clear_soft_errors(self):
        """ 清除软断言错误 """
        self._soft_errers = []

    def flush_soft_assertions(self):
        """ 抛出所有软断言错误 """
        if self._soft_errers:
            errors = "\n".join(self._soft_errers)
            self._soft_errers = []
            raise AssertionError(f"软断言失败:\n{errors}")