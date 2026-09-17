# api/admin/admin_api.py
import allure
from typing import Optional, Dict, List

from common.client.admin_client import AdminClient


class AdminApi:

    def __init__(self):
        self.client = AdminClient()

    @allure.step("用户登录")
    def login(self, username: str, password: str):
        return self.client.post("/admin/login", json={
            "username": username,
            "password": password
        })

    @allure.step("用户登出")
    def logout(self):
        return self.client.post("/admin/logout")

    @allure.step("用户注册")
    def register(self, data: Dict):
        return self.client.post("/admin/register", json=data)

    @allure.step("获取用户列表")
    def list(
            self,
            page_num: int = 1,
            page_size: int = 10,
            keyword: Optional[str] = None
    ):
        params = {"pageNum": page_num, "pageSize": page_size}
        if keyword:
            params["keyword"] = keyword
        return self.client.get("/admin/list", params=params)

    @allure.step("获取用户信息")
    def detail(self, admin_id: int):
        return self.client.get(f"/admin/{admin_id}")

    @allure.step("获取当前用户信息")
    def get_current_user(self):
        return self.client.get("/admin/info")

    @allure.step("修改用户信息")
    def update(self, admin_id: int, data: Dict):
        return self.client.post(f"/admin/update/{admin_id}", json=data)

    @allure.step("修改用户状态")
    def update_status(self, admin_id: int, status: int):
        return self.client.post(
            f"/admin/updateStatus/{admin_id}",
            params={"status": status}
        )

    @allure.step("修改用户密码")
    def update_password(self, data: Dict):
        return self.client.post("/admin/updatePassword", json=data)

    @allure.step("给用户分配角色")
    def update_role(self, admin_id: int, role_ids: List[int]):
        return self.client.post(
            "/admin/role/update",
            params={"adminId": admin_id, "roleIds": role_ids}
        )

    @allure.step("获取用户角色")
    def get_role_list(self, admin_id: int):
        return self.client.get(f"/admin/role/{admin_id}")

    @allure.step("删除用户")
    def delete(self, admin_id: int):
        return self.client.post(f"/admin/delete/{admin_id}")

    @allure.step("刷新token")
    def refresh_token(self):
        return self.client.get("/admin/refreshToken")
