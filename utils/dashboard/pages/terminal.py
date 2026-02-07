"""
系统终端页面

显示系统日志和执行命令。
"""

import os
import asyncio
import flet as ft

from Coral.protocol import CommandEvent, MessageChain, MessageSegment, UserInfo
from Coral import register


class TerminalPage:
    """系统终端页面"""
    
    def __init__(self, dashboard):
        """
        初始化终端页面
        
        Args:
            dashboard: Dashboard主类实例
        """
        self.dashboard = dashboard
        self.terminal_output = None
        self.command_input = None
        self.log_task = None
        
    def load(self) -> ft.Column:
        """
        加载页面内容
        
        Returns:
            页面内容列组件
        """
        content = ft.Column(spacing=20)
        
        # 页面标题
        content.controls.append(
            ft.Text("系统终端", style="headlineMedium")
        )
        
        # 终端输出区域
        self.terminal_output = ft.ListView(
            height=400,
            spacing=0,
            padding=0,
            auto_scroll=True
        )
        
        output_container = ft.Container(
            content=self.terminal_output,
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            height=400,
            bgcolor=ft.Colors.BLACK
        )
        
        content.controls.append(output_container)
        
        # 命令输入区域
        self.command_input = ft.TextField(
            label="命令",
            hint_text="输入要执行的命令",
            on_submit=self._execute_command,
            prefix_icon=ft.Icons.TERMINAL,
            border_radius=5,
            expand=True
        )
        
        input_row = ft.Row([
            self.command_input,
            ft.IconButton(
                icon=ft.Icons.SEND,
                on_click=self._execute_command,
                tooltip="执行命令"
            )
        ], spacing=10)
        
        content.controls.append(input_row)
        
        # 启动日志监控
        self._start_log_monitor()
        
        return content
    
    def _start_log_monitor(self) -> None:
        """启动日志监控"""
        if self.log_task and not self.log_task.done():
            self.log_task.cancel()
        
        self.log_task = self.dashboard.page.loop.create_task(
            self._monitor_logs()
        )
    
    async def _monitor_logs(self) -> None:
        """监控日志文件"""
        try:
            # 查找最新的日志文件
            log_files = self._get_log_files()
            if not log_files:
                self._add_terminal_line("未找到日志文件", color=ft.Colors.YELLOW)
                return
            
            latest_log = log_files[0]
            log_path = f"./logs/{latest_log}"
            
            # 读取现有日志
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        self._add_terminal_line(line.strip())
            
            # 监控新日志（简化版本）
            # 在实际实现中，这里应该使用文件监控
            self._add_terminal_line("日志监控已启动", color=ft.Colors.GREEN)
            
        except Exception as e:
            self._add_terminal_line(f"日志监控错误: {str(e)}", color=ft.Colors.RED)
    
    def _get_log_files(self) -> list:
        """获取日志文件列表"""
        try:
            if not os.path.exists("./logs"):
                return []
            
            log_files = [
                f for f in os.listdir("./logs")
                if f.startswith("Coral_") and f.endswith(".log")
            ]
            log_files.sort(reverse=True)
            return log_files
        except Exception:
            return []
    
    def _add_terminal_line(self, text: str, color: str = ft.Colors.WHITE) -> None:
        """
        添加终端行
        
        Args:
            text: 文本内容
            color: 文本颜色
        """
        if not self.terminal_output:
            return
        
        line = ft.Text(
            text,
            size=12,
            font_family="Cascadia Mono",
            color=color,
            selectable=True
        )
        
        self.terminal_output.controls.append(line)
        
        # 限制行数
        if len(self.terminal_output.controls) > 1000:
            self.terminal_output.controls.pop(0)
        
        self.dashboard.page.update()
    
    async def _execute_command(self, e) -> None:
        """执行命令"""
        if not self.command_input or not self.command_input.value:
            return
        
        command = self.command_input.value.strip()
        self.command_input.value = ""
        
        # 显示命令
        self._add_terminal_line(f"> {command}", color=ft.Colors.CYAN)
        
        try:
            # 解析命令
            parts = command.split()
            if not parts:
                return
            
            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # 执行命令
            result = await register.execute_command(
                CommandEvent(
                    event_id=f"console-{asyncio.get_event_loop().time()}",
                    platform="console",
                    self_id="Console",
                    command=cmd,
                    raw_message=MessageChain([MessageSegment.text(command)]),
                    user=UserInfo(
                        platform="system",
                        user_id="Console"
                    ),
                    args=args
                )
            )
            
            # 显示结果
            if result and result.message:
                output = result.message.to_plain_text()
                for line in output.split('\n'):
                    self._add_terminal_line(line.strip())
            else:
                self._add_terminal_line("命令执行完成", color=ft.Colors.GREEN)
                
        except Exception as ex:
            self._add_terminal_line(f"命令执行错误: {str(ex)}", color=ft.Colors.RED)
        
        self.dashboard.page.update()
    
    def update(self) -> None:
        """更新页面数据"""
        # 终端页面通常不需要自动更新
        pass
    
    def cleanup(self) -> None:
        """清理资源"""
        if self.log_task and not self.log_task.done():
            self.log_task.cancel()