# api/member/coupon_api.py
import allure
from typing import Dict, Optional

from common.client.member_client import MemberClient


class MemberCouponApi:

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取会员优惠卷列表")
    def list(self, use_status: Optional[int] = None) -> Dict:
        params = {}
        if use_status is not None:
            params["useStatus"] = use_status
        return self.client.get("/member/coupon/list", params=params)

    @allure.step("获取会员优惠卷历史列表")
    def list_history(self, use_status: Optional[int] = None) -> Dict:
        params = {}
        if use_status is not None:
            params["useStatus"] = use_status
        return self.client.get("/member/coupon/listhHistory", params=params)

    @allure.step("领取优惠卷")
    def add(self, coupon_id: int) -> Dict:
        return self.client.post(f"/member/coupon/add/{coupon_id}")

    @allure.step("获取当前商品相关优惠卷")
    def list_by_product(self, product_id: int) -> Dict:
        return self.client.get(f"/member/coupon/listByProduct/{product_id}")

    @allure.step("获取购物车的相关优惠卷")
    def list_cart(self, type: int) -> Dict:
        """ 获取登录会员购物车的相关优惠卷 """
        return self.client.get(f"/member/coupon/list/cart/{type}")
