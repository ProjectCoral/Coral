"""
事件总线页面

显示事件总线监控信息。
"""

from typing import List, Dict, Any
import time
import flet as ft

from ..components import DataTableComponent, create_table_with_header
from Coral import event_bus


class EventBusPage:
    """事件总线页面"""
    
    def __init__(self, dashboard):
        """
        初始化事件总线页面
        
        Args:
            dashboard: Dashboard主类实例
        """
        self.dashboard = dashboard
        self.events_table = None
        self.events_log = None
        
    def load(self) -> ft.Column:
        """
        加载页面内容
        
        Returns:
            页面内容列组件
        """
        content = ft.Column(spacing=20)
        
        # 页面标题
        content.controls.append(
            ft.Text("事件总线监控", style="headlineMedium")
        )
        
        # 事件类型表格
        events_data = self._get_events_data()
        events_columns = [
            {"key": "type", "label": "事件类型", "width": 250},
            {"key": "handlers", "label": "处理器数量", "width": 150},
            {"key": "last_activity", "label": "最后活动时间", "width": 150}
        ]
        
        self.events_table = DataTableComponent(
            columns=events_columns,
            data=events_data,
            title="事件类型",
            border=True,
            striped=True,
            hoverable=True
        )
        
        content.controls.append(self.events_table.build_with_container())
        
        # 最近事件日志
        content.controls.append(
            ft.Text("最近事件", style="titleMedium")
        )
        
        self.events_log = ft.Column(
            height=300,
            scroll=ft.ScrollMode.ALWAYS,
            spacing=5
        )
        
        log_container = ft.Container(
            content=self.events_log,
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            height=300
        )
        
        content.controls.append(log_container)
        
        return content
    
    def _get_events_data(self) -> List[Dict[str, Any]]:
        """
        获取事件数据
        
        Returns:
            事件数据列表
        """
        data = []
        
        for event_type, handlers in event_bus._subscribers.items():
            data.append({
                "type": event_type.__name__,
                "handlers": len(handlers),
                "last_activity": time.strftime('%H:%M:%S')
            })
        
        return data
    
    def update(self) -> None:
        """更新页面数据"""
        # 更新事件表格
        if self.events_table:
            new_data = self._get_events_data()
            self.events_table.update_data(new_data)
        
        # 这里可以添加事件日志的更新逻辑
        # 例如：self._add_event_log(event)