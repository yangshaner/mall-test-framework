# testcases/admin/tets_order.py
import pytest
import allure
import time
from common.assertions import ApiAssertion, DBAssertion
from common.db.mysql_util import mysql


@allure.feature("订单管理")
class TestOrder:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("订单列表")
    def test_get_order_list(self, order_api):
        response = order_api.list(page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "获取订单列表失败")
        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, 'list', "缺少list")
        self.api_assert.assert_field_exist(data, "total", "缺少total")

    @allure.story("订单列表")
    @pytest.mark.parametrize("status, status_name", [
        (0, "待付款"),
        (1, "待发货"),
        (2, "已发货"),
        (3, "已完成"),
        (4, "已关闭")
    ])
    def test_get_order_list_by_status(self, order_api, status, status_name: str):
        """ 测试按状态过滤订单 """
        status_name = {0: "待付款", 1: "待发货", 2: "已发货", 3: "已完成", 4: "已关闭"}
        response = order_api.list(page_num=1, page_size=10, status=status)
        self.api_assert.assert_success(response, f"按状态{status}查询失败")
        data = response.json().get("data", {})
        for order in data.get('list', []):
            assert order.get("status") == status, f"订单的状态应为{status}:{status_name}"

    @allure.story("订单列表")
    def test_get_order_list_with_order_sn(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get('data', {}).get('list', [])
        if not orders:
            pytest.skip("没有可用订单")
        order_sn = orders[0].get('orderSn')

        response = order_api.list(page_num=1, page_size=1, order_sn=order_sn)
        result = self.api_assert.assert_success(response, "按订单号查询失败")
        data = result.get('data', {})
        for order in data.get('list', []):
            assert order.get('orderSn') == order_sn, "订单号不匹配"

    @allure.story("订单详情")
    def test_get_order_detail(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("没有可用订单")

        order_id = orders[0].get("id")
        response = order_api.detail(order_id)
        result = self.api_assert.assert_success(response, "获取订单详情失败")
        data = result.get("data", {})
        self.api_assert.assert_field_exist(data, "orderSn", "缺少订单编号")
        self.api_assert.assert_field_exist(data, "orderItemList", "缺少商品列表")
        self.api_assert.assert_field_exist(data, "status", "缺少订单状态")
        self.api_assert.assert_field_exist(data, "totalAmount", "缺少总金额")
        assert isinstance(data.get('orderItemList'), list), "商品列表应为数组"

    @allure.story("订单备注")
    def test_update_order_note(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1, status=0)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("没有待付款的订单")

        order_id = orders[0].get("id")
        note = f"测试备注_{int(time.time())}"
        response = order_api.update_note(order_id, note, 0)
        self.api_assert.assert_success(response, "备注订单失败")
        self.db_assert.assert_field_value('oms_order', 'note', note,
                                          'id = %s', (order_id,))

    @allure.story("批量发货")
    def test_delivery(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1, status=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("没有待发货的订单")
        order_id = orders[0].get("id")
        delivery_sn = f"SF{int(time.time())}"
        delivery_data = [{
            'orderId': order_id,
            "deliveryCompany": "顺丰快递",
            "deliverySn": delivery_sn
        }]
        response = order_api.delivery(delivery_data)
        self.api_assert.assert_success(response, "发货失败")
        self.db_assert.assert_field_value('oms_order', 'status', 2,
                                          'id = %s', (order_id,))
        self.db_assert.assert_field_value('oms_order', 'delivery_company', '顺丰快递',
                                          'id = %s', (order_id,))
        self.db_assert.assert_field_value('oms_order', 'delivery_sn', delivery_sn,
                                          'id = %s', (order_id,))

    @allure.story("修改收货人信息")
    def test_update_receiver_info(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=1)
        orders = list_resp.json().get("data", {}).get("list", [])
        if not orders:
            pytest.skip("没有可用的订单")

        order_id = orders[0].get("id")
        data = {
            "orderId": order_id,
            "receiverName": f"测试收货人_{int(time.time())}",
            "receiverPhone": "13800138000",
            "receiverProvince": "广东省",
            "receiverCity": "深圳市",
            "receiverRegion": "南山区",
            "receiverDetailAddress": "科技园路1号",
            "status": orders[0].get('status')
        }
        response = order_api.update_receiver_info(data)
        self.api_assert.assert_success(response, "修改收货人信息失败")

        self.db_assert.assert_field_value('oms_order', 'receiver_name', data['receiverName'],
                                          'id = %s', (order_id,))

    @allure.story("批量关闭订单")
    def test_batch_close_orders(self, order_api):
        list_resp = order_api.list(page_num=1, page_size=2, status=0)
        orders = list_resp.json().get("data", {}).get("list", [])
        if len(orders) < 1:
            pytest.skip("没有待付款的订单")

        order_ids = [o.get("id") for o in orders[:2]]
        response = order_api.close(order_ids, "测试关闭")
        self.api_assert.assert_success(response, "关闭订单失败")

        for oid in order_ids:
            self.db_assert.assert_field_value('oms_order', 'status', 4,
                                              'id = %s', (oid,))

    @allure.story("批量删除订单")
    def text_batch_delete_orders(self, order_api):
        # 获取已关闭或已完成的订单
        list_resp = order_api.list(page_num=1, page_size=2, status=4)
        orders = list_resp.json().get("data", {}).get("list", [])
        if len(orders) < 1:
            pytest.skip("没有可删除的订单")

        order_ids = [o.get("id") for o in orders[:2]]
        response = order_api.delete(order_ids)
        self.api_assert.assert_success(response, "删除订单失败")

        for oid in order_ids:
            self.db_assert.assert_field_value('oms_order', 'delete_status', 1,
                                              'id = %s', (oid,))
