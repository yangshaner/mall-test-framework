# common/assertion/api_assertion.py

import allure
from typing import Optional, List

from .base_assertion import BaseAssertion

class ApiAssertion(BaseAssertion):

    @allure.step("断言API请求成功")
    def assert_success(self, response, message: str = "API请求失败",
                       check_response_code: bool = True, check_data: bool = True,
                       soft: bool = False):
        self.assert_response_status(response, 200, f"{message}: HTTP状态码错误", soft)

        if check_response_code:
            self.assert_response_code(response, 200, f"{message}: 业务状态码错误", soft)

        if check_data:
            self.assert_response_has_data(response, f"{message}: 缺少data字段", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return response.json()

    @allure.step("断言API请求失败")
    def assert_fail(self, response,
                    expected_code: Optional[int] = None,
                    expected_message: Optional[str] = None,
                    message: str = "API请求失败",
                    soft: bool = False):
        if response.status_code >= 200:
            self.assert_response_status(response, response.status_code,
                                        f"{message}: HTTP状态码", soft)
        else:
            data = response.json()
            if expected_code is not None:
                self.assert_not_equals(data.get("code"), 200,
                                       f"{message}: 业务状态码应为非200", soft)
            if expected_message is not None:
                self.assert_equals(data.get("code"), expected_code,
                                   f"{message}: 业务状态不匹配", soft)
            if expected_message:
                self.assert_response_massage(response, expected_message,
                                             f"{message}: 响应消息不匹配", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return response.json()

    @allure.step("断言分页响应")
    def assert_page_response(self, response,
                             expected_total:Optional[int] = None,
                             expected_page_size:Optional[int] = None,
                             min_items: int = 0,
                             allow_empty_list: bool = True,
                             message: str = "分页响应异常",
                             soft: bool = False):
        data = self.assert_success(response, message, soft=soft)
        page_data = data.get('data', {})

        self.assert_field_exist(page_data, ['pageNum', 'pageSize', 'totalPage', 'total'],
                                f"{message}: 缺少分页字段", soft)

        list_data = page_data.get('list')
        if list_data is None:
            total = data.get('total', 0)
            if total == 0 and allow_empty_list:
                list_data = []
            else:
                self.assert_field_exist(page_data, ['list'], f"{message}: 缺少list字段", soft)
                list_data = []

        self.assert_type(list_data, list,
                         f"{message}: list应为数组", soft)

        if min_items > 0:
            self.assert_greater_equal(len(list_data), min_items,
                                      f"{message}: 列表长度小于 {min_items}", soft)

        if expected_total is not None:
            self.assert_equals(page_data.get('total'), expected_total,
                               f"{message}: 总数不匹配", soft)

        if expected_page_size is not None:
            self.assert_equals(page_data.get('pageSize'), expected_page_size,
                               f"{message}: 每页大小不匹配", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return page_data

    def assert_list_response(self, response,
                             expected_count:Optional[int] = None,
                             min_count: int = 0,
                             message: str = "列表响应异常",
                             soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        list_data = data.get('data', [])
        self.assert_type(list_data, list, f"{message}: data应为数组", soft)

        if expected_count is not None:
            self.assert_equals(len(list_data), expected_count,
                               f"{message}: 列表数量不匹配", soft)
        elif min_count > 0:
            self.assert_greater_equal(len(list_data), min_count,
                                      f"{message}: 列表长度小于 {min_count}", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return list_data

    @allure.step("断言单个对象响应")
    def assert_object_response(self, response,
                               required_fields: Optional[List[str]] = None,
                               message: str = "对象响应异常",
                               soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        obj_data = data.get('data', {})
        self.assert_true(bool(obj_data), f"{message}: data为空", soft)

        if required_fields:
            self.assert_fields_exist(obj_data, required_fields, f"{message}: 缺少必要字段", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return obj_data

    @allure.step("断言创建成功")
    def assert_create_success(self, response,
                              expected_id_field: str = "id",
                              message: str = "创建失败",
                              soft: bool = False):
        data = self.assert_success(response, message, soft=soft)

        obj_data = data.get('data', {})
        self.assert_fields_exist(obj_data, [expected_id_field],
                                 f"{message}: 缺少ID字段", soft)
        self.assert_is_not_none(obj_data.get(expected_id_field),
                                f"{message}: ID为空", soft)

        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return obj_data.get(expected_id_field)

    @allure.step("断言删除成功")
    def assert_delete_success(self, response,
                              message: str = "删除失败",
                              soft: bool = False):
        return self.assert_success(response, message, False, soft)

    @allure.step("断言更新成功")
    def assert_update_success(self, response,
                              message: str = "更新失败",
                              soft: bool = False):
        return self.assert_success(response, message, False, soft)