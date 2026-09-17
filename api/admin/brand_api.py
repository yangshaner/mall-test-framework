# api/admin/brand_api.py

import allure
from typing import Optional, Dict, List

from common.client.admin_client import AdminClient

class BrandApi():

    def __init__(self):
        self.client = AdminClient()

    @allure.step("获取品牌列表")
    def list(
        self,
        page_num: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        show_status: Optional[int] = None
    ):
        params = {"pageNum": page_num, page_size: page_size}
        if keyword:
            params["keyword"] = keyword
        if show_status is not None:
            params["showStatus"] = show_status
        return self.client.get('/brand/list', params=params)

    @allure.step("获取全部品牌列表")
    def list_all(self):
        return self.client.get('/brand/listAll')

    @allure.step("获取品牌详情")
    def detail(self, brand_id: int):
        return self.client.get(f'/brand/{brand_id}')

    @allure.step("创建品牌")
    def create(self, data: Dict):
        return self.client.post('/brand/create', json=data)

    @allure.step("更新品牌")
    def update(self, brand_id: int, data: Dict):
        return self.client.post(f'/brand/update/{brand_id}', json=data)

    @allure.step("删除品牌")
    def delete(self, brand_id: int):
        return self.client.get(f'/brand/delete/{brand_id}')

    @allure.step("批量删除品牌")
    def delete_batch(self, ids: List[int]):
        return self.client.post('/brand/delete/batch', params={"ids": ids})

    @allure.step("批量更新显示状态")
    def update_show_status(self, ids: List[int], show_status: int):
        return self.client.post(
            '/brand/update/showStatus',
            params={"ids": ids, "showStatus": show_status}
        )

    @allure.step("批量更新厂家制造商状态")
    def update_factory_status(self, ids: List[int], factory_status: int):
        return self.client.post(
            '/brand/update/factoryStatus',
            params={"ids": ids, "factoryStatus": factory_status}
        )