"""
卡片组件

提供各种类型的卡片组件，用于展示信息和操作。
"""

from typing import List, Dict, Any, Optional, Callable
import flet as ft


class InfoCard:
    """信息卡片，用于展示键值对信息"""
    
    def __init__(
        self,
        title: str,
        icon: str = ft.Icons.INFO,
        data: Optional[Dict[str, Any]] = None,
        items: Optional[List[Dict[str, Any]]] = None
    ):
        """
        初始化信息卡片
        
        Args:
            title: 卡片标题
            icon: 卡片图标
            data: 键值对数据字典
            items: 项目列表，每个项目包含label和value键
        """
        self.title = title
        self.icon = icon
        self.data = data or {}
        self.items = items or []
        
    def build(self) -> ft.Card:
        """构建卡片组件"""
        content_items = []
        
        # 添加标题
        content_items.append(
            ft.ListTile(
                leading=ft.Icon(self.icon),
                title=ft.Text(self.title),
            )
        )
        content_items.append(ft.Divider())
        
        # 添加数据项
        if self.data:
            for label, value in self.data.items():
                content_items.append(create_info_row(label, str(value)))
        elif self.items:
            for item in self.items:
                label = item.get("label", "")
                value = item.get("value", "")
                content_items.append(create_info_row(label, str(value)))
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(content_items),
                padding=15
            )
        )


class StatusCard(InfoCard):
    """状态卡片，专门用于展示系统状态"""
    
    def __init__(self, data: Dict[str, Any]):
        super().__init__(
            title="系统状态",
            icon=ft.Icons.MONITOR_HEART,
            data=data
        )


class UsageCard(InfoCard):
    """占用信息卡片，用于展示资源使用情况"""
    
    def __init__(
        self,
        data: Dict[str, Any],
        charts: Optional[List[ft.Control]] = None
    ):
        """
        初始化占用信息卡片
        
        Args:
            data: 占用数据
            charts: 图表组件列表
        """
        super().__init__(
            title="占用信息",
            icon=ft.Icons.MEMORY,
            data=data
        )
        self.charts = charts or []
        
    def build(self) -> ft.Card:
        """构建包含图表的卡片"""
        card = super().build()
        content = card.content.content
        
        # 在数据项后插入图表
        if self.charts:
            for i, chart in enumerate(self.charts):
                # 找到合适的位置插入图表
                content.controls.insert(2 + i, chart)
        
        return card


class ActionCard:
    """操作卡片，包含操作按钮"""
    
    def __init__(
        self,
        title: str,
        icon: str = ft.Icons.TOUCH_APP,
        actions: Optional[List[Dict[str, Any]]] = None
    ):
        """
        初始化操作卡片
        
        Args:
            title: 卡片标题
            icon: 卡片图标
            actions: 操作列表，每个操作包含text、on_click、color等键
        """
        self.title = title
        self.icon = icon
        self.actions = actions or []
        
    def build(self) -> ft.Card:
        """构建卡片组件"""
        content_items = [
            ft.ListTile(
                leading=ft.Icon(self.icon),
                title=ft.Text(self.title),
            ),
            ft.Divider()
        ]
        
        # 添加操作按钮
        for action in self.actions:
            button = ft.ElevatedButton(
                text=action.get("text", ""),
                on_click=action.get("on_click"),
                color=action.get("color"),
                bgcolor=action.get("bgcolor"),
                icon=action.get("icon")
            )
            content_items.append(button)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(content_items),
                padding=15
            )
        )


class MetricCard:
    """指标卡片，用于展示单个指标"""
    
    def __init__(
        self,
        title: str,
        value: Any,
        icon: str = ft.Icons.TRENDING_UP,
        unit: str = "",
        color: str = ft.Colors.BLUE,
        trend: Optional[float] = None
    ):
        """
        初始化指标卡片
        
        Args:
            title: 指标标题
            value: 指标值
            icon: 指标图标
            unit: 单位
            color: 颜色
            trend: 趋势值（正数表示上升，负数表示下降）
        """
        self.title = title
        self.value = value
        self.icon = icon
        self.unit = unit
        self.color = color
        self.trend = trend
        
    def build(self) -> ft.Card:
        """构建卡片组件"""
        # 构建趋势指示器
        trend_widget = ft.Container()
        if self.trend is not None:
            trend_icon = ft.Icons.TRENDING_UP if self.trend > 0 else ft.Icons.TRENDING_DOWN
            trend_color = ft.Colors.GREEN if self.trend > 0 else ft.Colors.RED
            trend_widget = ft.Row([
                ft.Icon(trend_icon, color=trend_color, size=16),
                ft.Text(f"{abs(self.trend):.1f}%", color=trend_color, size=12)
            ], spacing=4)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(self.icon, color=self.color),
                        ft.Text(self.title, style="bodyMedium")
                    ], spacing=8),
                    ft.Row([
                        ft.Text(
                            f"{self.value}{self.unit}",
                            style="headlineMedium",
                            color=self.color
                        ),
                        trend_widget
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=20,
                width=200
            )
        )


def create_info_row(label: str, value: str, label_width: int = 150) -> ft.Row:
    """
    创建信息行
    
    Args:
        label: 标签文本
        value: 值文本
        label_width: 标签宽度
        
    Returns:
        ft.Row组件
    """
    return ft.Row(
        controls=[
            ft.Text(f"{label}:", width=label_width, style="bodyMedium"),
            ft.Text(value, style="bodyMedium")
        ]
    )