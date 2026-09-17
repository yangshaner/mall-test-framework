# testcases/admin/test_category.py
import pytest
import allure
import time

from common.assertions import ApiAssertion, DBAssertion
from common.utils.id_fetcher import IDFetcherWithAllure
from fixtures.admin_fixtures import data_generator
from common.db.mysql_util import mysql


@allure.feature("商品分类管理")
class TestCategory:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("分类树")
    def test_get_category_tree(self, category_api):
        response = category_api.list_with_children()
        self.api_assert.assert_success(response, "获取分类树失败")
        data = response.json().get('data', [])
        assert isinstance(data, list), "应返回列表"
        if data:
            first = data[0]
            self.api_assert.assert_field_exist(data[0], "id", "缺少id")
            self.api_assert.assert_field_exist(data[0], "name", "缺少name")
            self.api_assert.assert_field_exist(data[0], "children", "缺少children")
            assert isinstance(first.get('children'), list), "children应为列表"

    @allure.story("分类列表")
    def test_get_category_list(self, category_api):
        response = category_api.list(parent_id=0, page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "获取分页列表失败") # 没有data字段
        data = result.get('data', [])
        self.api_assert.assert_field_exist(data, 'list', "缺少list")
        self.api_assert.assert_field_exist(data, 'total', "缺少total")

    @allure.story("创建分类")
    def test_create_category(self, category_api, data_generator):
        category_name = f"测试分类_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 0,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        time.sleep(0.5)

        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module='category',
            search_value=category_name,
            page_size=10,
            max_pages=100,
            extra_params={'parent_id': 0}
        )

        if not category_id:
            category_id = IDFetcherWithAllure.get_id_by_module(
                api_instance=category_api,
                module='category',
                search_value=category_name,
                page_size=10,
                max_pages=100,
                exact_match=False,
                extra_params={'parent_id': 0}
            )

        assert category_id, f"未找到创建的分类：{category_name}"
        self.db_assert.assert_exists('pms_product_category', 'id = %s', (category_id,))
        self.db_assert.assert_field_value('pms_product_category', 'name', data['name'],
                                          'id = %s', (category_id,))
        category_api.delete(category_id)
        self.db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))

    @allure.story("更新分类")
    def test_update_category(self, category_api, data_generator):
        category_name = f"TEST_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 0,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        time.sleep(0.5)
        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"未找到创建的分类:{category_name}"

        update_data = {
            "parentId": 0,
            "name": f"已更新_{category_name}",
            "sort": 50,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.update(category_id, update_data)
        self.api_assert.assert_success(response, "更新分类失败")
        self.db_assert.assert_field_value('pms_product_category', 'name', update_data['name'],
                                          'id = %s', (category_id,))
        self.db_assert.assert_field_value('pms_product_category', 'sort', update_data['sort'],
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("分类详情")
    def test_get_category_detail(self, category_api, data_generator):
        category_name = f"测试分类_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 50,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"未找到创建的分类:{category_name}"

        response = category_api.detail(category_id)
        result = self.api_assert.assert_success(response, "获取分类详情失败")
        detail = result.get('data', {})
        assert detail.get('id') == category_id, "分类ID不匹配"
        assert detail.get('name') == category_name, "分类名称不匹配"
        self.api_assert.assert_field_exist(detail, 'level', "缺少level")
        self.api_assert.assert_field_exist(detail, 'sort', "缺少sort")

        category_api.delete(category_id)

    @allure.story("显示状态")
    @pytest.mark.parametrize("show_status", [0, 1])
    def test_update_show_status(self, category_api, data_generator, show_status):
        category_name = f"测试分类_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 0,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, f"未找到创建的分类:{category_name}"

        response = category_api.update_show_status([category_id], show_status)
        self.api_assert.assert_success(response, "修改显示状态失败")
        self.db_assert.assert_field_value('pms_product_category', 'show_status', show_status,
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("导航状态")
    @pytest.mark.parametrize("nav_status", [0, 1])
    def test_update_nav_status(self, category_api, data_generator, nav_status):
        category_name = f"测试分类_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 0,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, "未找到创建的分类"

        response = category_api.update_nav_status([category_id], nav_status)
        self.api_assert.assert_success(response, "修改导航状态失败")
        self.db_assert.assert_field_value('pms_product_category', 'nav_status', nav_status,
                                          'id = %s', (category_id,))

        category_api.delete(category_id)

    @allure.story("删除分类")
    def test_delete_category(self, category_api, data_generator):
        category_name = f"测试分类_{data_generator.random_string(4)}"
        data = {
            "parentId": 0,
            "name": category_name,
            "productUnit": "件",
            "sort": 0,
            "showStatus": 1,
            "navStatus": 0
        }
        response = category_api.create(data)
        self.api_assert.assert_success(response, "创建分类失败")

        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)
        assert category_id, "未找到创建的分类"

        self.db_assert.assert_exists('pms_product_category', 'id = %s', (category_id,))
        category_api.delete(category_id)
        self.api_assert.assert_success(response, "删除分类失败")

        self.db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))