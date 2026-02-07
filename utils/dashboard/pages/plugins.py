"""
插件管理页面

显示和管理插件信息。
"""

from typing import List, Dict, Any
import flet as ft

from ..components import DataTableComponent, create_table_with_header, create_action_buttons
from Coral import plugin_manager


class PluginsPage:
    """插件管理页面"""
    
    def __init__(self, dashboard):
        """
        初始化插件页面
        
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
        # 创建操作按钮 - 使用包装函数处理异步调用
        actions = [
            ft.ElevatedButton(
                "重新加载所有插件",
                on_click=self._handle_reload_all_plugins,
                icon=ft.Icons.REFRESH
            ),
            ft.ElevatedButton(
                "安装依赖",
                on_click=self._handle_install_dependencies,
                icon=ft.Icons.DOWNLOAD
            )
        ]
        
        # 创建表格
        columns = [
            {"key": "name", "label": "插件名称", "width": 200},
            {"key": "compatibility", "label": "兼容性", "width": 100},
            {"key": "status", "label": "状态", "width": 100},
            {"key": "actions", "label": "操作", "width": 150}
        ]
        
        data = self._get_plugins_data()
        
        self.table = DataTableComponent(
            columns=columns,
            data=data,
            title="插件列表",
            border=True,
            striped=True,
            hoverable=True,
            pagination=True,
            page_size=10
        )
        
        return create_table_with_header(
            columns=columns,
            data=data,
            title="插件管理",
            actions=actions
        )
    
    def _get_plugins_data(self) -> List[Dict[str, Any]]:
        """
        获取插件数据
        
        Returns:
            插件数据列表
        """
        data = []
        
        for plugin in plugin_manager.plugins:
            # 获取插件元数据
            # 注意：plugin_manager没有get_plugin_meta方法，使用其他方式获取兼容性信息
            compatibility = "N/A"
            # 尝试从插件目录获取信息
            plugin_path = f"./plugins/{plugin}"
            init_file = f"{plugin_path}/__init__.py"
            
            # 这里简化处理，实际应该解析插件元数据
            # 由于plugin_manager没有公开的get_plugin_meta方法，我们使用默认值
            compatibility = "兼容"
            
            # 创建操作按钮 - 使用包装函数处理异步调用
            action_buttons = create_action_buttons([
                {
                    "icon": ft.Icons.REFRESH,
                    "on_click": lambda e, p=plugin: self._handle_reload_single_plugin(e, p),
                    "tooltip": "重新加载插件",
                    "color": ft.Colors.BLUE
                },
                {
                    "icon": ft.Icons.INFO,
                    "on_click": lambda e, p=plugin: self._handle_show_plugin_info(e, p),
                    "tooltip": "查看详情",
                    "color": ft.Colors.GREEN
                }
            ])
            
            data.append({
                "name": plugin,
                "compatibility": str(compatibility),
                "status": ft.Text("已加载", color=ft.Colors.GREEN),
                "actions": action_buttons
            })
        
        return data
    
    def update(self) -> None:
        """更新页面数据"""
        if self.table:
            new_data = self._get_plugins_data()
            self.table.update_data(new_data)
    
    async def _reload_all_plugins(self, e) -> None:
        """重新加载所有插件"""
        import asyncio
        
        dialog = self.dashboard.show_confirmation_dialog(
            title="重新加载插件",
            message="确定要重新加载所有插件吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                plugin_manager.reload_plugins(),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _reload_single_plugin(self, plugin_name: str) -> None:
        """重新加载单个插件"""
        import asyncio
        
        dialog = self.dashboard.show_confirmation_dialog(
            title="重新加载插件",
            message=f"确定要重新加载插件 '{plugin_name}' 吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                plugin_manager.reload_plugin(plugin_name),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _install_dependencies(self, e) -> None:
        """安装依赖"""
        # TODO: 实现依赖安装逻辑
        alert = self.dashboard.show_alert_dialog(
            title="安装依赖",
            message="依赖安装功能正在开发中...",
            alert_type="info"
        )
        await alert.show()
    
    async def _show_plugin_info(self, plugin_name: str) -> None:
        """显示插件详情"""
        # TODO: 实现插件详情显示
        alert = self.dashboard.show_alert_dialog(
            title="插件详情",
            message=f"插件 '{plugin_name}' 的详细信息正在开发中...",
            alert_type="info"
        )
        await alert.show()
    
    def _handle_reload_single_plugin(self, e, plugin_name: str) -> None:
        """处理重新加载单个插件（包装函数）"""
        import asyncio
        # 在事件循环中运行异步函数
        asyncio.create_task(self._reload_single_plugin(plugin_name))
    
    def _handle_show_plugin_info(self, e, plugin_name: str) -> None:
        """处理显示插件详情（包装函数）"""
        import asyncio
        # 在事件循环中运行异步函数
        asyncio.create_task(self._show_plugin_info(plugin_name))
    
    def _handle_reload_all_plugins(self, e) -> None:
        """处理重新加载所有插件（包装函数）"""
        import asyncio
        # 在事件循环中运行异步函数
        asyncio.create_task(self._reload_all_plugins(e))
    
    def _handle_install_dependencies(self, e) -> None:
        """处理安装依赖（包装函数）"""
        import asyncio
        # 在事件循环中运行异步函数
        asyncio.create_task(self._install_dependencies(e))
