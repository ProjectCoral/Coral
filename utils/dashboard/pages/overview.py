"""
概览页面

显示系统概览信息，包括核心信息、系统状态、资源占用和操作。
"""

from typing import Dict, Any, Optional
import flet as ft
import psutil

from ..components import (
    InfoCard, StatusCard, UsageCard, ActionCard, MetricCard,
    create_info_row, create_chart_container
)


class OverviewPage:
    """概览页面"""
    
    def __init__(self, dashboard):
        """
        初始化概览页面
        
        Args:
            dashboard: Dashboard主类实例
        """
        self.dashboard = dashboard
        self.cpu_chart = dashboard.cpu_chart
        self.memory_chart = dashboard.memory_chart
        
        # 页面组件
        self.cards_container = None
        self.core_card = None
        self.status_card = None
        self.usage_card = None
        self.action_card = None
        
    def load(self) -> ft.Column:
        """
        加载页面内容
        
        Returns:
            页面内容列组件
        """
        content = ft.Column(spacing=20)
        
        # 页面标题
        content.controls.append(
            ft.Text("系统概览", style="headlineMedium")
        )
        
        # 创建卡片容器
        self.cards_container = ft.Row(wrap=True, spacing=20)
        self._create_cards()
        
        content.controls.append(self.cards_container)
        
        return content
    
    def _create_cards(self) -> None:
        """创建所有卡片"""
        # 获取系统信息
        system_info = self.dashboard.get_system_info()
        
        # 1. 核心信息卡片
        core_data = {
            "框架版本": system_info["coral_version"],
            "协议版本": system_info["protocol_version"],
            "插件管理器版本": system_info["pluginmanager_version"],
            "最后初始化时间": system_info["last_init_time"]
        }
        self.core_card = InfoCard(
            title="核心信息",
            icon=ft.Icons.INFO,
            data=core_data
        ).build()
        
        # 2. 系统状态卡片
        status_data = {
            "插件数量": system_info["plugin_count"],
            "适配器数量": system_info["adapter_count"],
            "驱动器数量": system_info["driver_count"],
            "注册命令": system_info["command_count"],
            "权限数量": system_info["permission_count"]
        }
        self.status_card = StatusCard(status_data).build()
        
        # 3. 占用信息卡片
        # 创建图表容器
        cpu_chart_container = create_chart_container(
            self.cpu_chart.update(),
            title="CPU使用率",
            height=200,
            width=600
        )
        
        memory_chart_container = create_chart_container(
            self.memory_chart.update(),
            title="内存使用",
            height=200,
            width=600
        )
        
        usage_data = {
            "CPU使用率": f"{system_info['cpu_percent']}%",
            "内存使用率": f"{system_info['memory_percent']}%",
            "磁盘使用率": f"{system_info['disk_percent']}"
        }
        
        self.usage_card = UsageCard(
            data=usage_data,
            charts=[cpu_chart_container, memory_chart_container]
        ).build()
        
        # 4. 操作卡片
        actions = [
            {
                "text": "重新加载插件",
                "on_click": self._reload_plugins,
                "icon": ft.Icons.REFRESH
            },
            {
                "text": "停止框架",
                "on_click": self._stop_framework,
                "color": ft.Colors.RED,
                "icon": ft.Icons.STOP
            }
        ]
        self.action_card = ActionCard(
            title="操作",
            icon=ft.Icons.TOUCH_APP,
            actions=actions
        ).build()
        
        # 5. 指标卡片（快速概览）
        metric_cards = self._create_metric_cards(system_info)
        
        # 将所有卡片添加到容器
        self.cards_container.controls = [
            self.core_card,
            self.status_card,
            self.usage_card,
            self.action_card,
            *metric_cards
        ]
    
    def _create_metric_cards(self, system_info: Dict[str, Any]) -> list:
        """
        创建指标卡片
        
        Args:
            system_info: 系统信息
            
        Returns:
            指标卡片列表
        """
        metrics = [
            MetricCard(
                title="CPU使用率",
                value=system_info["cpu_percent"],
                unit="%",
                icon=ft.Icons.MEMORY,
                color=ft.Colors.BLUE,
                trend=0  # 这里可以添加趋势计算
            ),
            MetricCard(
                title="内存使用率",
                value=system_info["memory_percent"],
                unit="%",
                icon=ft.Icons.STORAGE,
                color=ft.Colors.GREEN,
                trend=0
            ),
            MetricCard(
                title="插件数量",
                value=system_info["plugin_count"],
                icon=ft.Icons.EXTENSION,
                color=ft.Colors.ORANGE
            ),
            MetricCard(
                title="适配器数量",
                value=system_info["adapter_count"],
                icon=ft.Icons.CONTACTLESS,
                color=ft.Colors.PURPLE
            )
        ]
        
        return [metric.build() for metric in metrics]
    
    def update(self) -> None:
        """更新页面数据"""
        if not self.cards_container:
            return
        
        # 获取最新系统信息
        system_info = self.dashboard.get_system_info()
        
        # 更新状态卡片
        if self.status_card:
            status_content = self.status_card.content.content
            # 更新状态数据
            status_items = [
                ("插件数量", system_info["plugin_count"]),
                ("适配器数量", system_info["adapter_count"]),
                ("驱动器数量", system_info["driver_count"]),
                ("注册命令", system_info["command_count"]),
                ("权限数量", system_info["permission_count"])
            ]
            
            # 更新状态卡片内容
            for i, (label, value) in enumerate(status_items):
                if i + 2 < len(status_content.controls):  # +2 跳过标题和分割线
                    status_content.controls[i + 2] = create_info_row(label, str(value))
        
        # 更新占用信息卡片
        if self.usage_card:
            usage_content = self.usage_card.content.content
            # 更新占用数据
            usage_items = [
                ("CPU使用率", f"{system_info['cpu_percent']}%"),
                ("内存使用率", f"{system_info['memory_percent']}%"),
                ("磁盘使用率", f"{system_info['disk_percent']}")
            ]
            
            # 找到数据行的起始位置（跳过标题、分割线和图表）
            data_start_idx = 2  # 标题和分割线
            # 跳过图表（如果有）
            for i in range(len(usage_content.controls)):
                if isinstance(usage_content.controls[i], ft.Row):
                    data_start_idx = i
                    break
            
            # 更新占用数据
            for i, (label, value) in enumerate(usage_items):
                if data_start_idx + i < len(usage_content.controls):
                    usage_content.controls[data_start_idx + i] = create_info_row(label, value)
            
            # 更新图表
            # 查找图表容器并更新
            for i, control in enumerate(usage_content.controls):
                if isinstance(control, ft.Container) and hasattr(control.content, 'controls'):
                    # 检查是否是图表容器
                    if len(control.content.controls) > 1:
                        # 第一个是CPU图表，第二个是内存图表
                        if "CPU使用率" in str(control.content.controls[0]):
                            # 更新CPU图表
                            cpu_chart = self.cpu_chart.update()
                            chart_container = create_chart_container(
                                cpu_chart,
                                title="CPU使用率",
                                height=200,
                                width=600
                            )
                            usage_content.controls[i] = chart_container
                        elif "内存使用" in str(control.content.controls[0]):
                            # 更新内存图表
                            memory_chart = self.memory_chart.update()
                            chart_container = create_chart_container(
                                memory_chart,
                                title="内存使用",
                                height=200,
                                width=600
                            )
                            usage_content.controls[i] = chart_container
    
    async def _reload_plugins(self, e) -> None:
        """重新加载插件"""
        from Coral import plugin_manager
        import asyncio
        
        # 显示确认对话框
        dialog = self.dashboard.show_confirmation_dialog(
            title="重新加载插件",
            message="确定要重新加载所有插件吗？",
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                plugin_manager.reload_plugins(),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()
    
    async def _stop_framework(self, e) -> None:
        """停止框架"""
        from Coral import event_bus
        from Coral.protocol import CommandEvent, MessageChain, MessageSegment, UserInfo
        import asyncio
        import time
        
        # 显示确认对话框
        dialog = self.dashboard.show_confirmation_dialog(
            title="停止框架",
            message="确定要停止Coral框架吗？",
            confirm_color=ft.Colors.RED,
            on_confirm=lambda e: asyncio.run_coroutine_threadsafe(
                event_bus.publish(
                    CommandEvent(
                        event_id=f"console-{time.time()}",
                        platform="console",
                        self_id="Console",
                        command="stop",
                        raw_message=MessageChain([MessageSegment.text("stop")]),
                        user=UserInfo(
                            platform="system",
                            user_id="Console"
                        ),
                        args=[]
                    )
                ),
                asyncio.get_event_loop()
            )
        )
        await dialog.show()