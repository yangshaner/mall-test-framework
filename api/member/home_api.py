# api/member/home_api.py
import allure
from typing import Dict, Optional

from common.client.member_client import MemberClient


class HomeApi:

    def __init__(self):
        self.client = MemberClient()

    @allure.step("获取首页信息")
    def content(self) -> Dict:
        return self.client.get("/home/content")

    @allure.step("获取推荐商品")
    def recommend_product_list(self, page_num: int = 1, page_size: int = 4) -> Dict:
        return self.client.get("/home/recommandProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("获取商品推荐")
    def new_product_list(self, page_num: int = 1, page_size: int = 6) -> Dict:
        return self.client.get("/home/newProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("获取人气推荐")
    def hot_product_list(self, page_num: int = 1, page_size: int = 6) -> Dict:
        return self.client.get("/home/hotProductList", params={
            "pageNum": page_num,
            "pageSize": page_size
        })

    @allure.step("获取商品分类")
    def product_cate_list(self, parent_id: int) -> Dict:
        return self.client.get(f"/home/productCateList/{parent_id}")

    @allure.step("获取专题列表")
    def subject_list(self, cate_id: Optional[int] = None, page_num: int = 1, page_size: int = 4) -> Dict:
        params = {"pageNum": page_num, "pageSize": page_size}
        if cate_id:
            params["cateId"] = cate_id
        return self.client.get("/home/subjectList", params=params)
