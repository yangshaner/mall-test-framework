# api/mmeber/return_api.py
import allure
from typing import Dict

from common.client.member_client import MemberClient


class ReturnApi:

    def __init__(self):
        self.client = MemberClient()

    @allure.step("申请退货")
    def create(self, data: Dict):
        return self.client.post("/retuenApply/create", json=data)
