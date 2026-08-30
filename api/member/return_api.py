# api/mmeber/return_api.py
import allure
from typing import Dict

from common.client.member_client import MemberClient


class ReturnApi:
    """ 退货申请管理API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("申请退货")
    def create(self, data: Dict):
        """ 申请退货 """
        return self.client.post("/retuenApply/create", json=data)
