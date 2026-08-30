# common/assertion/api_assertion.py

import allure
from typing import Optional, List

from .base_assertion import BaseAssertion

class ApiAssertion(BaseAssertion):
    """ API断言响应 """

    @allure.step("断言API请求成功")
    def assert_success(self, response, message: str = "API请求失败",
                       check_response_code: bool = True, check_data: bool = True,
                       soft: bool = False):
        """
        断言请求成功
        - HTTP状态码 200
        - 业务状态码 200
        - 包含data字段（可选）
        """

        # HTTP 状态码
        self.assert_response_status(response, 200, f"{message}: HTTP状态码错误", soft)

        # 业务状态码
        if check_response_code:
            self.assert_response_code(response, 200, f"{message}: 业务状态码错误", soft)

        # data字段
        if check_data:
            self.assert_response_has_data(response, f"{message}: 缺少data字段", soft)

        # 如果有软断言错误，抛出 (？)
        if not soft and self.has_soft_errors():
            self.flush_soft_assertions()

        return response.json()

    @allure.step("断言API请求失败")
    def assert_fail(self, response,
                    expected_code: Optional[int] = None,
                    expected_message: Optional[str] = None,
                    message: str = "API请求失败",
                    soft: bool = False):
        """ 断言API请求失败 """
        # HTTP状态码可能是200但有业务错误，也可能是4xx/5xx
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
        """ 断言分页响应 """
        data = self.assert_success(response, message, soft=soft)
        page_data = data.get('data', {})

        # 验证分页基本字段
        self.assert_field_exist(page_data, ['pageNum', 'pageSize', 'totalPage', 'total'],
                                f"{message}: 缺少分页字段", soft)

        # 验证 list 字段（可能不存在或为空数组）
        list_data = page_data.get('list')
        if list_data is None:
            # 如果list不存在，检查total是否为0
            total = data.get('total', 0)
            if total == 0 and allow_empty_list:
                # 空列表是合理的
                list_data = []
            else:
                self.assert_field_exist(page_data, ['list'], f"{message}: 缺少list字段", soft)
                list_data = []

        # 验证列表是数组
        self.assert_type(list_data, list,
                         f"{message}: list应为数组", soft)

        # 验证列表长度
        if min_items > 0:
            self.assert_greater_equal(len(list_data), min_items,
                                      f"{message}: 列表长度小于 {min_items}", soft)

        # 验证总数
        if expected_total is not None:
            self.assert_equals(page_data.get('total'), expected_total,
                               f"{message}: 总数不匹配", soft)

        # 验证每页大小
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
        """ 断言列表响应 """
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
        """ 断言单个对象响应 """
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
        """ 断言创建操作成功 """
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
        """ 断言删除操作成功 """
        return self.assert_success(response, message, False, soft)

    @allure.step("断言更新成功")
    def assert_update_success(self, response,
                              message: str = "更新失败",
                              soft: bool = False):
        """ 断言更新操作成功 """
        return self.assert_success(response, message, False, soft)