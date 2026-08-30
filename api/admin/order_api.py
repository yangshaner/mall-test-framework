# api/admin/order_api.py

import allure
from typing import Optional, Dict, List

from common.client.admin_client import AdminClient

class OrderApi:

    def __init__(self):
        self.client = AdminClient()

    @allure.step("查询订单列表")
    def list(
        self,
        page_num: int = 1,
        page_size: int = 10,
        order_sn: Optional[str] = None,
        status: Optional[int] = None,
        order_type: Optional[int] = None,
        source_type: Optional[int] = None,
        receiver_keyword: Optional[str] = None
    ):
        # params = {"page_num": page_num, "page_size": page_size}
        params = {"pageNum": page_num, "pageSize": page_size}
        if order_sn:
            params["orderSn"] = order_sn
        if status is not None:
            params["status"] = status
        if order_type is not None:
            params["orderType"] = order_type
        if source_type is not None:
            params["sourceType"] = source_type
        if receiver_keyword:
            params["receiverKeyword"] = receiver_keyword
        return self.client.get("/order/list", params=params)

    @allure.step("获取订单详情")
    def detail(self, order_id: int):
        return self.client.get(f"/order/{order_id}")

    @allure.step("备注订单")
    def update_note(self, order_id: int, note: str, status: int):
        return self.client.post(
            "/order/update/note",
            params={"id": order_id, "note": note, "status": status},
        )

    @allure.step("修改收货人信息")
    def update_receiver_info(self, data: Dict):
        return self.client.post(
            "/order/update/receiverInfo",
            json=data
        )

    @allure.step("修改订单费用信息")
    def update_money_info(self, data: Dict):
        return self.client.post("/order/update/moneyInfo", json=data)

    @allure.step("批量发货")
    def delivery(self, data: List[Dict]):
        return self.client.post("/order/update/delivery", json=data)

    @allure.step("批量关闭订单")
    def close(self, ids: List[int], note: str = ""):
        return self.client.post("/order/update/close", params={"ids": ids, "note": note})

    @allure.step("批量删除订单")
    def delete(self, ids: List[int]):
        return self.client.post("/order/delete", params={"ids": ids})