# api/amdin/coupon_api.py
import allure
from typing import Optional, Dict

from common.client.admin_client import AdminClient


class CouponApi:

    def __init__(self):
        self.client = AdminClient()

    @allure.step("获取优惠券列表")
    def list(
            self,
            page_num: int = 1,
            page_size: int = 10,
            name: Optional[str] = None,
            type: Optional[int] = None
    ):
        params = {"pageNum": page_num, "pageSize": page_size}
        if name:
            params["name"] = name
        if type is not None:
            params["type"] = type
        return self.client.get("/coupon/list", params=params)

    @allure.step("获取优惠券详情")
    def detail(self, coupon_id: int):
        return self.client.get(f"/coupon/{coupon_id}")

    @allure.step("创建优惠券")
    def create(self, data: Dict):
        return self.client.post("/coupon/create", json=data)

    @allure.step("修改优惠券")
    def update(self, coupon_id: int, data: Dict):
        return self.client.post(f"/coupon/update/{coupon_id}", json=data)

    @allure.step("删除优惠券")
    def delete(self, coupon_id: int):
        return self.client.post(f"/coupon/update/{coupon_id}")
