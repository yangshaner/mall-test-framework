# testcases/member/test_cart.py
import pytest
import allure

from common.assertions import ApiAssertion, SoftAssertion


@allure.feature("购物车管理")
class TestCart:
    """ 购物车测试 """

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("购物车列表")
    def test_cart_list(self, cart_api):
        """ 测试购物车列表 """
        response = cart_api.list()
        print("获取购物车的业务状态码", response.json())
        result = self.api_assert.assert_success(response, "获取购物车列表失败")

        data = result.get("data", [])
        print(f"添加购物车返回的业务data：{data}")
        assert isinstance(data, list), "购物车数据应为列表"

    @allure.story("添加购物车")
    def test_add_to_cart(self, cart_api, test_product):
        """ 测试添加商品到购物车 """
        data = {
            "productId": test_product,
            "productSkuId": 1,
            "quantity": 1,
            "price": 99.99
        }
        response = cart_api.add(data)
        self.api_assert.assert_success(response, "添加购物车失败")

        # 验证购物车列表
        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        found = any(item.get("productId") == test_product for item in items)
        assert found, "商品未添加到购物车"

    @allure.story("修改购物车数量")
    def test_update_quantity(self, cart_api, test_cart_item):
        """ 测试修改购物车商品数量 """
        response = cart_api.update_quantity(test_cart_item, 3)
        self.api_assert.assert_success(response, "修改数量失败")

        # 验证数量已修改
        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        item = next((i for i in items if i.get("id") == test_cart_item), None)
        if item:
            assert item.get("quantity") == 3, "数量未更新"

    @allure.story("删除购物车商品")
    def test_delete_cart_item(self, cart_api, test_cart_item):
        """ 测试删除购物车商品 """
        response = cart_api.delete([test_cart_item])
        self.api_assert.assert_success(response, "删除购物车商品失败")

        # 验证已删除
        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        found = any(item.get("id") == test_cart_item for item in items)
        assert not found, "购物车商品未删除"

    @allure.story("清空购物车")
    def test_clear_cart(self, cart_api):
        """ 测试清空购物车 """
        response = cart_api.clear()
        print("清空购物车的response：", response)
        self.api_assert.assert_success(response, "清空购物车失败")

        # 验证已清空
        list_response = cart_api.list()
        list_result = list_response.json()
        items = list_result.get("data", [])
        assert len(items) == 0, "购物车未清空"

    @allure.story("购物车促销信息")
    def test_cart_promotion(self, cart_api, test_cart_item):
        """ 测试获取购物车促销信息 """
        response = cart_api.list_promotion()
        result = self.api_assert.assert_success(response, "获取促销信息失败")

        data = result.get("data", [])
        assert isinstance(data, list), "促销信息应为列表"
        if data:
            item = data[0]
            self.api_assert.assert_field_exist(item, "promotionMessage", "缺少促销信息")
