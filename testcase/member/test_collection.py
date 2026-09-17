# testcases/member/test_collection.py
import allure

from common.assertions import ApiAssertion


@allure.feature("会员商品收藏")
class TestCollection:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("收藏列表")
    def test_collection_list(self, collection_api, test_collection):
        response = collection_api.list(page_num=1, page_size=10)
        page_data = self.api_assert.assert_page_response(
            response,
            message="获取收藏列表失败",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert len(product_list) > 0, "已创建收藏但收藏列表为空"

    @allure.story("添加收藏")
    def test_add_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"测试商品_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        try:
            response = collection_api.add(data)
            self.api_assert.assert_success(response, "添加商品收藏失败", check_data=False)

            list_response = collection_api.list(page_num=1, page_size=50)
            list_result = list_response.json()
            items = list_result.get("data", {}).get("list", [])
            assert any(item.get("productId") == test_product for item in items), \
                "商品收藏后未出现在收藏列表中"
        finally:
            collection_api.delete(test_product)

    @allure.story("收藏详情")
    def test_collection_detail(self, collection_api, test_product):
        response = collection_api.detail(test_product)
        self.api_assert.assert_success(response, "获取收藏商品详情失败", check_data=False)

    @allure.story("删除收藏")
    def test_delete_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"测试商品_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        add_response = collection_api.add(data)
        self.api_assert.assert_success(add_response, "前置添加收藏失败", check_data=False)

        response = collection_api.delete(test_product)
        self.api_assert.assert_success(response, "删除商品收藏失败", check_data=False)

        list_response = collection_api.list(page_num=1, page_size=50)
        list_result = list_response.json()
        items = list_result.get("data", {}).get("list", [])
        assert not any(item.get("productId") == test_product for item in items), \
            "商品收藏未被删除"

    @allure.story("清空收藏")
    def test_clear_collection(self, collection_api, test_product, data_generator):
        data = {
            "productId": test_product,
            "productName": f"测试商品_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        collection_api.add(data)

        response = collection_api.clear()
        self.api_assert.assert_success(response, "清空商品收藏失败", check_data=False)

        list_response = collection_api.list(page_num=1, page_size=50)
        list_result = list_response.json()
        items = list_result.get("data", {}).get("list", [])
        assert len(items) == 0, "商品收藏列表未清空"