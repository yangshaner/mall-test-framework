# api/member/attention_api.py
import allure
from typing import Dict

from common.client.member_client import MemberClient


class AttentionApi:
    """ 会员关注品牌管理API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取品牌关注列表")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        """ 分页查询当前用户品牌关注列表 """
        return self.client.get("/member/attention/list", params={
            "page_num": page_num,
            "page_size": page_size
        })

    @allure.step("获取品牌关注详情")
    def detail(self, brand_id: int) -> Dict:
        """ 根据品牌ID获取品牌关注详情 """
        return self.client.get("/member/attention/detail", params={
            "brandId": brand_id
        })

    @allure.step("添加品牌关注")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/member/attention/add", json=data)

    @allure.step("取消品牌关注")
    def delete(self, brand_id: int) -> Dict:
        return self.client.post("/member/attention/delete", params={
            "brandId": brand_id
        })

    @allure.step("清空品牌关注")
    def clear(self) -> Dict:
        return self.client.post("/member/attention/clear")
