# common/utils/role_manager.py

import yaml
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


logger = logging.getLogger(__name__)

class PermissionType(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    UPDATE = "update"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"


def _match_permission(permission: str, permissions:Set[str]) -> bool:
    if permission in permissions:
        return True

    if "*" in permissions:
        return True

    if ":" in permission:
        resource, _ = permission.split(":", 1)

        if f"{resource}:*" in permissions:
            return True

    return False


@dataclass
class RolePermission:
    role_id: int
    role_name: str
    permissions: Set[str] = field(default_factory=set)
    resource_ids: List[str] = field(default_factory=set)
    menu_ids: List[int] = field(default_factory=list)
    description: str = ""

    def has_permission(self, permission: str) -> bool:
        return _match_permission(permission, self.permissions)

    def has_resource(self, resource_id: int) -> bool:
        return resource_id in self.resource_ids

    def add_permission(self, permission: str):
        self.permissions.add(permission)

    def add_resource(self, resource_id: int):
        if resource_id not in self.resource_ids:
            self.resource_ids.append(resource_id)


@dataclass
class AdminUser:
    id: int
    username: str
    roles: List[int] = field(default_factory=list)
    status: int = -1
    permissions: Set[str] = field(default_factory=set)

    def has_role(self, role_id: int) -> bool:
        return role_id in self.roles

    def has_permission(self, permission: str) -> bool:
        return _match_permission(permission, self.permissions)


class RoleManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._roles: Dict[int, RolePermission] = {}
        self._users: Dict[int, AdminUser] = {}
        self._permission_mapping = {}

        self._load_role_config()
        self._load_user_config()

    def _load_role_config(self):
        config_path = Path(__file__).parent.parent.parent / "data" / "roles" / "admin_roles.yml"

        if config_path.exists():
            with open(config_path, "r", encoding='utf-8') as f:
                config = yaml.safe_load(f)

                for role_data in config.get("roles", []):
                    role = RolePermission(
                        role_id=role_data.get("id"),
                        role_name=role_data.get("name"),
                        description=role_data.get("description", "")
                    )
                    for perm in role_data.get("permissions", []):
                        role.add_permission(perm)
                    role.resource_ids = role_data.get("resources", [])
                    role.menu_ids = role_data.get("menus", [])
                    self._roles[role.role_id] = role

        if not self._roles:
            self._init_default_roles()

    def _init_default_roles(self):
        super_admin = RolePermission(
            role_id=1,
            role_name="超级管理员",
            description="拥有所有权限"
        )
        super_admin.permissions = {
            "admin:read", "admin:write","admin:delete", "admin:update",
            "product:read", "product:write", "product:delete", "product:update",
            "order:read", "order:write", "order:delete", "order:update",
            "user:read", "user:write", "user:delete", "user:update",
            "coupon:read", "coupon:write", "coupon:delete", "coupon:update",
            "brand:read", "brand:write", "brand:delete", "brand:update",
            "category:read", "category:write", "category:delete", "category:update",
            "flash:read", "flash:write", "flash:delete", "flash:update",
            "home:read", "home:write", "home:delete", "home:update",
            "file:upload", "file:delete"
        }
        self._roles[1] = super_admin

        product_admin = RolePermission(
            role_id=2,
            role_name="商品管理员",
            description="商品相关权限"
        )
        product_admin.permissions = {
            "product:read", "product:write", "product:update",
            "brand:read", "brand:write", "brand:update",
            "category:read", "category:write", "category:update"
        }
        self._roles[2] = product_admin

        order_admin = RolePermission(
            role_id=3,
            role_name="订单管理员",
            description="订单管理权限"
        )
        order_admin.permissions = {
            "order:read", "order:write", "order:update",
            "user:read"
        }
        self._roles[3] = order_admin

        read_only = RolePermission(
            role_id=4,
            role_name="只读用户",
            description="只有查看权限"
        )
        read_only.permissions = {
            "product:read", "order:read", "user:read",
            "brand:read", "category:read", "coupon:read"
        }
        self._roles[4] = read_only

    def _load_user_config(self):
        config_path = Path(__file__).parent.parent.parent / "data" / "roles" /"test_users.yml"

        if config_path.exists():
            with open(config_path, "r", encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for user_data in config.get("admin_users", []):
                user = AdminUser(
                    id=user_data.get("id"),
                    username=user_data.get("username"),
                    roles=user_data.get("roles", [])
                )
                for role_id in user.roles:
                    role = self._roles.get(role_id)
                    if role:
                        user.permissions.update(role.permissions)
                self._users[user.username] = user

    def get_role(self, role_id: int) -> Optional[RolePermission]:
        return self._roles.get(role_id)

    def get_user(self, username: str) -> Optional[AdminUser]:
        return self._users.get(username)

    def get_user_permission(self, username: str) -> Set[str]:
        user = self._users.get(username)
        if user:
            return user.permissions
        return set()

    def get_user_roles(self, username: str) -> List[int]:
        user = self._users.get(username)
        if user:
            return user.roles
        return []

    def has_permission(self, username: str, permission: str) -> bool:
        user = self._users.get(username)
        if user:
            return user.has_permission(permission)
        return False

    def has_any_permission(self, username: str, permissions: List[str]) -> bool:
        user = self._users.get(username)
        if user:
            return any(p in user.permissions for p in permissions)
        return False

    def has_all_permissions(self, username: str, permissions: List[str]) -> bool:
        user = self._users.get(username)
        if user:
            return all(p in user.permissions for p in permissions)
        return False

    def can_access_resource(self, username: str, resource_id: int) -> bool:
        user = self._users.get(username)
        if user:
            for role_id in user.roles:
                role = self._roles.get(role_id)
                if role and role.has_resource(resource_id):
                    return True
        return False

    def get_users_by_role(self, role_id: int) -> List[str]:
        result = []
        for username, user in self._users.items():
            if user.has_role(role_id):
                result.append(username)
        return result

    def add_user(self, username: str, roles: List[str], user_id: int = None):
        user = AdminUser(
            id=user_id or len(self._users) + 1,
            username=username,
            roles=roles
        )
        for role_id in roles:
            role = self._roles.get(role_id)
            if role:
                user.permissions.update(role.permissions)
        self._users[username] = user
        logger.info(f"User {username} added with roles {roles}")

    def remove_user(self, username: str):
        if username in self._users:
            del self._users[username]
            logger.info(f"User {username} removed")

    def add_role(self, role: RolePermission):
        self._roles[role.role_id] = role
        logger.info(f"Role {role.role_id} added")

    def get_all_roles(self) -> List[RolePermission]:
        return list(self._roles.values())

    def get_all_users(self) -> List[AdminUser]:
        return list(self._users.values())

role_manager = RoleManager()