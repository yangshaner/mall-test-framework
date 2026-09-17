# testcases/member/test_coupon.py
import pytest
import allure

from common.assertions import ApiAssertion


@allure.feature("会员优惠券")
class TestMemberCoupon:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("优惠券列表")
    @pytest.mark.parametrize("use_status", [0, 1, 2])
    def test_coupon_list_by_status(self, member_coupon_api, use_status):
        response = member_coupon_api.list(use_status=use_status)
        self.api_assert.assert_page_response(
            response,
            message=f"获取优惠券列表失败(useStatus={use_status})",
            allow_empty_list=True
        )

    @allure.story("优惠券历史列表")
    def test_coupon_history_list(self, member_coupon_api):
        response = member_coupon_api.list_history()
        self.api_assert.assert_page_response(
            response,
            message="获取优惠券历史列表失败",
            allow_empty_list=True
        )

    @allure.story("商品相关优惠券")
    def test_coupon_list_by_product(self, member_coupon_api, test_product):
        response = member_coupon_api.list_by_product(test_product)
        self.api_assert.assert_list_response(
            response,
            message="获取商品相关优惠券失败"
        )

    @allure.story("购物车相关优惠券")
    @pytest.mark.parametrize("coupon_type", [0, 1])
    def test_coupon_list_by_cart(self, member_coupon_api, coupon_type):
        response = member_coupon_api.list_cart(coupon_type)
        self.api_assert.assert_list_response(
            response,
            message=f"获取购物车优惠券失败(type={coupon_type})"
        )

    @allure.story("领取优惠券")
    def test_receive_coupon(self, member_coupon_api, test_product):
        product_coupon_response = member_coupon_api.list_by_product(test_product)
        product_coupons = product_coupon_response.json().get("data", [])
        if not product_coupons:
            pytest.skip("当前商品没有可领取的优惠券")

        coupon_id = product_coupons[0].get("id")
        assert coupon_id, "优惠券数据缺少id"

        response = member_coupon_api.add(coupon_id)
        result = response.json()

        if result.get("code") != 200:
            message = result.get("message", "")
            if "已经" in message or "重复" in message or "exist" in message.lower():
                pytest.skip(f"优惠券已领取过：{message}")
        self.api_assert.assert_success(response, "领取优惠券失败", check_data=False)

    @allure.story("领取优惠券")
    def test_receive_nonexistent_coupon(self, member_coupon_api):
        response = member_coupon_api.add(999999999)
        result = response.json()
        assert result.get("code") != 200, "不存在的优惠券不应领取成功"