# api/member/collection_api.py
import allure
from typing import Dict, Optional, List

from common.client.member_client import MemberClient


class CollectionApi:
    """ 会员收藏管理API """

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取商品收藏列表")
    def list(self, page_num: int = 1, page_size: int = 5) -> Dict:
        """ 显示当前用户商品收藏列表 """
        return self.client.get("/member/productCollection/list", params={
            "page_num": page_num,
            "page_size": page_size
        })

    @allure.step("获取商品收藏详情")
    def detail(self, product_id: int) -> Dict:
        """ 显示商品收藏详情 """
        return self.client.get("/member/product/detail", params={
            "productId": product_id
        })

    @allure.step("添加商品收藏")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/member/productCollection/add", json=data)

    @allure.step("删除商品收藏")
    def delete(self, product_id: int) -> Dict:
        return self.client.post("/member/productCollection/delete", params={
            "productId": product_id
        })

    @allure.step("清空商品收藏")
    def clear(self) -> Dict:
        """ 清空当前用户商品收藏列表 """
        return self.client.post("/member/productCollection/clear")
