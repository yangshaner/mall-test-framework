# api/member/read_history_api.py
import allure
from typing import Dict, List

from common.client.member_client import MemberClient


class ReadHistoryApi:

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取浏览记录")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        return self.client.get("/member/readHistory/list", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("创建浏览记录")
    def create(self, data: Dict) -> Dict:
        return self.client.post("/member/readHistory/create", json=data)

    @allure.step("删除浏览记录")
    def delete(self, ids: List[str]) -> Dict:
        return self.client.post("/member/readHistory/delete", params={"ids": ids})

    @allure.step("清空浏览记录")
    def clear(self) -> Dict:
        return self.client.post("/member/readHistory/clear")
    