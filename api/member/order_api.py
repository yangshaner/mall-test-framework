# api/member/order_api.py
import allure
from typing import Dict, List

from common.client.member_client import MemberClient


class MemberOrderApi:

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取订单列表")
    def list(self, status: int = 1, page_num: int = 1, page_size: int = 10) -> Dict:
        return self.client.get("/order/list", params={
            "status": status,
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("获取订单详情")
    def detail(self, order_id: int) -> Dict:
        return self.client.get(f"/order/detail/{order_id}")

    @allure.step("确认生成订单")
    def generate_confirm_order(self, cart_ids: List[int]) -> Dict:
        return self.client.post("/order/generateConfirmOrder", json=cart_ids)

    @allure.step("生成订单")
    def generate_order(self, data: Dict) -> Dict:
        return self.client.post("/order/generateOrder", json=data)

    @allure.step("用户取消订单")
    def cancel_user_order(self, order_id: int) -> Dict:
        return self.client.post("/order/cancelUserOrder", params={"orderId": order_id})

    @allure.step("用户确认收货")
    def confirm_receiver_order(self, order_id: int) -> Dict:
        return self.client.post("/order/confirmReceiveOrder", params={"orderId": order_id})

    @allure.step("用户删除订单")
    def delete_order(self, order_id: int) -> Dict:
        return self.client.post("/order/deleteOrder", params={"orderId": order_id})

    @allure.step("支付成功回调")
    def pay_success(self, order_id: int, pay_type: int) -> Dict:
        return self.client.post("/order/paySuccess", params={
            "orderId": order_id,
            "payType": pay_type
        })

    @allure.step("申请退货")
    def return_apply(self, data: Dict) -> Dict:
        return self.client.post("/returnApply/create", json=data)
