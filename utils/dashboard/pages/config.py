"""
配置页面

显示和编辑框架配置。
"""

import json
import flet as ft

from Coral import config


class ConfigPage:
    """配置页面"""
    
    def __init__(self, dashboard):
        """
        初始化配置页面
        
        Args:
            dashboard: Dashboard主类实例
        """
        self.dashboard = dashboard
        self.config_editor = None
        
    def load(self) -> ft.Column:
        """
        加载页面内容
        
        Returns:
            页面内容列组件
        """
        content = ft.Column(spacing=20)
        
        # 页面标题
        content.controls.append(
            ft.Text("框架配置", style="headlineMedium")
        )
        
        # 操作按钮
        actions = ft.Row([
            ft.ElevatedButton(
                "保存配置",
                on_click=self._save_config,
                icon=ft.Icons.SAVE
            ),
            ft.ElevatedButton(
                "重新加载配置",
                on_click=self._reload_config,
                icon=ft.Icons.REFRESH
            )
        ], spacing=10)
        
        content.controls.append(actions)
        
        # 配置编辑器
        try:
            config_data = json.dumps(config.config, indent=4, ensure_ascii=False)
            self.config_editor = ft.TextField(
                value=config_data,
                multiline=True,
                min_lines=30,
                max_lines=30,
                text_size=14,
                border_color=ft.Colors.OUTLINE,
                border_radius=5,
                content_padding=10
            )
        except Exception as e:
            self.config_editor = ft.Text(
                f"无法加载配置: {str(e)}",
                color=ft.Colors.RED
            )
        
        editor_container = ft.Container(
            content=self.config_editor,
            padding=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            expand=True
        )
        
        content.controls.append(editor_container)
        
        return content
    
    def update(self) -> None:
        """更新页面数据"""
        # 配置页面通常不需要自动更新
        pass
    
    async def _save_config(self, e) -> None:
        """保存配置"""
        if not isinstance(self.config_editor, ft.TextField):
            alert = self.dashboard.show_alert_dialog(
                title="保存失败",
                message="配置编辑器未正确初始化",
                alert_type="error"
            )
            await alert.show()
            return
        
        try:
            new_config = json.loads(self.config_editor.value)
            config.config = new_config
            config.save()
            
            alert = self.dashboard.show_alert_dialog(
                title="保存成功",
                message="配置已保存",
                alert_type="success"
            )
            await alert.show()
        except json.JSONDecodeError as e:
            alert = self.dashboard.show_alert_dialog(
                title="保存失败",
                message=f"JSON格式错误: {str(e)}",
                alert_type="error"
            )
            await alert.show()
        except Exception as e:
            alert = self.dashboard.show_alert_dialog(
                title="保存失败",
                message=f"保存配置时出错: {str(e)}",
                alert_type="error"
            )
            await alert.show()
    
    async def _reload_config(self, e) -> None:
        """重新加载配置"""
        try:
            config.load_config(config.main_config)
            config_data = json.dumps(config.config, indent=4, ensure_ascii=False)
            
            if isinstance(self.config_editor, ft.TextField):
                self.config_editor.value = config_data
                self.dashboard.page.update()
                
                alert = self.dashboard.show_alert_dialog(
                    title="重新加载成功",
                    message="配置已重新加载",
                    alert_type="success"
                )
                await alert.show()
        except Exception as e:
            alert = self.dashboard.show_alert_dialog(
                title="重新加载失败",
                message=f"重新加载配置时出错: {str(e)}",
                alert_type="error"
            )
            await alert.show()