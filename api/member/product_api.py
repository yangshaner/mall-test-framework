# api/member/product_api.py
import allure
from typing import Dict, List, Optional

from common.client.member_client import MemberClient

class MemberProductApi:
    """ 前台商品API """

    def __init__(self, client):
        # self.client = MemberClient()
        self.client = client

    @allure.step("搜索商品")
    def search(self,
               keyword: Optional[str] = None,
               brand_id: Optional[int] = None,
               product_category_id: Optional[int] = None,
               page_num: int = 1,
               page_size: int = 10,
               sort: int = 0
        ) -> Dict:
        """ 综合搜索、筛选、排序 """
        params = {
            "pageNum": page_num,
            "pageSize": page_size,
            "sort": sort
        }
        if keyword:
            params["keyword"] = keyword
        if brand_id:
            params["brandId"] = brand_id
        if product_category_id:
            params["productCategoryId"] = product_category_id

        return self.client.get("/product/search", params=params)


    @allure.step("获取商品详情")
    def detail(self, product_id: int) -> Dict:
        return self.client.get(f"/product/detail/{product_id}")

    @allure.step("获取商品分类树")
    def category_tree(self) -> Dict:
        return self.client.get("/product/categoryTreeList")