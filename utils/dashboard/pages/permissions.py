"""
权限管理页面

显示和管理权限信息。
"""

from typing import List, Dict, Any
import flet as ft

from ..components import DataTableComponent, create_table_with_header
from Coral import perm_system


class PermissionsPage:
    """权限管理页面"""
    
    def __init__(self, dashboard):
        """
        初始化权限页面
        
        Args:
            dashboard: Dashboard主类实例
        """
        self.dashboard = dashboard
        self.table = None
        
    def load(self) -> ft.Column:
        """
        加载页面内容
        
        Returns:
            页面内容列组件
        """
        # 创建操作按钮
        actions = [
            ft.ElevatedButton(
                "添加权限",
                on_click=self._add_permission,
                icon=ft.Icons.ADD
            ),
            ft.ElevatedButton(
                "刷新",
                on_click=self._refresh_permissions,
                icon=ft.Icons.REFRESH
            )
        ]
        
        # 创建表格
        columns = [
            {"key": "name", "label": "权限名称", "width": 200},
            {"key": "description", "label": "描述", "width": 300},
            {"key": "users_groups", "label": "用户/组", "width": 300}
        ]
        
        data = self._get_permissions_data()
        
        self.table = DataTableComponent(
            columns=columns,
            data=data,
            title="权限列表",
            border=True,
            striped=True,
            hoverable=True,
            pagination=True,
            page_size=10
        )
        
        return create_table_with_header(
            columns=columns,
            data=data,
            title="权限管理",
            actions=actions
        )
    
    def _get_permissions_data(self) -> List[Dict[str, Any]]:
        """
        获取权限数据
        
        Returns:
            权限数据列表
        """
        data = []
        
        for perm_name, perm_desc in perm_system.registered_perms.items():
            # 获取拥有此权限的用户/组
            users = []
            for user, perms in perm_system.user_perms.items():
                for perm in perms:
                    if isinstance(perm, tuple) and perm[0] == perm_name:
                        users.append(f"用户 {user} (组 {perm[1]})")
                    elif perm == perm_name:
                        users.append(f"组 {user}")
            
            data.append({
                "name": perm_name,
                "description": perm_desc,
                "users_groups": "\n".join(users) if users else "无"
            })
        
        return data
    
    def update(self) -> None:
        """更新页面数据"""
        if self.table:
            new_data = self._get_permissions_data()
            self.table.update_data(new_data)
    
    async def _add_permission(self, e) -> None:
        """添加权限"""
        # TODO: 实现添加权限功能
        alert = self.dashboard.show_alert_dialog(
            title="添加权限",
            message="添加权限功能正在开发中...",
            alert_type="info"
        )
        await alert.show()
    
    async def _refresh_permissions(self, e) -> None:
        """刷新权限列表"""
        self.update()
        self.dashboard.page.update()
        
        alert = self.dashboard.show_alert_dialog(
            title="刷新成功",
            message="权限列表已刷新",
            alert_type="success"
        )
        await alert.show()