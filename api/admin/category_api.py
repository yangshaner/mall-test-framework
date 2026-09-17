# api/admin/category_api.py
import allure
from typing import List, Dict

from common.client.admin_client import AdminClient


class CategoryApi:

    def __init__(self):
        self.client = AdminClient()

    @allure.step("获取商品分类列表")
    def list(self, parent_id: int = 0, page_num: int = 1, page_size: int = 10):
        return self.client.get(
            f"/productCategory/list/{parent_id}",
            params={"pageNum": page_num, "pageSize": page_size},
        )

    @allure.step("获取商品分类详情")
    def detail(self, category_id: int):
        return self.client.get(f"/productCategory/{category_id}")

    @allure.step("获取素有一级分类以及子类")
    def list_with_children(self):
        return self.client.get("/productCategory/list/withChildren")

    @allure.step("创建商品分类")
    def create(self, data: Dict):
        return self.client.post("/productCategory/create", json=data)

    @allure.step("修改商品分类")
    def update(self, category_id: int, data: Dict):
        return self.client.post(f"/productCategory/update/{category_id}", json=data)

    @allure.step("修改显示状态")
    def update_show_status(self, ids: List[int], show_status: int):
        return self.client.post(
            "/productCategory/update/showStatus",
            params={"ids": ids, "showStatus": show_status}
        )

    @allure.step("修改导航栏显示状态")
    def update_nav_status(self, ids: List[int], nav_status: int):
        return self.client.post(
            "/productCategory/update/navStatus",
            params={"ids": ids, "navStatus": nav_status}
        )

    @allure.step("删除商品分类")
    def delete(self, category_id: int):
        return self.client.post(f"/productCategory/delete/{category_id}")
