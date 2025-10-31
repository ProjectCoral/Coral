import os
import psutil
import asyncio
import threading
import time
import json
import logging
import flet as ft

from Coral import (
    config, event_bus, register, perm_system,
    plugin_manager, driver_manager, adapter_manager
)

from Coral.protocol import CommandEvent, MessageSegment, MessageChain, UserInfo

logger = logging.getLogger(__name__)

process = psutil.Process()

class CoralDashboard:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Coral Framework Dashboard"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.log_task = None
        self.memory_data = []
        self.cpu_data = []
        self.init_time = int(time.time())
        self.setup_ui()
        
        # 启动数据刷新线程
        self.refresh_thread = threading.Thread(target=self.data_refresh_loop, daemon=True)
        self.refresh_thread.start()
    
    def setup_ui(self):
        """初始化UI布局"""
        # 创建导航栏
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
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
            ],
            on_change=self.navigate
        )
        
        # 创建内容区域
        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        
        # 创建状态栏
        # self.status_bar = ft.Text("系统状态: 正在初始化...", style="bodySmall")
        self.status_bar = ft.Text("系统状态: 正在初始化...", style="bodySmall")
        
        # 主布局
        self.main_layout = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                ft.Column([self.content_area, ft.Divider(), self.status_bar], expand=True)
            ],
            expand=True
        )
        
        self.page.add(self.main_layout)
        self.load_overview()
    
    def navigate(self, e):
        """导航到不同页面"""
        index = self.nav_rail.selected_index
        self.content_area.controls.clear()
        
        if index == 0:
            self.load_overview()
        elif index == 1:
            self.load_plugins()
        elif index == 2:
            self.load_adapters()
        elif index == 3:
            self.load_drivers()
        elif index == 4:
            self.load_config()
        elif index == 5:
            self.load_permissions()
        elif index == 6:
            self.load_event_bus()
        elif index == 7:
            self.load_system_terminal()
        
        self.page.update()
    
    def data_refresh_loop(self):
        """数据刷新线程"""
        while True:
            try:
                # 在主线程中更新UI
                self.page.run_task(self.update_ui_data)
                time.sleep(2)
            except Exception as e:
                logger.exception(f"Dashboard refresh error: {e}")
                time.sleep(4)
    
    async def update_ui_data(self):
        """更新UI数据"""
        try:
            # 更新状态栏
            self.status_bar.value = (
                f"系统状态: 运行中 | "
                f"插件: {len(plugin_manager.plugins)} | "
                f"适配器: {len(adapter_manager.adapters)} | "
                f"驱动器: {len(driver_manager.drivers)} | "
                f"最后更新: {time.strftime('%H:%M:%S')}"
            )
            
            # 根据当前页面更新内容
            index = self.nav_rail.selected_index
            if index == 0:
                self.update_overview()
            elif index == 1:
                self.update_plugins()
            elif index == 2:
                self.update_adapters()
            elif index == 3:
                self.update_drivers()
            elif index == 6:
                self.update_event_bus()
            # elif index == 7:
            #     await self.update_system_terminal()
                
            self.page.update()
        except Exception as e:
            logger.exception(f"UI update error: {e}")
    
    # 以下是各个页面的实现
    def load_overview(self):
        """加载概览页面"""
        self.overview_cards = ft.Row(wrap=True, spacing=20)
        
        # 核心信息卡片
        core_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO),
                        title=ft.Text("核心信息"),
                    ),
                    ft.Divider(),
                    self.create_info_row("框架版本", config.config.get("coral_version", "N/A")),
                    self.create_info_row("协议版本", "1.0.1"),
                    self.create_info_row("插件管理器版本", plugin_manager.pluginmanager_version),
                    self.create_info_row("最后初始化时间", f"{config.config.get('last_init_time', 0):.2f}秒"),
                ]),
                padding=15
            )
        )
        
        # 系统状态卡片
        status_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.MONITOR_HEART),
                        title=ft.Text("系统状态"),
                    ),
                    ft.Divider(),
                    self.create_info_row("插件数量", len(plugin_manager.plugins)),
                    self.create_info_row("适配器数量", len(adapter_manager.adapters)),
                    self.create_info_row("驱动器数量", len(driver_manager.drivers)),
                    self.create_info_row("注册命令", len(register.commands)),
                    self.create_info_row("权限数量", len(perm_system.registered_perms)),
                ]),
                padding=15
            )
        )
        
        # 占用信息卡片
        usage_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.MEMORY),
                        title=ft.Text("占用信息"),
                    ),
                    ft.Divider(),
                    ft.Text(f"CPU使用率:", width=150, style="bodyMedium"),
                    self.cpu_chart(),
                    self.create_info_row("内存使用率", f"{psutil.virtual_memory().percent}%"),
                    self.memory_chart(),
                    self.create_info_row("磁盘使用率", f"{psutil.disk_usage('/').percent}%"),
                ]),
                padding=15
            )
        )

        # 操作卡片
        action_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.TOUCH_APP),
                        title=ft.Text("操作"),
                    ),
                    ft.Divider(),
                    ft.ElevatedButton("重新加载插件", on_click=self.reload_plugins),
                    ft.ElevatedButton("停止框架", on_click=self.stop_framework, color=ft.Colors.RED),
                ]),
                padding=15
            )
        )
        
        self.overview_cards.controls = [core_card, status_card, usage_card, action_card]
        self.content_area.controls = [
            ft.Text("系统概览", style="headlineMedium"), # headlineMedium
            self.overview_cards
        ]

    def cpu_chart(self):
        current_time = int(time.time())
        elapsed = current_time - self.init_time
        
        # 添加新数据点
        self.cpu_data.append((psutil.cpu_percent(), elapsed))
        
        # 保持最多60个数据点（1分钟）
        if len(self.cpu_data) > 30:
            self.cpu_data.pop(0)
            
        # 创建或更新图表数据
        chart_data = [
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x[1], x[0]) for x in self.cpu_data],
                color=ft.Colors.BLUE,
                stroke_width=2,
                curved=True
            )
        ]
        
        return ft.LineChart(
            data_series=chart_data,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(f"{i}%")
                    ) for i in range(0, 101, 10)
                ],
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(f"{i}s")
                    ) for i in range(self.cpu_data[0][1],self.cpu_data[0][1] + 61, 10)
                ],
                labels_size=40,
            ),
            height=200,
            width=600,
            min_y=0,
            max_y=100,
            min_x=self.cpu_data[0][1] if self.cpu_data else 0,
            max_x=self.cpu_data[0][1] + 60 if self.cpu_data else 60,
            expand=True,
        )

    def memory_chart(self):
        current_time = int(time.time())
        elapsed = current_time - self.init_time
        
        # 添加新数据点
        self.memory_data.append((process.memory_info().rss, process.memory_info().vms, elapsed))
        
        # 保持最多60个数据点（1分钟）
        if len(self.memory_data) > 30:
            self.memory_data.pop(0)
            
        # 创建或更新图表数据
        chart_data = [
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x[2], x[0]/1024/1024) for x in self.memory_data],
                color=ft.Colors.BLUE,
                stroke_width=2,
                curved=True
            ),
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x[2], x[1]/1024/1024) for x in self.memory_data],
                color=ft.Colors.RED,
                stroke_width=2,
                curved=True
            )
        ]
        
        # 创建或更新Y轴标签
        max_memory = max([x[0] for x in self.memory_data + self.memory_data]) if self.memory_data else 100
        max_mb = (max_memory // 1024 // 1024) + 100  # 向上取整到最近的100MB
        
        return ft.LineChart(
            data_series=chart_data,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(f"{i}M")
                    ) for i in range(0, int(max_mb), 100)
                ],
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Text(f"{i}s")
                    ) for i in range(self.memory_data[0][2],self.memory_data[0][2] + 61, 10)
                ],
                labels_size=40,
            ),
            height=200,
            width=600,
            min_y=0,
            max_y=max_mb,
            min_x=self.memory_data[0][2] if self.memory_data else 0,
            max_x=self.memory_data[0][2] + 60 if self.memory_data else 60,
            expand=True,
        )

    def update_overview(self):
        """更新概览页面数据"""
        if self.overview_cards and len(self.overview_cards.controls) >= 3:
            # 更新系统状态卡片
            status_card = self.overview_cards.controls[1]
            status_content = status_card.content.content
            status_content.controls[2] = self.create_info_row("插件数量", len(plugin_manager.plugins))
            status_content.controls[3] = self.create_info_row("适配器数量", len(adapter_manager.adapters))
            status_content.controls[4] = self.create_info_row("驱动器数量", len(driver_manager.drivers))
            status_content.controls[5] = self.create_info_row("注册命令", len(register.commands))
            status_content.controls[6] = self.create_info_row("权限数量", len(perm_system.registered_perms))

            # 更新占用信息卡片
            usage_card = self.overview_cards.controls[2]
            usage_content = usage_card.content.content
            usage_content.controls[2] = ft.Text(f"CPU使用率:", width=150, style="bodyMedium")
            usage_content.controls[3] = self.cpu_chart()
            usage_content.controls[4] = self.create_info_row("内存使用率", f"{psutil.virtual_memory().percent}%")
            usage_content.controls[5] = self.memory_chart()
            usage_content.controls[6] = self.create_info_row("磁盘使用率", f"{psutil.disk_usage('/').percent}%")
    
    def load_plugins(self):
        """加载插件页面"""
        self.plugins_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("插件名称")),
                ft.DataColumn(ft.Text("兼容性")),
                ft.DataColumn(ft.Text("状态")),
                ft.DataColumn(ft.Text("操作")),
            ],
            rows=[]
        )
        
        self.update_plugins()
        
        self.content_area.controls = [
            ft.Text("插件管理", style="headlineMedium"),
            ft.Row([
                ft.ElevatedButton("重新加载所有插件", on_click=self.reload_plugins),
                ft.ElevatedButton("安装依赖", on_click=self.install_dependencies),
            ], spacing=10),
            ft.Container(
                content=self.plugins_data,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            )
        ]
    
    def update_plugins(self):
        """更新插件数据"""
        if not hasattr(self, 'plugins_data'):
            return
            
        self.plugins_data.rows = []
        for plugin in plugin_manager.plugins:
            meta = plugin_manager.get_plugin_meta(f"./plugins/{plugin}/__init__.py")
            compatibility = meta.get("compatibility", "N/A") if meta else "N/A"
            
            self.plugins_data.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(plugin)),
                        ft.DataCell(ft.Text(str(compatibility))),
                        ft.DataCell(ft.Text("已加载", color=ft.Colors.GREEN)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(ft.Icons.REFRESH, on_click=lambda e, p=plugin: self.reload_single_plugin(p)),
                                ft.IconButton(ft.Icons.INFO, on_click=lambda e, p=plugin: self.show_plugin_info(p)),
                            ], spacing=5)
                        ),
                    ]
                )
            )
    
    def load_adapters(self):
        """加载适配器页面"""
        self.adapters_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("协议")),
                ft.DataColumn(ft.Text("适配器")),
                ft.DataColumn(ft.Text("状态")),
                ft.DataColumn(ft.Text("关联驱动器")),
            ],
            rows=[]
        )
        
        self.update_adapters()
        
        self.content_area.controls = [
            ft.Text("适配器管理", style="headlineMedium"),
            ft.Container(
                content=self.adapters_data,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            )
        ]
    
    def update_adapters(self):
        """更新适配器数据"""
        if not hasattr(self, 'adapters_data'):
            return
            
        self.adapters_data.rows = []
        for protocol, adapter in adapter_manager.adapters.items():
            drivers = ", ".join([driver.__class__.__name__ for driver in adapter.drivers])
            
            self.adapters_data.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(protocol)),
                        ft.DataCell(ft.Text(adapter.__class__.__name__)),
                        ft.DataCell(ft.Text("运行中", color=ft.Colors.GREEN)),
                        ft.DataCell(ft.Text(drivers)),
                    ]
                )
            )
    
    def load_drivers(self):
        """加载驱动器页面"""
        self.drivers_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("名称")),
                ft.DataColumn(ft.Text("类型")),
                ft.DataColumn(ft.Text("状态")),
                ft.DataColumn(ft.Text("操作")),
            ],
            rows=[]
        )
        
        self.update_drivers()
        
        self.content_area.controls = [
            ft.Text("驱动器管理", style="headlineMedium"),
            ft.Row([
                ft.ElevatedButton("启动所有驱动器", on_click=self.start_drivers),
                ft.ElevatedButton("停止所有驱动器", on_click=self.stop_drivers),
            ], spacing=10),
            ft.Container(
                content=self.drivers_data,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            )
        ]
    
    def update_drivers(self):
        """更新驱动器数据"""
        if not hasattr(self, 'drivers_data'):
            return
            
        self.drivers_data.rows = []
        for name, driver in driver_manager.drivers.items():
            status = "运行中" if driver._running else "已停止"
            color = ft.Colors.GREEN if driver._running else ft.Colors.RED
            
            self.drivers_data.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(name)),
                        ft.DataCell(ft.Text(driver.__class__.__name__)),
                        ft.DataCell(ft.Text(status, color=color)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.PLAY_ARROW if not driver._running else ft.Icons.PAUSE,
                                    on_click=lambda e, d=driver: asyncio.run_coroutine_threadsafe(self.toggle_driver(d), asyncio.new_event_loop())
                                ),
                                ft.IconButton(ft.Icons.INFO, on_click=lambda e, d=driver: asyncio.run_coroutine_threadsafe(self.show_driver_info(d), asyncio.new_event_loop())),
                            ], spacing=5)
                        ),
                    ]
                )
            )
    
    def load_config(self):
        """加载配置页面"""
        self.config_view = ft.Column()
        
        try:
            config_data = json.dumps(config.config, indent=4)
            self.config_editor = ft.TextField(
                value=config_data,
                multiline=True,
                min_lines=30,
                max_lines=30,
                text_size=14,
                border_color=ft.Colors.OUTLINE
            )
        except:
            self.config_editor = ft.Text("无法加载配置", color=ft.Colors.RED)
        
        self.content_area.controls = [
            ft.Text("框架配置", style="headlineMedium"),
            ft.Row([
                ft.ElevatedButton("保存配置", on_click=self.save_config),
                ft.ElevatedButton("重新加载配置", on_click=self.reload_config),
            ], spacing=10),
            ft.Container(
                content=self.config_editor,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            )
        ]
    
    def load_permissions(self):
        """加载权限页面"""
        self.perms_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("权限名称")),
                ft.DataColumn(ft.Text("描述")),
                ft.DataColumn(ft.Text("用户/组")),
            ],
            rows=[]
        )
        
        self.update_permissions()
        
        self.content_area.controls = [
            ft.Text("权限管理", style="headlineMedium"),
            ft.Row([
                ft.ElevatedButton("添加权限", on_click=self.add_permission),
                ft.ElevatedButton("刷新", on_click=self.update_permissions),
            ], spacing=10),
            ft.Container(
                content=self.perms_data,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            )
        ]
    
    def update_permissions(self, e=None):
        """更新权限数据"""
        if not hasattr(self, 'perms_data'):
            return
            
        self.perms_data.rows = []
        for perm_name, perm_desc in perm_system.registered_perms.items():
            # 获取拥有此权限的用户/组
            users = []
            for user, perms in perm_system.user_perms.items():
                for perm in perms:
                    if isinstance(perm, tuple) and perm[0] == perm_name:
                        users.append(f"用户 {user} (组 {perm[1]})")
                    elif perm == perm_name:
                        users.append(f"组 {user}")
            
            self.perms_data.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(perm_name)),
                        ft.DataCell(ft.Text(perm_desc)),
                        ft.DataCell(ft.Text("\n".join(users) if users else "无")),
                    ]
                )
            )
        
        if e:
            self.page.update()
    
    def load_event_bus(self):
        """加载事件总线页面"""
        self.events_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("事件类型")),
                ft.DataColumn(ft.Text("处理器数量")),
                ft.DataColumn(ft.Text("最后活动时间")),
            ],
            rows=[]
        )
        
        self.events_log = ft.Column(height=300, scroll=ft.ScrollMode.ALWAYS)
        
        self.update_event_bus()
        
        self.content_area.controls = [
            ft.Text("事件总线监控", style="headlineMedium"),
            ft.Container(
                content=self.events_data,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5
            ),
            ft.Text("最近事件", style="titleMedium"),
            ft.Container(
                content=self.events_log,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                height=300
            )
        ]

    def load_system_terminal(self):
        """加载系统终端页面"""
        if self.log_task and not self.log_task.done():
            self.log_task.cancel()
        
        self.system_terminal = ft.ListView(
            height=440,        # 设置高度
            width=1200,         # 设置宽度
            spacing=0,         # 行间距
            padding=0,         # 内边距
            auto_scroll=True,  # 自动滚动到最新一行
        )

        # 异步启动日志更新
        self.log_task = self.page.loop.create_task(self.update_system_terminal())

        # 更新页面内容
        self.content_area.controls = [
            ft.Text("系统终端", style="headlineMedium"),
            self.system_terminal,
            ft.TextField(
                label="命令",
                hint_text="输入要执行的命令",
                on_submit=lambda e: self.execute_system_command(e),
                width=1000
                ),
        ]

    def execute_system_command(self, e):
        """执行系统命令"""
        if not hasattr(self,'system_terminal'):
            return
        command = e.control.value
        if not command:
            return
        
        command, args = command.split(" ", 1) if " " in command else (command, "")

        args = args.split() if args else []

        task = self.page.loop.create_task(
                register.execute_command(
                    CommandEvent(
                        event_id=f"console-{time.time()}",
                        platform="console",
                        self_id="Console",
                        command=command,
                        raw_message=MessageChain([MessageSegment.text("stop")]),
                        user=UserInfo(
                            platform="system",
                            user_id="Console"
                        ),
                        args=args,
                    )
                )
            )
        while not task.done():
            time.sleep(0.01)
        
        result = task.result()

        result = result.message.to_plain_text() if result.message else "命令执行失败"

        for line in result.split('\n'):
            self.system_terminal.controls.append(ft.Text(line.strip(), size=14, font_family="Cascadia Mono"))

        e.control.value = "" 

    async def update_system_terminal(self):
        """异步更新系统终端数据"""
        if not hasattr(self, 'system_terminal'):
            return

        max_lines = 1000  # 最大显示行数
        try:
            async for line in self.read_log():
                text = ft.Text(line.strip(), size=14, font_family="Cascadia Mono")
                self.system_terminal.controls.append(text)
                # 如果超过最大行数，删除最旧的行
                if len(self.system_terminal.controls) > max_lines:
                    self.system_terminal.controls.pop(0)
                self.page.update()
        except asyncio.CancelledError:
            pass
    
    async def read_log(self):
        """异步读取日志"""
        log_files = [file for file in os.listdir("./logs") 
                     if file.startswith("Coral_") and file.endswith(".log")]
        log_files.sort(reverse=True)
        
        try:
            with open(f"./logs/{log_files[0]}", "r", encoding="utf-8") as f:
                # 先读取已有内容
                for line in f:
                    yield line
                    
                # 持续监控新内容
                while True:
                    where = f.tell()
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                        f.seek(where)
                    else:
                        yield line
        except Exception as e:
            logger.error(f"Log read error: {e}")

    def update_event_bus(self):
        """更新事件总线数据"""
        if not hasattr(self, 'events_data'):
            return
            
        # 更新事件类型表格
        self.events_data.rows = []
        for event_type, handlers in event_bus._subscribers.items():
            self.events_data.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(event_type.__name__)),
                        ft.DataCell(ft.Text(str(len(handlers)))),
                        ft.DataCell(ft.Text(time.strftime('%H:%M:%S'))),
                    ]
                )
            )
    
    def add_event_log(self, event):
        """添加事件日志"""
        if not hasattr(self, 'events_log'):
            return
            
        self.events_log.controls.insert(
            0,
            ft.Text(f"[{time.strftime('%H:%M:%S')}] {event.__class__.__name__}", style="bodySmall")
        )
        
        # 限制日志数量
        if len(self.events_log.controls) > 50:
            self.events_log.controls.pop()
    
    # 以下是UI辅助方法
    def create_info_row(self, label, value):
        """创建信息行"""
        return ft.Row(
            controls=[
                ft.Text(f"{label}:", width=150, style="bodyMedium"),
                ft.Text(value, style="bodyMedium")
            ]
        )
    
    # 以下是操作处理方法
    async def reload_plugins(self, e):
        """重新加载所有插件"""
        asyncio.run_coroutine_threadsafe(plugin_manager.reload_plugins(), asyncio.get_event_loop())
        self.status_bar.value = "正在重新加载插件..."
        self.page.update()
    
    async def reload_single_plugin(self, plugin_name):
        """重新加载单个插件"""
        asyncio.run_coroutine_threadsafe(plugin_manager.reload_plugin(plugin_name), asyncio.get_event_loop())
        self.status_bar.value = f"正在重新加载插件: {plugin_name}"
        self.page.update()
    
    async def install_dependencies(self, e):
        """安装依赖"""
        self.status_bar.value = "正在检查并安装依赖..."
        self.page.update()
        # 这里需要实现实际的依赖安装逻辑
    
    async def stop_framework(self, e):
        """停止框架"""
        if await self.show_confirmation_dialog("确认停止", "确定要停止Coral框架吗？"):
            asyncio.run_coroutine_threadsafe(
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
                asyncio.get_event_loop())
            self.status_bar.value = "框架正在停止..."
            self.page.update()
    
    async def start_drivers(self, e):
        """启动所有驱动器"""
        asyncio.run_coroutine_threadsafe(driver_manager.start_all(), asyncio.get_event_loop())
        self.status_bar.value = "正在启动所有驱动器..."
        self.page.update()
    
    async def stop_drivers(self, e):
        """停止所有驱动器"""
        asyncio.run_coroutine_threadsafe(driver_manager.stop_all(), asyncio.get_event_loop())
        self.status_bar.value = "正在停止所有驱动器..."
        self.page.update()
    
    async def toggle_driver(self, driver):
        """切换驱动器状态"""
        if driver._running:
            asyncio.run_coroutine_threadsafe(driver.stop(), asyncio.get_event_loop())
        else:
            asyncio.run_coroutine_threadsafe(driver.start(), asyncio.get_event_loop())
    
    async def save_config(self, e):
        """保存配置"""
        try:
            new_config = json.loads(self.config_editor.value)
            config.config = new_config
            config.save()
            self.status_bar.value = "配置已保存"
        except Exception as e:
            self.status_bar.value = f"保存失败: {str(e)}"
        self.page.update()
    
    async def reload_config(self, e):
        """重新加载配置"""
        config.load_config(config.main_config)
        self.config_editor.value = json.dumps(config.config, indent=4)
        self.page.update()
    
    async def add_permission(self, e):
        """添加权限"""
        
        permission_name = await self.show_input_dialog("添加权限", "请输入权限名称:")
        if not permission_name or permission_name not in perm_system.registered_perms:
            self.status_bar.value = "权限名称为空或不存在"
            self.page.update()
            return
        
        
        permission_user = await self.show_input_dialog("添加权限", "请输入用户:")
        if not permission_user:
            self.status_bar.value = "用户为空"
            self.page.update()
            return
        
        permission_group = await self.show_input_dialog("添加权限", "请输入组(可选):")
        if not permission_group:
            permission_group = -1

        command = f"{permission_name} {permission_user} {permission_group}"
        result = perm_system.add_perm(command)
        self.status_bar.value = result
        self.update_permissions()
        self.page.update()
    
    async def show_plugin_info(self, plugin_name):
        """显示插件详情"""
        # TODO实现插件详情的UI逻辑
        pass
    
    async def show_driver_info(self, driver):
        """显示驱动器详情"""
        # TODO实现驱动器详情的UI逻辑
        pass
    
    async def show_input_dialog(self, title, message):
        """显示输入对话框"""
        input_value = None
        text_field = ft.TextField(label="输入内容") 
        
        def close_dialog(e):
            nonlocal input_value
            input_value = text_field.value if e.control.data == "true" else None
            dlg_modal.open = False
            self.page.update()
        
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                text_field,
                ft.TextButton("确定", data="true", on_click=close_dialog),
                ft.TextButton("取消", data="false", on_click=close_dialog),
            ],
        )
        
        self.page.overlay.append(dlg_modal)
        dlg_modal.open = True
        self.page.update()
        
        # 等待对话框关闭
        while dlg_modal.open:
            await asyncio.sleep(0.1)

        return input_value

    async def show_confirmation_dialog(self, title, message):
        """显示确认对话框"""
        confirm = False
        
        def close_dialog(e):
            nonlocal confirm
            confirm = e.control.data == "true"  # 直接从按钮的data属性获取
            dlg_modal.open = False
            self.page.update()
        
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("确定", data="true", on_click=close_dialog),  # 直接传递函数引用
                ft.TextButton("取消", data="false", on_click=close_dialog),
            ],
        )
        
        self.page.overlay.append(dlg_modal)
        dlg_modal.open = True
        self.page.update()
        
        # 等待对话框关闭
        while dlg_modal.open:
            await asyncio.sleep(0.1)
        
        return confirm
def dashboard(page: ft.Page):
    page.title = "Coral Dashboard"
    CoralDashboard(page)

async def run_dashboard(dashboard_config: dict):
    logger.info("Starting Coral Dashboard...")
    if dashboard_config.get("listen", True):
        host = "0.0.0.0"
    else:
        host = "127.0.0.1"
    port = dashboard_config.get("port", 9000)
    await ft.app_async(
        target=dashboard,
        use_color_emoji=True,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=port
    )
