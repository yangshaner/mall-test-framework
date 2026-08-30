# api/admin/product_api.py

import allure
from typing import Optional, Dict, List

from common.client.admin_client import AdminClient

class ProductApi:

    def __init__(self):
        self.client = AdminClient()

    @allure.step("获取商品列表")
    def list(self,
             page_num: int = 1,
             page_size: int = 10,
             keyword: Optional[str] = None,
             product_sn: Optional[str] = None,
             publish_status: Optional[int] = None,
             verify_status: Optional[int] = None,
             product_category_id: Optional[int] = None,
             brand_id: Optional[int] = None
             ):
        params = {
            "pageNum": page_num,
            "pageSize": page_size
        }
        if keyword:
            params["keyword"] = keyword
        if product_sn:
            params["productSn"] = product_sn
        if publish_status is not None:
            params["publishStatus"] = publish_status
        if verify_status is not None:
            params["verifyStatus"] = verify_status
        if product_category_id:
            params["productCategoryId"] = product_category_id
        if brand_id:
            params["brandId"] = brand_id

        return self.client.get('/product/list', params=params)

    @allure.step("创建商品")
    def create(self, data: Dict):
        # return self.client.post('/product/create', data=data) # 这样会报400
        return self.client.post('/product/create', json=data)

    @allure.step("更新商品")
    def update(self, product_id: int, data: Dict):
        return self.client.post(f'/product/update/{product_id}', json=data)

    @allure.step("获取商品编辑信息")
    def get_update_info(self, product_id: int):
        return self.client.get(f'/product/updateInfo/{product_id}')

    @allure.step("模糊查询商品")
    def simple_list(self, keyword: str):
        """ 根据商品名称或货号模糊查询 """
        return self.client.get('/product/simpleList', params={"keyword": keyword})

    @allure.step("批量修改审查状态")
    def update_verify_status(self, ids: List[int], verify_status: int, detail: str = ""):
        return self.client.post(
            "/product/update/verifyStatus",
            params={"ids": ids, "verifyStatus": verify_status, "detail": detail}
        )

    @allure.step("批量上下架商品")
    def update_publish_status(self, ids: List[int], publish_status: int):
        return self.client.post(
            "/product/update/publishStatus",
            params={"ids": ids, "publishStatus": publish_status}
        )

    @allure.step("批量推荐商品")
    def update_recommend_status(self, ids: List[int], recommend_status: int):
        return self.client.post(
            "/product/update/recommendStatus",
            params={"ids": ids, "recommendStatus": recommend_status}
        )

    @allure.step("批量设为新品")
    def update_new_status(self, ids: List[int], new_status: int):
        return self.client.post(
            "/product/update/newStatus",
            params={"ids": ids, "newStatus": new_status}
        )

    @allure.step("批量修改删除状态")
    def update_delete_statue(self, ids: List[int], delete_status: int):
        return self.client.post(
            "/product/update/deleteStatus",
            params={"ids": ids, "deleteStatus": delete_status}
        )