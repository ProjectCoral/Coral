"""
Dashboard主模块

提供Dashboard的主要逻辑和入口点。
"""

import os
import time
import asyncio
import threading
import logging
import flet as ft
import psutil

from typing import Dict, Any, Optional
from Coral import (
    config, event_bus, register, perm_system,
    plugin_manager, driver_manager, adapter_manager
)

from .components import (
    InfoCard, StatusCard, UsageCard, ActionCard, MetricCard,
    CpuChart, MemoryChart, create_info_row,
    ConfirmationDialog, InputDialog, AlertDialog
)
from .pages import (
    OverviewPage, PluginsPage, AdaptersPage, DriversPage,
    ConfigPage, PermissionsPage, EventBusPage, TerminalPage
)

logger = logging.getLogger(__name__)


class CoralDashboard:
    """Coral Dashboard主类"""
    
    def __init__(self, page: ft.Page):
        """
        初始化Dashboard
        
        Args:
            page: Flet页面对象
        """
        self.page = page
        self._setup_page()
        self._init_components()
        self._setup_navigation()
        self._start_refresh_thread()
        
        # 加载默认页面
        self.load_page("overview")
    
    def _setup_page(self) -> None:
        """设置页面属性"""
        self.page.title = "Coral Framework Dashboard"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
            use_material3=True
        )
        
        # 状态栏
        self.status_bar = ft.Text(
            "系统状态: 正在初始化...",
            style="bodySmall",
            color=ft.Colors.with_opacity(0.7, ft.Colors.BLACK)
        )
    
    def _init_components(self) -> None:
        """初始化组件"""
        self.init_time = time.time()
        
        # 图表组件
        self.cpu_chart = CpuChart(self.init_time)
        self.memory_chart = MemoryChart(self.init_time)
        
        # 页面组件
        self.pages: Dict[str, Any] = {
            "overview": OverviewPage(self),
            "plugins": PluginsPage(self),
            "adapters": AdaptersPage(self),
            "drivers": DriversPage(self),
            "config": ConfigPage(self),
            "permissions": PermissionsPage(self),
            "event_bus": EventBusPage(self),
            "terminal": TerminalPage(self)
        }
        
        # 当前活动页面
        self.current_page: Optional[str] = None
    
    def _setup_navigation(self) -> None:
        """设置导航栏"""
        # 导航目的地
        destinations = [
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD,
                selected_icon=ft.Icons.DASHBOARD_OUTLINED,
                label="概览"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EXTENSION,
                selected_icon=ft.Icons.EXTENSION_OUTLINED,
                label="插件"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CONTACTLESS,
                selected_icon=ft.Icons.CONTACTLESS_OUTLINED,
                label="适配器"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DRIVE_ETA,
                selected_icon=ft.Icons.DRIVE_ETA_OUTLINED,
                label="驱动器"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS,
                selected_icon=ft.Icons.SETTINGS_OUTLINED,
                label="配置"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SECURITY,
                selected_icon=ft.Icons.SECURITY_OUTLINED,
                label="权限"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EVENT,
                selected_icon=ft.Icons.EVENT_AVAILABLE,
                label="事件总线"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.KEYBOARD_COMMAND_KEY,
                selected_icon=ft.Icons.KEYBOARD_COMMAND_KEY_OUTLINED,
                label="系统终端"
            ),
        ]
        
        # 导航栏
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=destinations,
            on_change=self._handle_navigation
        )
        
        # 内容区域
        self.content_area = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20
        )
        
        # 主布局
        self.main_layout = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                ft.Column([
                    self.content_area,
                    ft.Divider(),
                    self.status_bar
                ], expand=True)
            ],
            expand=True
        )
        
        self.page.add(self.main_layout)
    
    def _handle_navigation(self, e) -> None:
        """处理导航事件"""
        page_map = {
            0: "overview",
            1: "plugins",
            2: "adapters",
            3: "drivers",
            4: "config",
            5: "permissions",
            6: "event_bus",
            7: "terminal"
        }
        
        index = self.nav_rail.selected_index
        page_name = page_map.get(index, "overview")
        self.load_page(page_name)
    
    def load_page(self, page_name: str) -> None:
        """
        加载页面
        
        Args:
            page_name: 页面名称
        """
        if page_name not in self.pages:
            logger.error(f"未知页面: {page_name}")
            return
        
        # 清空内容区域
        self.content_area.controls.clear()
        
        # 加载页面内容
        page = self.pages[page_name]
        page_content = page.load()
        
        if page_content:
            self.content_area.controls.append(page_content)
        
        self.current_page = page_name
        self.page.update()
    
    def _start_refresh_thread(self) -> None:
        """启动数据刷新线程"""
        self.refresh_thread = threading.Thread(
            target=self._data_refresh_loop,
            daemon=True
        )
        self.refresh_thread.start()
    
    def _data_refresh_loop(self) -> None:
        """数据刷新循环"""
        while True:
            try:
                # 在主线程中更新UI
                self.page.run_task(self._update_ui_data)
                time.sleep(2)  # 每2秒刷新一次
            except Exception as e:
                logger.exception(f"Dashboard刷新错误: {e}")
                time.sleep(5)
    
    async def _update_ui_data(self) -> None:
        """更新UI数据"""
        try:
            # 更新状态栏
            self._update_status_bar()
            
            # 更新当前页面
            if self.current_page and self.current_page in self.pages:
                page = self.pages[self.current_page]
                if hasattr(page, 'update'):
                    page.update()
            
            self.page.update()
        except Exception as e:
            logger.exception(f"UI更新错误: {e}")
    
    def _update_status_bar(self) -> None:
        """更新状态栏"""
        try:
            status_text = (
                f"系统状态: 运行中 | "
                f"插件: {len(plugin_manager.plugins)} | "
                f"适配器: {len(adapter_manager.adapters)} | "
                f"驱动器: {len(driver_manager.drivers)} | "
                f"最后更新: {time.strftime('%H:%M:%S')}"
            )
            self.status_bar.value = status_text
        except Exception as e:
            logger.error(f"状态栏更新错误: {e}")
            self.status_bar.value = f"状态更新错误: {str(e)}"
    
    # 公共方法供页面使用
    
    def show_confirmation_dialog(
        self,
        title: str,
        message: str,
        on_confirm: Optional[callable] = None,
        on_cancel: Optional[callable] = None
    ) -> ConfirmationDialog:
        """
        显示确认对话框
        
        Args:
            title: 对话框标题
            message: 对话框消息
            on_confirm: 确认回调
            on_cancel: 取消回调
            
        Returns:
            ConfirmationDialog实例
        """
        return ConfirmationDialog(
            page=self.page,
            title=title,
            message=message,
            on_confirm=on_confirm,
            on_cancel=on_cancel
        )
    
    def show_input_dialog(
        self,
        title: str,
        message: str,
        default_value: str = "",
        on_confirm: Optional[callable] = None
    ) -> InputDialog:
        """
        显示输入对话框
        
        Args:
            title: 对话框标题
            message: 对话框消息
            default_value: 默认值
            on_confirm: 确认回调
            
        Returns:
            InputDialog实例
        """
        return InputDialog(
            page=self.page,
            title=title,
            message=message,
            default_value=default_value,
            on_confirm=on_confirm
        )
    
    def show_alert_dialog(
        self,
        title: str,
        message: str,
        alert_type: str = "info"
    ) -> AlertDialog:
        """
        显示警告对话框
        
        Args:
            title: 对话框标题
            message: 对话框消息
            alert_type: 对话框类型
            
        Returns:
            AlertDialog实例
        """
        return AlertDialog(
            page=self.page,
            title=title,
            message=message,
            alert_type=alert_type
        )
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        return {
            "coral_version": config.config.get("coral_version", "N/A"),
            "protocol_version": "1.0.1",
            "pluginmanager_version": plugin_manager.pluginmanager_version,
            "last_init_time": f"{config.config.get('last_init_time', 0):.2f}秒",
            "plugin_count": len(plugin_manager.plugins),
            "adapter_count": len(adapter_manager.adapters),
            "driver_count": len(driver_manager.drivers),
            "command_count": len(register.commands),
            "permission_count": len(perm_system.registered_perms),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else "N/A"
        }


def dashboard(page: ft.Page):
    """
    Dashboard入口函数
    
    Args:
        page: Flet页面对象
    """
    CoralDashboard(page)


async def run_dashboard(dashboard_config: Dict[str, Any]):
    """
    运行Dashboard
    
    Args:
        dashboard_config: Dashboard配置
    """
    logger.debug("启动Coral Dashboard...")
    
    # 获取主机和端口配置
    host = "0.0.0.0" if dashboard_config.get("listen", True) else "127.0.0.1"
    port = dashboard_config.get("port", 9000)
    
    # 启动Flet应用
    await ft.app_async(
        target=dashboard,
        use_color_emoji=True,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=port,
        assets_dir="assets"
    )