"""
驱动器管理页面

显示和管理驱动器信息。
"""

from typing import List, Dict, Any
import flet as ft

from ..components import DataTableComponent, create_table_with_header, create_action_buttons
from Coral import driver_manager


class DriversPage:
    """驱动器管理页面"""
    
    def __init__(self, dashboard):
        """
        初始化驱动器页面
        
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
                "启动所有驱动器",
                on_click=self._start_all_drivers,
                icon=ft.Icons.PLAY_ARROW
            ),
            ft.ElevatedButton(
                "停止所有驱动器",
                on_click=self._stop_all_drivers,
                icon=ft.Icons.STOP,
                color=ft.Colors.RED
            )
        ]
        
        # 创建表格
        columns = [
            {"key": "name", "label": "名称", "width": 150},
            {"key": "type", "label": "类型", "width": 200},
            {"key": "status", "label": "状态", "width": 100},
            {"key": "actions", "label": "操作", "width": 150}
        ]
        
        data = self._get_drivers_data()
        
        self.table = DataTableComponent(
            columns=columns,
            data=data,
            title="驱动器列表",
            border=True,
            striped=True,
            hoverable=True
        )
        
        return create_table_with_header(
            columns=columns,
            data=data,
            title="驱动器管理",
            actions=actions
        )
    
    def _get_drivers_data(self) -> List[Dict[str, Any]]:
        """
        获取驱动器数据
        
        Returns:
            驱动器数据列表
        """
        data = []
        
        for name, driver in driver_manager.drivers.items():
            status = "运行中" if driver._running else "已停止"
            color = ft.Colors.GREEN if driver._running else ft.Colors.RED
            
            # 创建操作按钮
            action_buttons = create_action_buttons([
                {
                    "icon": ft.Icons.PLAY_ARROW if not driver._running else ft.Icons.PAUSE,
                    "on_click": lambda e, d=driver: self._toggle_driver(d),
                    "tooltip": "启动/停止",
                    "color": ft.Colors.BLUE
                },
                {
                    "icon": ft.Icons.INFO,
                    "on_click": lambda e, d=driver: self._show_driver_info(d),
                    "tooltip": "查看详情",
                    "color": ft.Colors.GREEN
                }
            ])
            
            data.append({
                "name": name,
                "type": driver.__class__.__name__,
                "status": ft.Text(status, color=color),
                "actions": action_buttons
            })
        
        return data
    
    def update(self) -> None:
        """更新页面数据"""
        if self.table:
            new_data = self._get_drivers_data()
            self.table.update_data(new_data)
    
    async def _start_all_drivers(self, e) -> None:
        """启动所有驱动器"""
        import asyncio
        
        dialog = self.dashboard.show_confirmation_dialog(
            title="启动驱动器",
            message="确定要启动所有驱动器吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                driver_manager.start_all(),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _stop_all_drivers(self, e) -> None:
        """停止所有驱动器"""
        import asyncio
        
        dialog = self.dashboard.show_confirmation_dialog(
            title="停止驱动器",
            message="确定要停止所有驱动器吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                driver_manager.stop_all(),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _toggle_driver(self, driver) -> None:
        """切换驱动器状态"""
        import asyncio
        
        action = "停止" if driver._running else "启动"
        dialog = self.dashboard.show_confirmation_dialog(
            title=f"{action}驱动器",
            message=f"确定要{action}这个驱动器吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                driver.stop() if driver._running else driver.start(),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _show_driver_info(self, driver) -> None:
        """显示驱动器详情"""
        alert = self.dashboard.show_alert_dialog(
            title="驱动器详情",
            message=f"驱动器 '{driver.__class__.__name__}' 的详细信息正在开发中...",
            alert_type="info"
        )
        await alert.show()