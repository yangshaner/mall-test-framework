# api/member/address_api.py
import allure
from typing import Dict, Optional, List

from common.client.member_client import MemberClient


class AddressApi:
    """ 会员收货地址API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取所有收货地址")
    def list(self) -> Dict:
        return self.client.get("/member/address/list")

    @allure.step("获取收货地址详情")
    def detail(self, address_id: int) -> Dict:
        return self.client.get(f"/member/address/{address_id}")

    @allure.step("添加收货地址")
    def add(self, data: str) -> Dict:
        return self.client.post("/member/address", json=data)

    @allure.step("修改收货地址")
    def update(self, address_id: int, data: Dict) -> Dict:
        return self.client.post(f"/member/address/update/{address_id}", json=data)

    @allure.step("删除收货地址")
    def delete(self, address_id: int) -> Dict:
        return self.client.post(f"/member/address/delete/{address_id}")
