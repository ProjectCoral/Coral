"""
适配器管理页面

显示和管理适配器信息。
"""

from typing import List, Dict, Any
import flet as ft

from ..components import DataTableComponent, create_table_with_header
from Coral import adapter_manager


class AdaptersPage:
    """适配器管理页面"""
    
    def __init__(self, dashboard):
        """
        初始化适配器页面
        
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
        # 创建表格
        columns = [
            {"key": "protocol", "label": "协议", "width": 150},
            {"key": "adapter", "label": "适配器", "width": 200},
            {"key": "status", "label": "状态", "width": 100},
            {"key": "drivers", "label": "关联驱动器", "width": 300}
        ]
        
        data = self._get_adapters_data()
        
        self.table = DataTableComponent(
            columns=columns,
            data=data,
            title="适配器列表",
            border=True,
            striped=True,
            hoverable=True
        )
        
        return create_table_with_header(
            columns=columns,
            data=data,
            title="适配器管理"
        )
    
    def _get_adapters_data(self) -> List[Dict[str, Any]]:
        """
        获取适配器数据
        
        Returns:
            适配器数据列表
        """
        data = []
        
        for protocol, adapter in adapter_manager.adapters.items():
            # 获取关联的驱动器
            drivers = ", ".join([driver.__class__.__name__ for driver in adapter.drivers])
            
            data.append({
                "protocol": protocol,
                "adapter": adapter.__class__.__name__,
                "status": ft.Text("运行中", color=ft.Colors.GREEN),
                "drivers": drivers
            })
        
        return data
    
    def update(self) -> None:
        """更新页面数据"""
        if self.table:
            new_data = self._get_adapters_data()
            self.table.update_data(new_data)