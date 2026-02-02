"""
图表组件

提供各种类型的图表组件，用于数据可视化。
"""

from typing import List, Tuple, Optional, Any, Dict
import time
import psutil
import flet as ft


class LineChartComponent:
    """折线图组件基类"""
    
    def __init__(
        self,
        title: str = "",
        height: int = 200,
        width: int = 600,
        min_y: float = 0,
        max_y: float = 100,
        data_points: Optional[List[Tuple[float, float]]] = None,
        color: str = ft.Colors.BLUE,
        show_grid: bool = True,
        curved: bool = True
    ):
        """
        初始化折线图组件
        
        Args:
            title: 图表标题
            height: 图表高度
            width: 图表宽度
            min_y: Y轴最小值
            max_y: Y轴最大值
            data_points: 数据点列表，每个点为(x, y)元组
            color: 线条颜色
            show_grid: 是否显示网格
            curved: 是否使用曲线
        """
        self.title = title
        self.height = height
        self.width = width
        self.min_y = min_y
        self.max_y = max_y
        self.data_points = data_points or []
        self.color = color
        self.show_grid = show_grid
        self.curved = curved
        
    def add_data_point(self, x: float, y: float) -> None:
        """添加数据点"""
        self.data_points.append((x, y))
        
    def clear_data(self) -> None:
        """清空数据"""
        self.data_points.clear()
        
    def build(self) -> ft.LineChart:
        """构建图表组件"""
        # 创建数据系列
        chart_data = [
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x, y) for x, y in self.data_points],
                color=self.color,
                stroke_width=2,
                curved=self.curved
            )
        ]
        
        # 创建Y轴标签
        y_labels = []
        y_step = (self.max_y - self.min_y) / 5
        for i in range(6):
            value = self.min_y + i * y_step
            y_labels.append(
                ft.ChartAxisLabel(
                    value=value,
                    label=ft.Text(f"{value:.1f}")
                )
            )
        
        # 创建X轴标签（基于时间）
        x_labels = []
        if self.data_points:
            min_x = min(x for x, _ in self.data_points)
            max_x = max(x for x, _ in self.data_points)
            x_range = max_x - min_x
            
            if x_range > 0:
                for i in range(6):
                    value = min_x + i * (x_range / 5)
                    x_labels.append(
                        ft.ChartAxisLabel(
                            value=value,
                            label=ft.Text(f"{value:.0f}s")
                        )
                    )
        
        return ft.LineChart(
            data_series=chart_data,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            left_axis=ft.ChartAxis(
                labels=y_labels,
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=x_labels if x_labels else [],
                labels_size=40,
            ),
            height=self.height,
            width=self.width,
            min_y=self.min_y,
            max_y=self.max_y,
            min_x=self.data_points[0][0] if self.data_points else 0,
            max_x=self.data_points[-1][0] if self.data_points else 60,
            expand=True,
            interactive=True,
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
        )


class CpuChart(LineChartComponent):
    """CPU使用率图表"""
    
    def __init__(self, init_time: Optional[float] = None):
        """
        初始化CPU图表
        
        Args:
            init_time: 初始化时间戳
        """
        super().__init__(
            title="CPU使用率",
            min_y=0,
            max_y=100,
            color=ft.Colors.BLUE
        )
        self.init_time = init_time or time.time()
        self.data_history: List[Tuple[float, float]] = []
        self.max_history_points = 60  # 最多保存60个数据点
        
    def update(self) -> ft.LineChart:
        """更新CPU数据并返回图表"""
        current_time = time.time()
        elapsed = current_time - self.init_time
        cpu_percent = psutil.cpu_percent()
        
        # 添加新数据点
        self.add_data_point(elapsed, cpu_percent)
        self.data_history.append((elapsed, cpu_percent))
        
        # 限制历史数据长度
        if len(self.data_history) > self.max_history_points:
            self.data_history.pop(0)
            # 重新构建数据点
            self.clear_data()
            for x, y in self.data_history:
                self.add_data_point(x, y)
        
        return self.build()


class MemoryChart(LineChartComponent):
    """内存使用图表"""
    
    def __init__(self, init_time: Optional[float] = None):
        """
        初始化内存图表
        
        Args:
            init_time: 初始化时间戳
        """
        super().__init__(
            title="内存使用",
            min_y=0,
            max_y=4096,  # 默认4GB
            color=ft.Colors.GREEN
        )
        self.init_time = init_time or time.time()
        self.data_history: List[Tuple[float, float]] = []
        self.max_history_points = 60
        
    def update(self) -> ft.LineChart:
        """更新内存数据并返回图表"""
        current_time = time.time()
        elapsed = current_time - self.init_time
        
        # 获取内存信息
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # 动态调整Y轴最大值
        if memory_mb > self.max_y * 0.8:
            self.max_y = max(self.max_y * 1.5, memory_mb * 1.2)
        
        # 添加新数据点
        self.add_data_point(elapsed, memory_mb)
        self.data_history.append((elapsed, memory_mb))
        
        # 限制历史数据长度
        if len(self.data_history) > self.max_history_points:
            self.data_history.pop(0)
            # 重新构建数据点
            self.clear_data()
            for x, y in self.data_history:
                self.add_data_point(x, y)
        
        return self.build()


class MultiSeriesChart(LineChartComponent):
    """多系列图表"""
    
    def __init__(
        self,
        series_configs: List[Dict[str, Any]],
        **kwargs
    ):
        """
        初始化多系列图表
        
        Args:
            series_configs: 系列配置列表，每个配置包含name、color、data等
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)
        self.series_configs = series_configs
        
    def build(self) -> ft.LineChart:
        """构建多系列图表"""
        chart_data = []
        
        for config in self.series_configs:
            data_points = config.get("data_points", [])
            chart_data.append(
                ft.LineChartData(
                    data_points=[ft.LineChartDataPoint(x, y) for x, y in data_points],
                    color=config.get("color", ft.Colors.BLUE),
                    stroke_width=config.get("stroke_width", 2),
                    curved=config.get("curved", True),
                    stroke_cap_round=config.get("stroke_cap_round", True),
                )
            )
        
        chart = super().build()
        chart.data_series = chart_data
        return chart


def create_chart_container(
    chart: ft.Control,
    title: str = "",
    height: int = 250,
    width: int = 600
) -> ft.Container:
    """
    创建图表容器，包含标题和边框
    
    Args:
        chart: 图表组件
        title: 图表标题
        height: 容器高度
        width: 容器宽度
        
    Returns:
        包含图表的容器
    """
    content = []
    
    if title:
        content.append(
            ft.Text(title, style="titleMedium", weight=ft.FontWeight.BOLD)
        )
    
    content.append(chart)
    
    return ft.Container(
        content=ft.Column(content, spacing=10),
        padding=15,
        border=ft.border.all(1, ft.Colors.OUTLINE),
        border_radius=8,
        height=height,
        width=width,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK)
    )