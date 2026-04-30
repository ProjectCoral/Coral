"""
Coral 权限类型系统
支持 |、&、~ 运算符组合权限
"""

from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .perm_system import PermSystem

PermissionType = Union["Permission", "PermissionSet"]


class Permission:
    """
    权限类型，由 root 和 name 构成防止命名冲突
    例如: Permission("core", "admin") 表示 core.admin

    Usage:
        ADMIN = Permission("core", "admin")
        can_manage = ADMIN | Permission("core", "manage")
        can_delete = Permission("core", "read") & ~Permission("core", "banned")
    """

    def __init__(self, root: str, name: str, description: str = ""):
        self.root = root
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"{self.root}.{self.name}"

    def __repr__(self) -> str:
        return f"P({self.root!r}.{self.name!r}, desc={self.description!r})"

    def __or__(self, other: "Permission") -> "PermissionSet":
        return PermissionSet(PermissionSet.Operator.OR, self, other)

    def __and__(self, other: "Permission") -> "PermissionSet":
        return PermissionSet(PermissionSet.Operator.AND, self, other)

    def __invert__(self) -> "PermissionSet":
        return PermissionSet(PermissionSet.Operator.NOT, self, None)

    def __rand__(self, other: "Permission") -> "PermissionSet":
        return PermissionSet(PermissionSet.Operator.AND, other, self)

    def __hash__(self) -> int:
        return hash((self.root, self.name))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Permission):
            return self.root == other.root and self.name == other.name
        return False

    def check(self, perm_system: "PermSystem", user_id: str, group_id: str) -> bool:
        """
        检查权限（供 PermissionSet 递归调用）

        Args:
            perm_system: 权限系统实例
            user_id: 用户ID
            group_id: 群组ID

        Returns:
            是否拥有权限
        """
        return perm_system.check_single(self, user_id, group_id)


class PermissionSet:
    """
    权限集，通过运算符组合多个 Permission
    支持 | (OR)、& (AND)、~ (NOT) 运算符

    Usage:
        perms = Permission("a", "read") | Permission("b", "write")
        perms = Permission("a", "admin") & ~Permission("a", "banned")
    """

    class Operator:
        OR = "or"
        AND = "and"
        NOT = "not"

    def __init__(
        self, op: str, left: PermissionType, right: Optional[PermissionType] = None
    ):
        self.op = op
        self.left = left
        self.right = right

    def check(self, perm_system: "PermSystem", user_id: str, group_id: str) -> bool:
        """
        检查权限

        Args:
            perm_system: 权限系统实例
            user_id: 用户ID
            group_id: 群组ID

        Returns:
            是否拥有权限
        """
        if self.op == self.Operator.OR:
            return self.left.check(perm_system, user_id, group_id) or (
                self.right.check(perm_system, user_id, group_id)
                if self.right
                else False
            )
        elif self.op == self.Operator.AND:
            return self.left.check(perm_system, user_id, group_id) and (
                self.right.check(perm_system, user_id, group_id)
                if self.right
                else False
            )
        elif self.op == self.Operator.NOT:
            return not self.left.check(perm_system, user_id, group_id)
        return False

    def __or__(self, other: Permission) -> "PermissionSet":
        return PermissionSet(self.Operator.OR, self, other)

    def __and__(self, other: Permission) -> "PermissionSet":
        return PermissionSet(self.Operator.AND, self, other)

    def __invert__(self) -> "PermissionSet":
        return PermissionSet(self.Operator.NOT, self, None)

    def __repr__(self) -> str:
        if self.op == self.Operator.NOT:
            return f"(~{self.left!r})"
        elif self.op == self.Operator.AND:
            return f"({self.left!r} & {self.right!r})"
        else:
            return f"({self.left!r} | {self.right!r})"


def create_permission(root: str, name: str = "", desc: str = "") -> Permission:
    """
    快速创建权限（不自动注册，需手动调用 perm_system.register_perm）

    Args:
        root: 权限根名称（如 "core", "plugin"）
        name: 权限名称（如 "admin", "read"）
        desc: 权限描述

    Returns:
        Permission 对象
    """
    return Permission(root, name, desc)
