"""
对话框组件

提供各种类型的对话框组件，用于用户交互。
"""

from typing import Optional, Callable, Any
import flet as ft


class ConfirmationDialog:
    """确认对话框"""
    
    def __init__(
        self,
        page: ft.Page,
        title: str = "确认",
        message: str = "确定要执行此操作吗？",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        confirm_color: str = ft.Colors.RED,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        """
        初始化确认对话框
        
        Args:
            page: Flet页面对象
            title: 对话框标题
            message: 对话框消息
            confirm_text: 确认按钮文本
            cancel_text: 取消按钮文本
            confirm_color: 确认按钮颜色
            on_confirm: 确认回调函数
            on_cancel: 取消回调函数
        """
        self.page = page
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.confirm_color = confirm_color
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.dialog = None
        self.result = None
        
    def _create_dialog(self) -> ft.AlertDialog:
        """创建对话框组件"""
        
        def handle_confirm(e):
            self.dialog.open = False
            self.result = True
            self.page.update()
            if self.on_confirm:
                self.on_confirm(e)
        
        def handle_cancel(e):
            self.dialog.open = False
            self.result = False
            self.page.update()
            if self.on_cancel:
                self.on_cancel(e)
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.title),
            content=ft.Text(self.message),
            actions=[
                ft.TextButton(
                    self.confirm_text,
                    on_click=handle_confirm,
                    style=ft.ButtonStyle(color=self.confirm_color)
                ),
                ft.TextButton(
                    self.cancel_text,
                    on_click=handle_cancel
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return self.dialog
    
    async def show(self) -> bool:
        """
        显示对话框并等待结果
        
        Returns:
            bool: 用户是否确认
        """
        dialog = self._create_dialog()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
        # 等待对话框关闭
        while dialog.open:
            await asyncio.sleep(0.1)
        
        # 从overlay中移除对话框
        self.page.overlay.remove(dialog)
        self.page.update()
        
        return self.result


class InputDialog:
    """输入对话框"""
    
    def __init__(
        self,
        page: ft.Page,
        title: str = "输入",
        message: str = "请输入内容:",
        default_value: str = "",
        hint_text: str = "",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        multiline: bool = False,
        on_confirm: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable] = None
    ):
        """
        初始化输入对话框
        
        Args:
            page: Flet页面对象
            title: 对话框标题
            message: 对话框消息
            default_value: 默认值
            hint_text: 提示文本
            confirm_text: 确认按钮文本
            cancel_text: 取消按钮文本
            multiline: 是否多行输入
            on_confirm: 确认回调函数，接收输入值
            on_cancel: 取消回调函数
        """
        self.page = page
        self.title = title
        self.message = message
        self.default_value = default_value
        self.hint_text = hint_text
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.multiline = multiline
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.dialog = None
        self.result = None
        self.input_field = None
        
    def _create_dialog(self) -> ft.AlertDialog:
        """创建对话框组件"""
        
        def handle_confirm(e):
            self.dialog.open = False
            self.result = self.input_field.value
            self.page.update()
            if self.on_confirm and self.result is not None:
                self.on_confirm(self.result)
        
        def handle_cancel(e):
            self.dialog.open = False
            self.result = None
            self.page.update()
            if self.on_cancel:
                self.on_cancel(e)
        
        # 创建输入字段
        self.input_field = ft.TextField(
            value=self.default_value,
            hint_text=self.hint_text,
            multiline=self.multiline,
            min_lines=1 if not self.multiline else 3,
            max_lines=1 if not self.multiline else 10,
            autofocus=True,
            on_submit=handle_confirm if not self.multiline else None
        )
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.title),
            content=ft.Column([
                ft.Text(self.message),
                self.input_field
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton(
                    self.confirm_text,
                    on_click=handle_confirm
                ),
                ft.TextButton(
                    self.cancel_text,
                    on_click=handle_cancel
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return self.dialog
    
    async def show(self) -> Optional[str]:
        """
        显示对话框并等待结果
        
        Returns:
            Optional[str]: 用户输入的值，如果取消则为None
        """
        dialog = self._create_dialog()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
        # 等待对话框关闭
        while dialog.open:
            await asyncio.sleep(0.1)
        
        # 从overlay中移除对话框
        self.page.overlay.remove(dialog)
        self.page.update()
        
        return self.result


class AlertDialog:
    """警告/信息对话框"""
    
    def __init__(
        self,
        page: ft.Page,
        title: str = "提示",
        message: str = "",
        alert_type: str = "info",  # info, warning, error, success
        button_text: str = "确定",
        on_close: Optional[Callable] = None
    ):
        """
        初始化警告对话框
        
        Args:
            page: Flet页面对象
            title: 对话框标题
            message: 对话框消息
            alert_type: 对话框类型
            button_text: 按钮文本
            on_close: 关闭回调函数
        """
        self.page = page
        self.title = title
        self.message = message
        self.alert_type = alert_type
        self.button_text = button_text
        self.on_close = on_close
        self.dialog = None
        
        # 根据类型设置图标和颜色
        self._setup_style()
        
    def _setup_style(self):
        """根据类型设置样式"""
        if self.alert_type == "warning":
            self.icon = ft.Icons.WARNING_AMBER
            self.icon_color = ft.Colors.AMBER
        elif self.alert_type == "error":
            self.icon = ft.Icons.ERROR
            self.icon_color = ft.Colors.RED
        elif self.alert_type == "success":
            self.icon = ft.Icons.CHECK_CIRCLE
            self.icon_color = ft.Colors.GREEN
        else:  # info
            self.icon = ft.Icons.INFO
            self.icon_color = ft.Colors.BLUE
            
    def _create_dialog(self) -> ft.AlertDialog:
        """创建对话框组件"""
        
        def handle_close(e):
            self.dialog.open = False
            self.page.update()
            if self.on_close:
                self.on_close(e)
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(self.icon, color=self.icon_color),
                ft.Text(self.title, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(self.message),
            actions=[
                ft.TextButton(
                    self.button_text,
                    on_click=handle_close
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        return self.dialog
    
    async def show(self):
        """显示对话框"""
        dialog = self._create_dialog()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
        # 等待对话框关闭
        while dialog.open:
            await asyncio.sleep(0.1)
        
        # 从overlay中移除对话框
        self.page.overlay.remove(dialog)
        self.page.update()


class ProgressDialog:
    """进度对话框"""
    
    def __init__(
        self,
        page: ft.Page,
        title: str = "处理中",
        message: str = "请稍候...",
        indeterminate: bool = True,
        value: float = 0.0
    ):
        """
        初始化进度对话框
        
        Args:
            page: Flet页面对象
            title: 对话框标题
            message: 对话框消息
            indeterminate: 是否不确定进度
            value: 进度值（0.0-1.0）
        """
        self.page = page
        self.title = title
        self.message = message
        self.indeterminate = indeterminate
        self.value = value
        self.dialog = None
        self.progress_bar = None
        
    def _create_dialog(self) -> ft.AlertDialog:
        """创建对话框组件"""
        
        if self.indeterminate:
            self.progress_bar = ft.ProgressBar()
        else:
            self.progress_bar = ft.ProgressBar(value=self.value)
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.title),
            content=ft.Column([
                ft.Text(self.message),
                self.progress_bar
            ], tight=True, spacing=10),
            actions=[],
        )
        
        return self.dialog
    
    def show(self):
        """显示对话框"""
        dialog = self._create_dialog()
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        return dialog
    
    def update_progress(self, value: float = None, message: str = None):
        """更新进度"""
        if value is not None and not self.indeterminate:
            self.progress_bar.value = value
        if message is not None:
            # 更新消息需要重新创建对话框内容
            pass
        self.page.update()
    
    def close(self):
        """关闭对话框"""
        if self.dialog:
            self.dialog.open = False
            self.page.overlay.remove(self.dialog)
            self.page.update()


# 导入asyncio用于异步操作
import asyncio