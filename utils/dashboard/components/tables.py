"""
表格组件

提供数据表格组件，用于展示结构化数据。
"""

from typing import List, Dict, Any, Optional, Callable
import flet as ft


class DataTableComponent:
    """数据表格组件"""
    
    def __init__(
        self,
        columns: List[Dict[str, Any]],
        data: Optional[List[Dict[str, Any]]] = None,
        title: str = "",
        show_header: bool = True,
        border: bool = True,
        striped: bool = True,
        hoverable: bool = True,
        sortable: bool = False,
        pagination: bool = False,
        page_size: int = 10
    ):
        """
        初始化数据表格组件
        
        Args:
            columns: 列配置列表，每个配置包含key、label、width等
            data: 数据列表，每个元素为字典
            title: 表格标题
            show_header: 是否显示表头
            border: 是否显示边框
            striped: 是否显示斑马纹
            hoverable: 是否显示悬停效果
            sortable: 是否可排序
            pagination: 是否分页
            page_size: 每页显示行数
        """
        self.columns = columns
        self.data = data or []
        self.title = title
        self.show_header = show_header
        self.border = border
        self.striped = striped
        self.hoverable = hoverable
        self.sortable = sortable
        self.pagination = pagination
        self.page_size = page_size
        self.current_page = 1
        
        # 创建Flet列定义
        self.ft_columns = self._create_columns()
        self.ft_rows = self._create_rows()
        
    def _create_columns(self) -> List[ft.DataColumn]:
        """创建Flet列定义"""
        columns = []
        for col in self.columns:
            column = ft.DataColumn(
                label=ft.Text(col.get("label", "")),
                numeric=col.get("numeric", False),
                tooltip=col.get("tooltip", ""),
                on_sort=col.get("on_sort") if self.sortable else None
            )
            columns.append(column)
        return columns
    
    def _create_rows(self) -> List[ft.DataRow]:
        """创建Flet行数据"""
        rows = []
        
        # 计算分页范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.data[start_idx:end_idx] if self.pagination else self.data
        
        for i, row_data in enumerate(page_data):
            cells = []
            for col in self.columns:
                cell_key = col.get("key", "")
                cell_value = row_data.get(cell_key, "")
                
                # 处理单元格内容
                if isinstance(cell_value, ft.Control):
                    cell_content = cell_value
                else:
                    cell_content = ft.Text(str(cell_value))
                
                cells.append(ft.DataCell(cell_content))
            
            # 添加斑马纹效果
            color = None
            if self.striped and i % 2 == 0:
                color = ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
            
            row = ft.DataRow(
                cells=cells,
                color=color or row_data.get("row_color")
            )
            rows.append(row)
        
        return rows
    
    def update_data(self, new_data: List[Dict[str, Any]]) -> None:
        """更新表格数据"""
        self.data = new_data
        self.ft_rows = self._create_rows()
    
    def add_row(self, row_data: Dict[str, Any]) -> None:
        """添加一行数据"""
        self.data.append(row_data)
        self.ft_rows = self._create_rows()
    
    def remove_row(self, index: int) -> None:
        """移除一行数据"""
        if 0 <= index < len(self.data):
            self.data.pop(index)
            self.ft_rows = self._create_rows()
    
    def build(self) -> ft.DataTable:
        """构建表格组件"""
        table = ft.DataTable(
            columns=self.ft_columns,
            rows=self.ft_rows,
            show_checkbox_column=False,
            show_bottom_border=self.border,
            border=ft.border.all(1, ft.Colors.OUTLINE) if self.border else None,
            border_radius=5 if self.border else 0,
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE) if self.border else None,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE) if self.border else None,
            heading_row_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK) if self.show_header else None,
            heading_row_height=40,
            data_row_color={
                "hovered": ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
            } if self.hoverable else None,
            data_row_min_height=40,
            data_row_max_height=60,
            column_spacing=20,
            divider_thickness=1,
        )
        
        return table
    
    def build_with_container(self) -> ft.Container:
        """构建包含容器的表格"""
        content = []
        
        if self.title:
            content.append(
                ft.Text(self.title, style="titleMedium", weight=ft.FontWeight.BOLD)
            )
        
        content.append(self.build())
        
        # 添加分页控件
        if self.pagination and len(self.data) > self.page_size:
            total_pages = (len(self.data) + self.page_size - 1) // self.page_size
            pagination_row = self._create_pagination_controls(total_pages)
            content.append(pagination_row)
        
        return ft.Container(
            content=ft.Column(content, spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE) if self.border else None,
            border_radius=5 if self.border else 0,
        )
    
    def _create_pagination_controls(self, total_pages: int) -> ft.Row:
        """创建分页控件"""
        def go_to_page(page: int):
            if 1 <= page <= total_pages:
                self.current_page = page
                self.ft_rows = self._create_rows()
        
        page_info = ft.Text(f"第 {self.current_page} 页，共 {total_pages} 页")
        
        prev_button = ft.IconButton(
            icon=ft.Icons.NAVIGATE_BEFORE,
            on_click=lambda e: go_to_page(self.current_page - 1),
            disabled=self.current_page <= 1
        )
        
        next_button = ft.IconButton(
            icon=ft.Icons.NAVIGATE_NEXT,
            on_click=lambda e: go_to_page(self.current_page + 1),
            disabled=self.current_page >= total_pages
        )
        
        return ft.Row(
            [prev_button, page_info, next_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )


def create_table_with_header(
    columns: List[Dict[str, Any]],
    data: List[Dict[str, Any]],
    title: str = "",
    actions: Optional[List[ft.Control]] = None
) -> ft.Column:
    """
    创建带标题和操作按钮的表格
    
    Args:
        columns: 列配置
        data: 表格数据
        title: 表格标题
        actions: 操作按钮列表
        
    Returns:
        包含表格的列组件
    """
    content = []
    
    # 添加标题和操作按钮
    header_row = []
    if title:
        header_row.append(
            ft.Text(title, style="headlineMedium", expand=True)
        )
    
    if actions:
        header_row.append(
            ft.Row(actions, spacing=10)
        )
    
    if header_row:
        content.append(
            ft.Row(header_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
    
    # 创建表格
    table = DataTableComponent(columns=columns, data=data)
    content.append(table.build_with_container())
    
    return ft.Column(content, spacing=20)


def create_action_buttons(
    actions: List[Dict[str, Any]],
    spacing: int = 5
) -> ft.Row:
    """
    创建操作按钮行
    
    Args:
        actions: 操作配置列表，每个配置包含icon、on_click、tooltip等
        spacing: 按钮间距
        
    Returns:
        包含操作按钮的行
    """
    buttons = []
    
    for action in actions:
        icon = action.get("icon")
        on_click = action.get("on_click")
        tooltip = action.get("tooltip", "")
        color = action.get("color")
        
        button = ft.IconButton(
            icon=icon,
            on_click=on_click,
            tooltip=tooltip,
            icon_color=color,
            icon_size=20
        )
        buttons.append(button)
    
    return ft.Row(buttons, spacing=spacing)