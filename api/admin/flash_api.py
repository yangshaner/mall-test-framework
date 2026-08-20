# api/admin/flash_api.py
import allure
from typing import Optional, Dict, List, Any

from common.client.admin_client import AdminClient


class FlashApi:
    """ 限时购活动管理API """

    def __init__(self):
        self.client = AdminClient()

    # ---------- 限时购活动 ----------

    @allure.step("获取限时购活动列表")
    def list(self, page_num: int = 1, page_size: int = 10, keyword: Optional[str] = None):
        """ 根据活动名称分页查询 """
        params = {"pageNum": page_num, "pageSize": page_size}
        if keyword:
            params["keyword"] = keyword
        return self.client.get("/flash/list", params=params)

    @allure.step("获取活动详情")
    def detail(self, flash_id: int):
        """ 获取活动详情 """
        return self.client.get(f"/flash/{flash_id}")

    @allure.step("创建限时购活动")
    def create(self, data: Dict):
        """ 添加活动 """
        return self.client.post("/flash/create", json=data)

    @allure.step("编辑活动")
    def update(self, flash_id: int, data: Dict):
        """ 编辑活动 """
        return self.client.post(f"/flash/update/{flash_id}", json=data)

    @allure.step("修改上下限状态")
    def update_status(self, flash_id: int, status: int):
        """ 修改上下限状态 """
        return self.client.post(
            f"/flash/update/status/{flash_id}",
            params={"status": status},
        )

    @allure.step("删除活动")
    def delete(self, flash_id: int):
        """ 删除活动 """
        return self.client.post(f"/flash/delete/{flash_id}")

    # --------------- 限时购场次 ---------------

    @allure.step("获取全部场次")
    def session_list(self):
        """ 获取全部场次 """
        return self.client.get("/flashSession/list")

    @allure.step("获取场次详情")
    def session_detail(self, session_id: int):
        """ 获取场次详情 """
        return self.client.get(f"/flashSession/{session_id}")

    @allure.step("创建场次")
    def session_create(self, data: Dict):
        """ 添加场次 """
        return self.client.post("/flashSession/create", json=data)

    @allure.step("修改场次")
    def session_update(self, session_id: int, data: Dict):
        """ 修改场次 """
        return self.client.post(f"/flashSession/update/{session_id}", json=data)

    @allure.step("修改场次启用状态")
    def session_update_status(self, session_id: int, status: int):
        """ 修改启用状态 """
        return self.client.post(
            f"/flashSession/update/status/{session_id}",
            params={"status": status}
        )

    @allure.step("删除场次")
    def session_delete(self, session_id: int):
        """ 删除场次 """
        return self.client.post(f"/flashSession/delete/{session_id}")

    # ---------------- 限时购商品关系 ------------------

    @allure.step("获取限时购商品关联列表")
    def relation_list(
            self,
            flash_promotion_id: int,
            flash_promotion_session_id: int,
            page_num: int = 1,
            page_size: int = 10
    ):
        """ 分页查询不同场次关联及商品信息 """
        return self.client.get(
            "/flashProductRelation/list",
            params={
                "flashPromotionId": flash_promotion_id,
                "flashPromotionSessionId": flash_promotion_session_id,
                "pageNum": page_num,
                "pageSize": page_size
            }
        )

    @allure.step("获取关联商品促销信息")
    def relation_detail(self, relation_id: int):
        """ 获取关联商品促销信息 """
        return self.client.get(f"/flashProductRelation/{relation_id}")

    @allure.step("批量选择商品添加关联")
    def relation_create(self, data: List[Dict]):
        """ 批量选择商品添加关联 """
        return self.client.post("/flashProductRelation/create", json=data)

    @allure.step("修改关联信息")
    def relation_update(self, relation_id: int, data: Dict):
        """ 修改关联信息 """
        return self.client.post(f"/flashProductRelation/update/{relation_id}", json=data)

    @allure.step("删除关联")
    def relation_delete(self, relation_id: int):
        """ 删除关联 """
        return self.client.post(f"/flashProductRelation/delete/{relation_id}")
