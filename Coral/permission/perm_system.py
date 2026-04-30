"""
Coral 权限系统
"""

import os
import json
import logging
from functools import lru_cache
from typing import Optional, Union, List, Dict, Set, Tuple, TYPE_CHECKING
from ..protocol import CommandEvent
from .permission import Permission, PermissionType

if TYPE_CHECKING:
    from .permission import Permission

logger = logging.getLogger(__name__)


class PermSystem:
    """权限系统"""

    def __init__(self, config):
        """
        初始化权限系统

        Args:
            config: 配置实例
        """
        self.config = config
        self.perm_file = self.config.get("perm_file", "./coral.perms")

        # 权限数据存储（内部全部使用 Permission 对象）
        self.registered_perms: Dict[Permission, str] = {}  # Permission -> 描述
        self.user_perms: Dict[str, List[Dict[str, Permission]]] = (
            {}
        )  # 用户ID -> [{perm: Permission, group: str}, ...]
        self.group_perms: Dict[str, List[Permission]] = (
            {}
        )  # 群组ID -> [Permission, ...]

        # ========== 索引结构（优化运行时开销） ==========
        # 用户全局权限索引: user_id -> Set[Permission]
        self._user_global_perms: Dict[str, Set[Permission]] = {}
        # 用户群组权限索引: user_id -> group_id -> Set[Permission]
        self._user_perms_by_group: Dict[str, Dict[str, Set[Permission]]] = {}
        # 群组权限索引: group_id -> Set[Permission]
        self._group_perms_index: Dict[str, Set[Permission]] = {}
        # ALL 全局权限标记
        self._all_perm = Permission("ALL", "", "所有权限")

        self.load_permissions()

        # 注册基础权限
        self.register_perm(self._all_perm)
        self.register_perm(Permission("permission_system", "", "权限系统基础权限"))

    def _rebuild_indexes(self):
        """重建所有索引结构"""
        # 重置索引
        self._user_global_perms.clear()
        self._user_perms_by_group.clear()
        self._group_perms_index.clear()

        # 重建用户权限索引
        for user_id, perm_entries in self.user_perms.items():
            global_set = set()
            by_group: Dict[str, Set[Permission]] = {}

            for entry in perm_entries:
                perm = entry["perm"]
                group = entry["group"]

                if group == "ALL":
                    global_set.add(perm)
                else:
                    if group not in by_group:
                        by_group[group] = set()
                    by_group[group].add(perm)

            if global_set:
                self._user_global_perms[user_id] = global_set
            if by_group:
                self._user_perms_by_group[user_id] = by_group

        # 重建群组权限索引
        for group_id, perms in self.group_perms.items():
            if perms:
                self._group_perms_index[group_id] = set(perms)

    def _invalidate_cache(self):
        """使缓存失效（权限变更时调用）"""
        self._check_permission.cache_clear()

    def _parse_permission(self, perm_str: str) -> Permission:
        """解析权限字符串为 Permission 对象

        Args:
            perm_str: 权限字符串，格式如 "core.admin" 或 "plugin.load"

        Returns:
            Permission 对象
        """
        if "." in perm_str:
            root, name = perm_str.split(".", 1)
        else:
            root, name = perm_str, ""
        return Permission(root, name)

    def _serialize_permission(self, perm: Permission) -> str:
        """将 Permission 序列化为字符串（用于 JSON 存储）

        Args:
            perm: Permission 对象

        Returns:
            格式为 "root:name" 的字符串
        """
        return f"{perm.root}:{perm.name}"

    def _deserialize_permission(self, perm_str: str) -> Permission:
        """将字符串反序列化为 Permission 对象

        Args:
            perm_str: 格式为 "root:name" 的字符串

        Returns:
            Permission 对象
        """
        root, name = perm_str.split(":", 1)
        return Permission(root, name)

    async def perm_command(self, command: CommandEvent) -> str:
        """权限管理命令处理器"""
        if not command.args:
            return self._get_help_message()

        subcommand = command.args[0]

        try:
            if subcommand == "show":
                return self.show_perms()
            elif subcommand == "list":
                return self.list_perms()
            elif subcommand == "add":
                if len(command.args) < 4:
                    return "错误: 参数不足\n用法: perms add <权限名> <用户ID> <群组ID>"
                perm = self._parse_permission(command.args[1])
                user_id = command.args[2]
                group_id = command.args[3] if len(command.args) > 3 else "-1"
                return self.add_perm(perm, user_id, group_id)
            elif subcommand == "remove":
                if len(command.args) < 4:
                    return (
                        "错误: 参数不足\n用法: perms remove <权限名> <用户ID> <群组ID>"
                    )
                perm = self._parse_permission(command.args[1])
                user_id = command.args[2]
                group_id = command.args[3] if len(command.args) > 3 else "-1"
                return self.remove_perm(perm, user_id, group_id)
            elif subcommand == "grant":
                if len(command.args) < 3:
                    return "错误: 参数不足\n用法: perms grant <权限名> <用户ID>"
                perm = self._parse_permission(command.args[1])
                user_id = command.args[2]
                return self.grant_global_perm(perm, user_id)
            elif subcommand == "revoke":
                if len(command.args) < 3:
                    return "错误: 参数不足\n用法: perms revoke <权限名> <用户ID>"
                perm = self._parse_permission(command.args[1])
                user_id = command.args[2]
                return self.revoke_global_perm(perm, user_id)
            else:
                return f"错误: 未知子命令 '{subcommand}'\n{self._get_help_message()}"
        except Exception as e:
            logger.error(f"Permission command execution error: {e}")
            return f"Error: {str(e)}"

    def _get_help_message(self) -> str:
        """获取帮助信息"""
        return (
            "权限管理命令\n"
            "用法:\n"
            "  perms show - 显示所有已注册权限\n"
            "  perms list - 列出用户和群组权限\n"
            "  perms add <权限名> <用户ID> [群组ID] - 添加权限\n"
            "  perms remove <权限名> <用户ID> [群组ID] - 移除权限\n"
            "  perms grant <权限名> <用户ID> - 授予用户全局权限\n"
            "  perms revoke <权限名> <用户ID> - 撤销用户全局权限"
        )

    def load_permissions(self):
        """加载权限数据（从 JSON 反序列化为 Permission 对象）"""
        if not os.path.exists(self.perm_file):
            logger.info("Permission file does not exist, creating new permission file")
            self.user_perms = {}
            self.group_perms = {}
            self.save_permissions()
        else:
            try:
                with open(self.perm_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 反序列化 user_perms：字符串 -> Permission 对象
                    self.user_perms = {}
                    raw_user_perms = data.get("user_perms", {})
                    for user_id, perm_entries in raw_user_perms.items():
                        self.user_perms[user_id] = []
                        for entry in perm_entries:
                            self.user_perms[user_id].append(
                                {
                                    "perm": self._deserialize_permission(entry["perm"]),
                                    "group": entry["group"],
                                }
                            )

                    # 反序列化 group_perms：字符串 -> Permission 对象
                    self.group_perms = {}
                    raw_group_perms = data.get("group_perms", {})
                    for group_id, perms in raw_group_perms.items():
                        self.group_perms[group_id] = [
                            self._deserialize_permission(p) for p in perms
                        ]

                logger.info(
                    f"Permission data loaded, users: {len(self.user_perms)}, groups: {len(self.group_perms)}"
                )
            except Exception as e:
                logger.error(f"Failed to load permission file: {e}")
                self.user_perms = {}
                self.group_perms = {}

        # 加载后重建索引
        self._rebuild_indexes()

    def save_permissions(self):
        """保存权限数据（将 Permission 对象序列化为 JSON）"""
        try:
            # 序列化 user_perms：Permission -> 字符串
            serializable_user_perms = {}
            for user_id, perm_entries in self.user_perms.items():
                serializable_user_perms[user_id] = [
                    {
                        "perm": self._serialize_permission(entry["perm"]),
                        "group": entry["group"],
                    }
                    for entry in perm_entries
                ]

            # 序列化 group_perms：Permission -> 字符串
            serializable_group_perms = {}
            for group_id, perms in self.group_perms.items():
                serializable_group_perms[group_id] = [
                    self._serialize_permission(p) for p in perms
                ]

            data = {
                "user_perms": serializable_user_perms,
                "group_perms": serializable_group_perms,
            }
            with open(self.perm_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save permission file: {e}")

    def register_perm(self, permission: Permission, desc: Optional[str] = None):
        """
        注册权限

        Args:
            permission: Permission 对象
            perm_desc: 权限描述
        """
        if not isinstance(permission, Permission):
            logger.error("Unsupported permission type: {}".format(type(permission)))
            return

        if permission.description is None:
            permission.description = desc or ""
        if permission in self.registered_perms:
            logger.warning(
                f"Permission '{permission}' already registered, overwriting..."
            )
        self.registered_perms[permission] = permission.description
        logger.debug(f"Registered permission: {permission} - {permission.description}")

    def add_perm(
        self, permission: Permission, user_id: str, group_id: str = "-1"
    ) -> str:
        """
        添加权限

        Args:
            permission: Permission 对象
            user_id: 用户ID
            group_id: 群组ID（默认为-1表示全局）

        Returns:
            操作结果消息
        """
        if permission not in self.registered_perms:
            return f"错误: 权限 '{permission}' 未注册"

        user_id = str(user_id)
        group_id = str(group_id)

        if user_id == "-1":
            # 群组权限
            if group_id not in self.group_perms:
                self.group_perms[group_id] = []
            if permission not in self.group_perms[group_id]:
                self.group_perms[group_id].append(permission)
                self._invalidate_cache()
                self._rebuild_indexes()
                self.save_permissions()
                return f"成功为群组 {group_id} 添加权限 '{permission}'"
            else:
                return f"群组 {group_id} 已拥有权限 '{permission}'"
        else:
            # 用户权限
            if user_id not in self.user_perms:
                self.user_perms[user_id] = []

            perm_entry = {"perm": permission, "group": group_id}

            if perm_entry not in self.user_perms[user_id]:
                self.user_perms[user_id].append(perm_entry)
                self._invalidate_cache()
                self._rebuild_indexes()
                self.save_permissions()
                return f"成功为用户 {user_id} 在群组 {group_id} 添加权限 '{permission}'"
            else:
                return f"用户 {user_id} 在群组 {group_id} 已拥有权限 '{permission}'"

    def remove_perm(
        self, permission: Permission, user_id: str, group_id: str = "-1"
    ) -> str:
        """
        移除权限

        Args:
            permission: Permission 对象
            user_id: 用户ID
            group_id: 群组ID（默认为-1表示全局）

        Returns:
            操作结果消息
        """
        user_id = str(user_id)
        group_id = str(group_id)

        if user_id == "-1":
            # 群组权限
            if (
                group_id in self.group_perms
                and permission in self.group_perms[group_id]
            ):
                self.group_perms[group_id].remove(permission)
                self._invalidate_cache()
                self._rebuild_indexes()
                self.save_permissions()
                return f"成功从群组 {group_id} 移除权限 '{permission}'"
            else:
                return f"群组 {group_id} 未拥有权限 '{permission}'"
        else:
            # 用户权限
            if user_id in self.user_perms:
                perm_entry = {"perm": permission, "group": group_id}
                if perm_entry in self.user_perms[user_id]:
                    self.user_perms[user_id].remove(perm_entry)
                    self._invalidate_cache()
                    self._rebuild_indexes()
                    self.save_permissions()
                    return f"成功从用户 {user_id} 在群组 {group_id} 移除权限 '{permission}'"

        return f"用户 {user_id} 在群组 {group_id} 未拥有权限 '{permission}'"

    def grant_global_perm(self, permission: Permission, user_id: str) -> str:
        """
        授予用户全局权限（在所有群组生效）

        Args:
            permission: Permission 对象
            user_id: 用户ID

        Returns:
            操作结果消息
        """
        return self.add_perm(permission, user_id, "ALL")

    def revoke_global_perm(self, permission: Permission, user_id: str) -> str:
        """
        撤销用户全局权限

        Args:
            permission: Permission 对象
            user_id: 用户ID

        Returns:
            操作结果消息
        """
        return self.remove_perm(permission, user_id, "ALL")

    def _is_root_match(
        self, user_root: str, user_name: str, check_root: str, check_name: str
    ) -> bool:
        """
        检查用户权限是否匹配待检查权限的根权限（字符串参数版本）

        Args:
            user_root: 用户权限根
            user_name: 用户权限名
            check_root: 待检查权限根
            check_name: 待检查权限名

        Returns:
            是否匹配（用户拥有根权限或相同权限）
        """
        # 完全相同
        if user_root == check_root and user_name == check_name:
            return True

        # 如果待检查权限是子权限，检查用户是否拥有对应的根权限
        # 拥有根权限（如 "core", ""）可以匹配所有子权限（如 "core", "admin"）
        if check_name and not user_name:
            return user_root == check_root

        return False

    @lru_cache(maxsize=1024)
    def _check_permission(
        self, user_id: str, group_id: str, perm_root: str, perm_name: str
    ) -> bool:
        """
        缓存的权限检查（内部使用）

        Args:
            user_id: 用户ID
            group_id: 群组ID
            perm_root: 权限根
            perm_name: 权限名

        Returns:
            是否拥有权限
        """
        # 解析待检查权限
        check_perm = Permission(perm_root, perm_name)

        # 检查 ALL 全局权限
        if self._all_perm in self._user_global_perms.get(user_id, set()):
            return True

        # 1. 检查用户全局权限（通过索引）
        user_global = self._user_global_perms.get(user_id)
        if user_global:
            for user_perm in user_global:
                if self._is_root_match(
                    user_perm.root, user_perm.name, perm_root, perm_name
                ):
                    return True

        # 2. 检查用户在特定群组的权限（通过索引）
        user_by_group = self._user_perms_by_group.get(user_id)
        if user_by_group:
            group_perms = user_by_group.get(group_id)
            if group_perms:
                for user_perm in group_perms:
                    if self._is_root_match(
                        user_perm.root, user_perm.name, perm_root, perm_name
                    ):
                        return True

        # 3. 检查群组权限（通过索引）
        group_perms = self._group_perms_index.get(group_id)
        if group_perms:
            for group_perm in group_perms:
                if self._is_root_match(
                    group_perm.root, group_perm.name, perm_root, perm_name
                ):
                    return True

        # 4. 检查全局群组权限（-1）
        global_group_perms = self._group_perms_index.get("-1")
        if global_group_perms:
            for group_perm in global_group_perms:
                if self._is_root_match(
                    group_perm.root, group_perm.name, perm_root, perm_name
                ):
                    return True

        return False

    def check_perm(
        self,
        permission: Union[PermissionType, List[PermissionType]],
        user_id: Union[str, int],
        group_id: Union[str, int] = -1,
    ) -> bool:
        """
        检查权限

        Args:
            permission: Permission 对象、PermissionSet 或列表
            user_id: 用户ID
            group_id: 群组ID（默认为-1）

        Returns:
            是否拥有权限
        """
        # Console用户拥有所有权限
        if str(user_id) == "Console":
            return True

        user_id_str = str(user_id)
        group_id_str = str(group_id)

        # 处理列表（OR逻辑）
        if isinstance(permission, list):
            for perm in permission:
                if self.check_perm(perm, user_id_str, group_id_str):
                    return True
            return False

        # Permission 或 PermissionSet
        return permission.check(self, user_id_str, group_id_str)

    def check_single(
        self, permission: Permission, user_id: str, group_id: str
    ) -> bool:
        """检查单个权限"""
        # 检查权限是否已注册
        if permission not in self.registered_perms:
            logger.warning(
                f"Permission '{permission}' not registered, skipping check"
            )
            return True

        return self._check_permission(user_id, group_id, permission.root, permission.name)

    def show_perms(self) -> str:
        """显示所有已注册权限"""
        if not self.registered_perms:
            return "暂无已注册权限"

        message = f"已注册权限 ({len(self.registered_perms)} 个):\n"
        for perm, perm_desc in self.registered_perms.items():
            message += f"  {perm}: {perm_desc}\n"
        return message

    def list_perms(self) -> str:
        """列出所有用户和群组权限"""
        message = "权限分配情况:\n\n"

        # 群组权限
        if self.group_perms:
            message += "群组权限:\n"
            for group_id, perms in self.group_perms.items():
                if perms:
                    message += f"  群组 {group_id}:\n"
                    for perm in perms:
                        message += f"    - {perm}\n"
        else:
            message += "暂无群组权限\n"

        message += "\n"

        # 用户权限
        if self.user_perms:
            message += "用户权限:\n"
            for user_id, perms in self.user_perms.items():
                if perms:
                    message += f"  用户 {user_id}:\n"
                    for perm_entry in perms:
                        group_info = (
                            f" (群组: {perm_entry['group']})"
                            if perm_entry["group"] != "ALL"
                            else " (全局)"
                        )
                        message += f"    - {perm_entry['perm']}{group_info}\n"
        else:
            message += "暂无用户权限\n"

        return message

    def get_user_perms(self, user_id: str) -> List[Dict[str, Permission]]:
        """获取用户的所有权限"""
        user_id = str(user_id)
        return self.user_perms.get(user_id, [])

    def get_group_perms(self, group_id: str) -> List[Permission]:
        """获取群组的所有权限"""
        group_id = str(group_id)
        return self.group_perms.get(group_id, [])

    def clear_user_perms(self, user_id: str) -> bool:
        """清除用户的所有权限"""
        user_id = str(user_id)
        if user_id in self.user_perms:
            del self.user_perms[user_id]
            self._invalidate_cache()
            self._rebuild_indexes()
            self.save_permissions()
            return True
        return False

    def clear_group_perms(self, group_id: str) -> bool:
        """清除群组的所有权限"""
        group_id = str(group_id)
        if group_id in self.group_perms:
            del self.group_perms[group_id]
            self._invalidate_cache()
            self._rebuild_indexes()
            self.save_permissions()
            return True
        return False