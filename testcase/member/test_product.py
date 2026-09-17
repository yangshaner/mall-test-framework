# testcases/member/test_product.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("前台商品管理")
class TestMemberProduct:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("商品搜索")
    def test_search_product_list(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message="搜索商品列表失败",
            allow_empty_list=True
        )

    @allure.story("商品搜索")
    def test_search_product_by_keyword(self, member_product_api, test_product):
        detail_response = member_product_api.detail(test_product)
        detail_result = detail_response.json()
        product_name = detail_result.get("data", {}).get("name")
        if not product_name:
            pytest.skip("无法获取测试商品名称")

        response = member_product_api.search(keyword=product_name, page_num=1, page_size=10)
        page_data = self.api_assert.assert_page_response(
            response,
            message="按关键字搜索商品失败",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert product_list, "按名称搜索未找到已上架的测试商品"
        assert any(item.get("id") == test_product for item in product_list), \
            "搜索结果中不包含测试商品"

    @allure.story("商品搜索")
    def test_search_product_pagination(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=1)
        page_data = self.api_assert.assert_page_response(
            response,
            expected_page_size=1,
            message="搜索商品分页失败",
            allow_empty_list=True
        )

        product_list = page_data.get("list", [])
        assert len(product_list) <= 1, "pageSize=1 时每页最多返回1条数据"

    @allure.story("商品搜索")
    @pytest.mark.parametrize("sort", [0, 1])
    def test_search_product_with_sort(self, member_product_api, sort):
        response = member_product_api.search(sort=sort, page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message=f"排序搜索(sort={sort})失败",
            allow_empty_list=True
        )

    @allure.story("商品搜索")
    def test_search_product_by_brand(self, member_product_api, test_brand):
        response = member_product_api.search(brand_id=test_brand, page_num=1, page_size=10)
        self.api_assert.assert_page_response(
            response,
            message="按品牌筛选商品失败",
            allow_empty_list=True
        )

    @allure.story("商品详情")
    def test_product_detail(self, member_product_api, test_product):
        response = member_product_api.detail(test_product)
        data = self.api_assert.assert_object_response(
            response,
            required_fields=["id", "name"],
            message="获取商品详情失败"
        )

        assert data.get("id") == test_product, "商品详情ID与请求ID不一致"

    @allure.story("商品详情")
    def test_product_detail_not_exist(self, member_product_api):
        response = member_product_api.detail(999999999)
        result = response.json()
        assert result.get("code") != 200 or not result.get("data"), \
            "不存在的商品不应返回有效详情数据"

    @allure.story("商品分类树")
    def test_category_tree(self, member_product_api):
        response = member_product_api.category_tree()
        self.api_assert.assert_list_response(
            response,
            message="获取商品分类树失败"
        )