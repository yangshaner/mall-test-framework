# testcases/member/test_scenario.py
import pytest
import allure
import time

from common.assertions import ApiAssertion
from common.db.mysql_util import mysql
from api.admin.order_api import OrderApi


@allure.feature("前台场景测试")
class TestMemberScenario:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    @allure.story("完整购物流程")
    def test_full_shopping_flow(
            self,
            member_product_api,
            cart_api,
            member_order_api,
            address_api,
            test_product
    ):
        with allure.step("1. 搜索商品"):
            response = member_product_api.search(keyword="手机")
            result = self.api_assert.assert_success(response, "搜索商品失败")
            products = result.get("data", {}).get("list", [])
            assert len(products) > 0, "没搜索到商品"

        with allure.step("2. 查看商品详情"):
            product_id = products[0].get('id')
            response = member_product_api.detail(product_id)
            result = self.api_assert.assert_success(response, "获取商品详情失败")
            detail = result.get("data", {})
            self.api_assert.assert_field_exist(detail, "product", "缺少商品信息")
            self.api_assert.assert_field_exist(detail, "skuStockList", "缺少SKU信息")

        with allure.step("3. 添加商品到购物车"):
            cart_data = {
                "productId": product_id,
                "productSkuId": detail.get("skuStockList", [{}])[0].get("id", 1),
                "quantity": 1,
                "price": detail.get("product", {}).get("price", 99.99)
            }
            response = cart_api.add(cart_data)
            self.api_assert.assert_success(response, "添加购物车失败")

        with allure.step("4. 获取购物车列表"):
            response = cart_api.list_promotion()
            result = self.api_assert.assert_success(response, "获取购物车失败")
            cart_items = result.get('data', [])
            assert len(cart_items) > 0, "购物车为空"
            cart_id = cart_items[0].get("id")

        with allure.step("5. 生成确认单"):
            response = member_order_api.generate_confirm_order([cart_id])
            result = self.api_assert.assert_success(response, "生成确认单失败")
            confirm_data = result.get("data", {})
            self.api_assert.assert_field_exist(confirm_data, "calcAmount", "缺少金额计算")

        with allure.step("6. 获取收货地址"):
            response = address_api.list()
            result = self.api_assert.assert_success(response, "获取收货地址失败")
            addresses = result.get('data', [])
            address_id = addresses[0].get("id") if addresses else None

            if not address_id:
                address_data = {
                    "name": "测试地址",
                    "phoneNumber": "13800138000",
                    "province": "广东省",
                    "city": "深圳市",
                    "region": "南山区",
                    "detailAddress": "科技园路1号",
                    "defaultStatus": 1
                }
                response = address_api.add(address_data)
                address_result = response.json()
                address_id = address_result.get("data", {}).get("id")

        with allure.step("7. 生成订单"):
            order_data = {
                "memberReceiveAddressId": address_id,
                "couponId": None,
                "useIntegration": 0,
                "payType": 0,
                "cartIds": [cart_id]
            }
            response = member_order_api.generate_order(order_data)
            result = self.api_assert.assert_success(response, "生成订单失败")
            order_result = result.get("data", {})
            order_id = order_result.get("orderItemList")[0].get("orderId")
            assert order_id, "订单ID为空"

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            assert detail_result.get("data", {}).get("id") == order_id, "订单详情不匹配"

        with allure.step("8. 支付成功回调"):
            response = member_order_api.pay_success(order_id, 1)
            self.api_assert.assert_success(response, "支付回调失败")

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get("data", {}).get("status")
            assert status == 1, f"订单状态应待发货（1），实际为{status}"


        with allure.step("9. 管理员后台发货"):
            order_api = OrderApi()
            delivery_data = [{
                "orderId": order_id,
                "deliveryCompany": "顺丰快递",
                "deliverySn": f"SF{int(time.time())}"
            }]
            response = order_api.delivery(delivery_data)
            self.api_assert.assert_success(response, "后台发货失败")

            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get('data', {}).get('status')
            assert status == 2, f"发货后订单状态应为已发货(2)，实际为：{status}"

            order_detail = detail_result.get("data", {})
            assert order_detail.get("deliveryCompany") == "顺丰快递", "物流公司未保存"
            assert order_detail.get("deliverySn") is not None, "物流单号未保存"

        with allure.step("10. 用户确认收货"):
            response = member_order_api.confirm_receiver_order(order_id)
            self.api_assert.assert_success(response, "确认收货失败", check_data=False)

        with allure.step("11. 验证订单完成"):
            detail_response = member_order_api.detail(order_id)
            detail_result = detail_response.json()
            status = detail_result.get("data", {}).get("status")
            assert status == 3, f"订单状态应为已完成（3），实际为{status}"

        with allure.step("12. 验证数据库订单状态"):
            sql = "SELECT status FROM oms_order WHERE id = %s"
            result = mysql.query(sql, (order_id,))

            allure.attach(
                f"查询结果: {result}\n"
                f"结果类型: {type(result)}\n"
                f"结果长度: {len(result) if result else 0}",
                name="数据库查询调试信息",
                attachment_type=allure.attachment_type.TEXT
            )

            assert result, f"订单未在数据库中存在: order_id={order_id}"
            db_status = result[0].get('status')
            assert db_status == 3, f"数据库订单状态应为3，实际为{db_status}"

        with allure.step("13. 清理购物车"):
            cart_api.clear()

    @allure.story("优惠券使用流程")
    def test_coupon_flow(
            self,
            member_coupon_api,
            cart_api,
            member_order_api,
            address_api,
            test_cart_item
    ):
        with allure.step("1. 获取可领取的优惠券"):
            response = member_coupon_api.list_by_product(test_cart_item)
            result = self.api_assert.assert_success(response, "获取商品优惠券失败")
            coupon = result.get("data", [])

            if not coupon:
                pytest.skip("没有可用的优惠券")

            coupon_id = coupon[0].get("id")

        with allure.step("2. 领取优惠券"):
            response = member_coupon_api.add(coupon_id)
            self.api_assert.assert_success(response, "领取优惠券失败")

        with allure.step("3. 获取我的优惠券"):
            response = member_coupon_api.list(use_status=0)
            result = self.api_assert.assert_success(response, "领取优惠券列表失败")
            my_coupons = result.get("data", [])
            found = any(c.get("id") == coupon_id for c in my_coupons)
            assert found, "领取的优惠券未在列表中"

        with allure.step("4. 使用优惠券下单"):
            confirm_response = member_order_api.generate_confirm_order([test_cart_item])
            confirm_result = confirm_response.json()
            address_id = confirm_result.get("data", {}).get("memberReceiverAddressList", [{}])[0].get("id")

            order_data = {
                "memberReceiverAddressId": address_id,
                "couponId": coupon_id,
                "useIntegration": 0,
                "payType": 1,
                "cartIds": [test_cart_item]
            }
            history_response = member_coupon_api.list_history(use_status=1)
            history_result = history_response.json()