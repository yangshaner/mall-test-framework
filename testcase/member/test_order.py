# testcases/member/test_order.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("前台订单管理")
class TestMemberOrder:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("订单列表")
    @pytest.mark.parametrize("status", [-1, 0, 1, 2, 3, 4])
    def test_order_list_by_status(self, member_order_api, status):
        status_names = {-1: "全部", 0: "待付款", 1: "待发货", 2: "已发货", 3: "已完成", 4: "已关闭"}

        response = member_order_api.list(status=status)

        page_data = self.api_assert.assert_page_response(
            response,
            message=f"获取{status_names.get(status)}订单失败",
            allow_empty_list=True,
            soft=False
        )

        if status != -1:
            for order in page_data.get("list", []):
                assert order.get("status") == status, f"订单状态应为{status}"

    @allure.story("订单详情")
    def test_order_detail(self, member_order_api):
        response = member_order_api.list(status=-1, page_size=1)
        list_result = response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("没有可用的订单")

        order_id = orders[0].get("id")
        response = member_order_api.detail(order_id)
        result = self.api_assert.assert_success(response, "获取订单详情失败")

        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, "orderSn", "缺少订单编号")
        self.api_assert.assert_field_exist(data, "orderItemList", "缺少订单商品列表")
        self.api_assert.assert_field_exist(data, "status", "缺少订单状态")

    @allure.story("生成确认单")
    def test_generate_confirm_order(self, member_order_api, test_cart_item):
        response = member_order_api.generate_confirm_order([test_cart_item])
        result = self.api_assert.assert_success(response, "生成确认单失败")

        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, "cartPromotionItemList", "缺少购物车信息")
        self.api_assert.assert_field_exist(data, "memberReceiveAddressList", "缺少收货地址")
        self.api_assert.assert_field_exist(data, "calcAmount", "缺少金额计算")

    @allure.story("取消订单")
    def test_cancel_order(self, member_order_api):
        list_response = member_order_api.list(status=0, page_size=1)
        list_result = list_response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("没有待付款订单")

        order_id = orders[0].get("id")
        response = member_order_api.cancel_user_order(order_id)
        self.api_assert.assert_success(response, "取消订单失败")

    @allure.story("确认订单")
    def test_confirm_order(self, member_order_api):
        list_response = member_order_api.list(status=2, page_size=1)
        list_result = list_response.json()
        orders = list_result.get("data", {}).get("list", [])

        if not orders:
            pytest.skip("没有已发货订单")

        order_id = orders[0].get("id")
        response = member_order_api.confirm_receiver_order(order_id)
        self.api_assert.assert_success(response, "确认收货失败", check_data=False)