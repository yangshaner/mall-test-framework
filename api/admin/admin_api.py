# api/admin/admin_api.py
import allure
from typing import Optional, Dict, Any, List

from common.client.admin_client import AdminClient


class AdminApi:
    """ 后台用户管理API """

    def __init__(self):
        self.client = AdminClient()

    @allure.step("用户登录")
    def login(self, username: str, password: str):
        """ 用户登录后返回token """
        return self.client.post("/admin/login", json={
            "username": username,
            "password": password
        })

    @allure.step("用户登出")
    def logout(self):
        """ 登出功能 """
        return self.client.post("/admin/logout")

    @allure.step("用户注册")
    def register(self, data: Dict):
        """ 用户注册 """
        return self.client.post("/admin/register", json=data)

    @allure.step("获取用户列表")
    def list(
            self,
            page_num: int = 1,
            page_size: int = 10,
            keyword: Optional[str] = None
    ):
        """ 根据用户名或姓名分页获取用户列表 """
        params = {"pageNum": page_num, "pageSize": page_size}
        if keyword:
            params["keyword"] = keyword
        return self.client.get("/admin/list", params=params)

    @allure.step("获取用户信息")
    def detail(self, admin_id: int):
        """ 获取指定用户信息 """
        return self.client.get(f"/admin/{admin_id}")

    @allure.step("获取当前用户信息")
    def get_current_user(self):
        """ 获取当前用户信息 """
        return self.client.get("/admin/info")

    @allure.step("修改用户信息")
    def update(self, admin_id: int, data: Dict):
        """ 修改指定用户信息 """
        return self.client.post(f"/admin/update/{admin_id}", json=data)

    @allure.step("修改用户状态")
    def update_status(self, admin_id: int, status: int):
        """ 修改账号状态 """
        return self.client.post(
            f"/admin/updateStatus/{admin_id}",
            params={"status": status}
        )

    @allure.step("修改用户密码")
    def update_password(self, data: Dict):
        """ 修改指定用户密码 """
        return self.client.post("/admin/updatePassword", json=data)

    @allure.step("给用户分配角色")
    def update_role(self, admin_id: int, role_ids: List[int]):
        """ 给用户分配角色 """
        return self.client.post(
            "/admin/role/update",
            params={"adminId": admin_id, "roleIds": role_ids}
        )

    @allure.step("获取用户角色")
    def get_role_list(self, admin_id: int):
        """ 获取指定用户角色 """
        return self.client.get(f"/admin/role/{admin_id}")

    @allure.step("删除用户")
    def delete(self, admin_id: int):
        """ 删除指定用户信息 """
        return self.client.post(f"/admin/delete/{admin_id}")

    @allure.step("刷新token")
    def refresh_token(self):
        """ 刷新token """
        return self.client.get("/admin/refreshToken")
