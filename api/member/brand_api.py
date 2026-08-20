# api/member/brand_api.py
import allure
from typing import Optional, Dict, List, Any

from common.client.member_client import MemberClient


class MemberBrandApi:
    """ 前台品牌管理API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取推荐品牌列表")
    def recommend_list(self, page_num: int, page_size: int = 6):
        """ 分页获取推荐品牌 """
        return self.client.get(
            "/brand/recommendList",
            params={"pageNum": page_num, "pageSize": page_size}
        )

    @allure.step("获取品牌详情")
    def detail(self, brand_id: int):
        """ 获取品牌详情 """
        return self.client.get(f"/brand/detail/{brand_id}")

    @allure.step("获取品牌相关商品")
    def product_list(self, brand_id: int, page_num: int = 1, page_size: int = 6):
        """ 分页获取品牌相关商品 """
        return self.client.get(
            "/brand/productList",
            params={"brandId": brand_id, "pageNum": page_num, "pageSize": page_size}
        )
