"""
Coral 权限系统
"""
import os
import json
import logging
from typing import Union, List, Dict
from .protocol import CommandEvent

logger = logging.getLogger(__name__)


class PermSystem:
    """权限系统"""
    
    def __init__(self, register, config):
        """
        初始化权限系统
        
        Args:
            register: 注册器实例
            config: 配置实例
        """
        self.register = register
        self.config = config
        self.perm_file = self.config.get("perm_file", "./coral.perms")
        
        # 权限数据存储
        self.registered_perms: Dict[str, str] = {}  # 权限名 -> 描述
        self.user_perms: Dict[str, List[Dict[str, str]]] = {}  # 用户ID -> 权限列表
        self.group_perms: Dict[str, List[str]] = {}  # 群组ID -> 权限列表
        
        self.load_permissions()
        
        # 注册基础权限
        self.register_perm("ALL", "所有权限")
        self.register_perm("permission_system", "权限系统基础权限")
        
        # 注册权限管理命令
        self.register.register_command(
            "perms",
            "权限管理命令\n"
            "用法:\n"
            "  perms show - 显示所有已注册权限\n"
            "  perms list - 列出用户和群组权限\n"
            "  perms add <权限名> <用户ID> [群组ID] - 添加权限\n"
            "  perms remove <权限名> <用户ID> [群组ID] - 移除权限\n"
            "  perms grant <权限名> <用户ID> - 授予用户全局权限\n"
            "  perms revoke <权限名> <用户ID> - 撤销用户全局权限",
            self.perm_command,
            ["permission_system"],
        )
    
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
                perm_name = command.args[1]
                user_id = command.args[2]
                group_id = command.args[3] if len(command.args) > 3 else "-1"
                return self.add_perm(perm_name, user_id, group_id)
            elif subcommand == "remove":
                if len(command.args) < 4:
                    return "错误: 参数不足\n用法: perms remove <权限名> <用户ID> <群组ID>"
                perm_name = command.args[1]
                user_id = command.args[2]
                group_id = command.args[3] if len(command.args) > 3 else "-1"
                return self.remove_perm(perm_name, user_id, group_id)
            elif subcommand == "grant":
                if len(command.args) < 3:
                    return "错误: 参数不足\n用法: perms grant <权限名> <用户ID>"
                perm_name = command.args[1]
                user_id = command.args[2]
                return self.grant_global_perm(perm_name, user_id)
            elif subcommand == "revoke":
                if len(command.args) < 3:
                    return "错误: 参数不足\n用法: perms revoke <权限名> <用户ID>"
                perm_name = command.args[1]
                user_id = command.args[2]
                return self.revoke_global_perm(perm_name, user_id)
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
        """加载权限数据"""
        if not os.path.exists(self.perm_file):
            logger.info("Permission file does not exist, creating new permission file")
            self.user_perms = {}
            self.group_perms = {}
            self.save_permissions()
        else:
            try:
                with open(self.perm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_perms = data.get('user_perms', {})
                    self.group_perms = data.get('group_perms', {})
                logger.info(f"Permission data loaded, users: {len(self.user_perms)}, groups: {len(self.group_perms)}")
            except Exception as e:
                logger.error(f"Failed to load permission file: {e}")
                self.user_perms = {}
                self.group_perms = {}
    
    def save_permissions(self):
        """保存权限数据"""
        try:
            data = {
                'user_perms': self.user_perms,
                'group_perms': self.group_perms
            }
            with open(self.perm_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save permission file: {e}")
    
    def register_perm(self, perm_name: str, perm_desc: str):
        """
        注册权限
        
        Args:
            perm_name: 权限名称
            perm_desc: 权限描述
        """
        if perm_name in self.registered_perms:
            logger.warning(f"Permission '{perm_name}' already registered, overwriting description")
        self.registered_perms[perm_name] = perm_desc
        logger.debug(f"Registered permission: {perm_name} - {perm_desc}")
    
    def add_perm(self, perm_name: str, user_id: str, group_id: str = "-1") -> str:
        """
        添加权限
        
        Args:
            perm_name: 权限名称
            user_id: 用户ID
            group_id: 群组ID（默认为-1表示全局）
        
        Returns:
            操作结果消息
        """
        if perm_name not in self.registered_perms:
            return f"错误: 权限 '{perm_name}' 未注册"
        
        user_id = str(user_id)
        group_id = str(group_id)
        
        if user_id == "-1":
            # 群组权限
            if group_id not in self.group_perms:
                self.group_perms[group_id] = []
            if perm_name not in self.group_perms[group_id]:
                self.group_perms[group_id].append(perm_name)
                self.save_permissions()
                return f"成功为群组 {group_id} 添加权限 '{perm_name}'"
            else:
                return f"群组 {group_id} 已拥有权限 '{perm_name}'"
        else:
            # 用户权限
            if user_id not in self.user_perms:
                self.user_perms[user_id] = []
            
            perm_entry = {
                'perm': perm_name,
                'group': group_id
            }
            
            if perm_entry not in self.user_perms[user_id]:
                self.user_perms[user_id].append(perm_entry)
                self.save_permissions()
                return f"成功为用户 {user_id} 在群组 {group_id} 添加权限 '{perm_name}'"
            else:
                return f"用户 {user_id} 在群组 {group_id} 已拥有权限 '{perm_name}'"
    
    def remove_perm(self, perm_name: str, user_id: str, group_id: str = "-1") -> str:
        """
        移除权限
        
        Args:
            perm_name: 权限名称
            user_id: 用户ID
            group_id: 群组ID（默认为-1表示全局）
        
        Returns:
            操作结果消息
        """
        user_id = str(user_id)
        group_id = str(group_id)
        
        if user_id == "-1":
            # 群组权限
            if group_id in self.group_perms and perm_name in self.group_perms[group_id]:
                self.group_perms[group_id].remove(perm_name)
                self.save_permissions()
                return f"成功从群组 {group_id} 移除权限 '{perm_name}'"
            else:
                return f"群组 {group_id} 未拥有权限 '{perm_name}'"
        else:
            # 用户权限
            if user_id in self.user_perms:
                perm_entry = {
                    'perm': perm_name,
                    'group': group_id
                }
                if perm_entry in self.user_perms[user_id]:
                    self.user_perms[user_id].remove(perm_entry)
                    self.save_permissions()
                    return f"成功从用户 {user_id} 在群组 {group_id} 移除权限 '{perm_name}'"
        
        return f"用户 {user_id} 在群组 {group_id} 未拥有权限 '{perm_name}'"
    
    def grant_global_perm(self, perm_name: str, user_id: str) -> str:
        """
        授予用户全局权限（在所有群组生效）
        
        Args:
            perm_name: 权限名称
            user_id: 用户ID
        
        Returns:
            操作结果消息
        """
        return self.add_perm(perm_name, user_id, "ALL")
    
    def revoke_global_perm(self, perm_name: str, user_id: str) -> str:
        """
        撤销用户全局权限
        
        Args:
            perm_name: 权限名称
            user_id: 用户ID
        
        Returns:
            操作结果消息
        """
        return self.remove_perm(perm_name, user_id, "ALL")
    
    def check_perm(
        self, 
        perm_name: Union[str, List[str]], 
        user_id: Union[str, int], 
        group_id: Union[str, int] = -1
    ) -> bool:
        """
        检查权限
        
        Args:
            perm_name: 权限名称或权限列表
            user_id: 用户ID
            group_id: 群组ID（默认为-1）
        
        Returns:
            是否拥有权限
        """
        # Console用户拥有所有权限
        if str(user_id) == "Console":
            return True
        
        # 处理权限列表
        if isinstance(perm_name, list):
            for perm in perm_name:
                if self._check_single_perm(perm, user_id, group_id):
                    return True
            return False
        
        return self._check_single_perm(perm_name, user_id, group_id)
    
    def _check_single_perm(self, perm_name: str, user_id: Union[str, int], group_id: Union[str, int]) -> bool:
        """检查单个权限"""
        user_id = str(user_id)
        group_id = str(group_id)
        
        # 检查权限是否已注册
        if perm_name not in self.registered_perms:
            logger.warning(f"Permission '{perm_name}' not registered, skipping check")
            return True
        
        # 1. 检查用户全局权限
        if user_id in self.user_perms:
            for perm_entry in self.user_perms[user_id]:
                if perm_entry['perm'] == "ALL":
                    return True
                if perm_entry['perm'] == perm_name and perm_entry['group'] == "ALL":
                    return True
        
        # 2. 检查用户在特定群组的权限
        if user_id in self.user_perms:
            for perm_entry in self.user_perms[user_id]:
                if perm_entry['perm'] == perm_name and perm_entry['group'] == group_id:
                    return True
        
        # 3. 检查群组权限
        if group_id in self.group_perms:
            if perm_name in self.group_perms[group_id]:
                return True
        
        # 4. 检查全局群组权限
        if "-1" in self.group_perms:
            if perm_name in self.group_perms["-1"]:
                return True
        
        return False
    
    def show_perms(self) -> str:
        """显示所有已注册权限"""
        if not self.registered_perms:
            return "暂无已注册权限"
        
        message = f"已注册权限 ({len(self.registered_perms)} 个):\n"
        for perm_name, perm_desc in self.registered_perms.items():
            message += f"  {perm_name}: {perm_desc}\n"
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
                        group_info = f" (群组: {perm_entry['group']})" if perm_entry['group'] != "ALL" else " (全局)"
                        message += f"    - {perm_entry['perm']}{group_info}\n"
        else:
            message += "暂无用户权限\n"
        
        return message
    
    def get_user_perms(self, user_id: str) -> List[Dict[str, str]]:
        """获取用户的所有权限"""
        user_id = str(user_id)
        return self.user_perms.get(user_id, [])
    
    def get_group_perms(self, group_id: str) -> List[str]:
        """获取群组的所有权限"""
        group_id = str(group_id)
        return self.group_perms.get(group_id, [])
    
    def clear_user_perms(self, user_id: str) -> bool:
        """清除用户的所有权限"""
        user_id = str(user_id)
        if user_id in self.user_perms:
            del self.user_perms[user_id]
            self.save_permissions()
            return True
        return False
    
    def clear_group_perms(self, group_id: str) -> bool:
        """清除群组的所有权限"""
        group_id = str(group_id)
        if group_id in self.group_perms:
            del self.group_perms[group_id]
            self.save_permissions()
            return True
        return False