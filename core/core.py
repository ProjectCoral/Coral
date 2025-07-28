import sys
import os
import re
import datetime
import logging
import random
from rich.console import Console
from rich.traceback import Traceback
import traceback
from io import StringIO

from .plugin_manager import PLUGINMANAGER_VERSION
from .protocol import PROTOCOL_VERSION

logger = logging.getLogger(__name__)

CORAL_VERSION = "250610_early_development"
PLUGIN_DIR = "./plugins"
CONFIG_FILE = "./config.json"

def walklevel(path=".", max_depth=None):
    # 初始化队列和层级计数器
    queue = [(path, 0)]
    while queue:
        current_path, depth = queue.pop(0)
        if max_depth is not None and depth > max_depth:
            continue
        try:
            entries = os.listdir(current_path)
        except PermissionError:
            continue  # 忽略无法访问的目录
        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(current_path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
                queue.append((full_path, depth + 1))
            else:
                files.append(entry)
        yield current_path, dirs, files



def parse_traceback_lines(traceback_lines) -> list:
    pattern = r'^\s*File "(?P<file>.+)", line (?P<line>\d+), in (?P<function>.+)$'
    result = []
    
    for line in traceback_lines:
        line = line.split("\n")[0]  # 移除第二行
        match = re.match(pattern, line.strip())  # 移除首尾空白提高匹配稳定性
        if match:
            # 将行号转换为整数，其他保持字符串
            info = {
                "file": match.group("file"),
                "line": int(match.group("line")),
                "function": match.group("function")
            }
            result.append(info)
    result.reverse()  # 反转顺序，使最新的函数在最前面
    return result


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器，捕获未处理的异常并生成详细日志"""
    # 创建内存缓冲区捕获 rich 的输出
    buffer = StringIO()
    buffer_console = Console(file=buffer, record=True, force_terminal=True, highlight=False, no_color=True, color_system=None)
    
    # 生成时间戳
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 生成错误提示
    random_tip = random.choice([
        "Oops!",
        "No, this shouldn't happen.",
        "Smells like a *bug*.",
        "I'm sorry, Dave. I'm afraid I can't do that.",
        "What the heck is going on here?",
        "Houston, we have a problem.",
        "You're not supposed to be here.",
        "Yet another bug has been found."
    ])

    # 添加错误基本信息
    buffer_console.print(f"{random_tip}")
    buffer_console.print("Coral Core ran into a critical error and needs to shut down.")
    buffer_console.print(f"Timestamp: ({timestamp})")

    buffer_console.print("Possible causes:")
    buffer_console.print("\t- Coral Core is out of date.")
    buffer_console.print("\t- A plugin is causing the error.")
    buffer_console.print("\t- Coral Core has encountered an unexpected error.")
    buffer_console.print("\t- Your configuration is incorrect.")
    buffer_console.print("\t- Your system is having hardware or software issues.")

    # 打印Coral Core版本信息
    buffer_console.print("\n-----------------------Coral Core Information----------------------")

    buffer_console.print(f"Core Version: {CORAL_VERSION}")
    buffer_console.print(f"PluginManager Version: {PLUGINMANAGER_VERSION}")
    buffer_console.print(f"Protocol Version: {PROTOCOL_VERSION}")

    if 'event_bus' in locals():
        buffer_console.print("\nEvent Bus subscribed events:\n")
        for event_type in event_bus._subscribers.keys():
            buffer_console.print(f"\t{event_type.__name__}: {[handler[0].__name__ if isinstance(handler, tuple) else handler.__name__ for handler in event_bus._subscribers[event_type]]}")
    else:
        buffer_console.print("\n\U000026A0 Event Bus not initialized.")
    if 'register' in locals():
        buffer_console.print("\nRegister registered commands:\n")
        for command_name in register.commands.keys():
            buffer_console.print(f"\t{command_name}: {register.commands[command_name][0].__name__} (permission: {register.commands[command_name][1]})")
    else:
        buffer_console.print("\U000026A0 Register not initialized.")
    if 'perm_system' in locals():
        buffer_console.print("\nPerm System registered permissions:\n")
        for perm_name in perm_system.registered_perms.keys():
            buffer_console.print(f"\t{perm_name}: {perm_system.registered_perms[perm_name]}")
    else:
        buffer_console.print("\U000026A0 Perm System not initialized.")

    buffer_console.print(   "-------------------------------------------------------------------")
    
    # 打印插件信息
    buffer_console.print("\n------------------------------Plugins------------------------------")

    if 'config' in locals():
        plugin_dir = str(config.get("plugin_dir", PLUGIN_DIR))
    else:
        plugin_dir = PLUGIN_DIR

    if os.path.exists(plugin_dir):
        buffer_console.print(f"Plugin Directory: {plugin_dir}")
        buffer_console.print(f"Plugins:\n")
        for plugin_name in os.listdir(plugin_dir):
            if os.path.isdir(os.path.join(plugin_dir, plugin_name)):
                buffer_console.print(f"\t|\t{plugin_name}")
    else:
        buffer_console.print(f"\U000026A0 Plugin Directory not found.")

    if 'plugin_manager' in locals():
        buffer_console.print(f"\nLoaded plugins:\n")
        for plugin in plugin_manager.plugins:
            buffer_console.print(f"\t|\t{plugin}")
    buffer_console.print(   "-------------------------------------------------------------------")

    # 捕获异常并打印详细信息
    buffer_console.print("\n-------------------------Exception Details-------------------------")
    buffer_console.print(f"Exception Type: {exc_type.__name__}")
    buffer_console.print(f"Exception Message: {exc_value}\n")
    
    # 生成丰富的堆栈跟踪（包含局部变量）
    tb = Traceback.from_exception(
        exc_type,
        exc_value,
        exc_traceback,
        show_locals=True,
        suppress=[],  # 可选：排除特定模块的堆栈帧
        extra_lines=3    # 错误上下文行数
    )
    buffer_console.print(tb)

    buffer_console.print("\nOriginal Traceback (most recent call last):")
    for line in traceback.format_tb(exc_traceback, limit=None):
        buffer_console.print(line)

    try:
        buffer_console.print(f"Crash Top Location: {exc_traceback.tb_frame.f_code.co_filename}:{exc_traceback.tb_lineno}")
    except AttributeError:
        buffer_console.print("Crash Top Location: Unknown")

    # 打印可能的错误位置
    if possible_locations := parse_traceback_lines(traceback.format_tb(exc_traceback)):
        buffer_console.print("Possible Locations:")
        for items in possible_locations:
            if possible_locations.index(items) == 0:
                buffer_console.print(f"\tSUSPECTED -> {items['file']}:{items['line']} in {items['function']}")
                continue
            buffer_console.print(f"\t{items['file']}:{items['line']} in {items['function']}")
    
    buffer_console.print(   "-------------------------------------------------------------------")

    buffer_console.print("\n---------------------Global Variables Snapshot----------------------")

    for name, value in globals().items():
        if not name.startswith('__'):
            buffer_console.print(f"{name}: {type(value)} = {repr(value)[:200]}")

    for name, value in locals().items():
        if not name.startswith('__'):
            buffer_console.print(f"{name}: {type(value)} = {repr(value)[:200]}")

    buffer_console.print(   "-------------------------------------------------------------------")

    # 添加额外调试信息

    buffer_console.print("\n------------------------System Information--------------------------")

    buffer_console.print(f"Python: {sys.version.split()[0]}")
    buffer_console.print(f"System: {sys.platform}")
    buffer_console.print(f"Executable: {sys.executable}")
    
    buffer_console.print(   "-------------------------------------------------------------------")
    
    # 打印文件夹树状结构（深度为 3 层）

    buffer_console.print("\n--------------------------Folder Structure--------------------------")

    buffer_console.print(f"Working Dir: {os.getcwd()}")
    for root, _, files in walklevel(".", max_depth=2):
        level = root.replace(os.getcwd(), '').count(os.sep)
        indent = '\t|' + '\t|'*(level-1)
        buffer_console.print(f"{indent}\t{os.path.basename(root)}/")
        subindent = '\t|' + '\t|'*(level)
        for f in files:
            buffer_console.print(f"{subindent}\t{f}")

    buffer_console.print(   "-------------------------------------------------------------------")

    # 生成日志文件名
    log_file = f"./logs/crash_report_{timestamp.replace(':', '-').replace(' ', '_')}.log"
    
    # 写入日志文件
    with open(log_file, "w", encoding="utf-8") as f:
        # 去除ANSI颜色代码后写入
        f.write(buffer.getvalue())
    
    # 同时在控制台输出错误（带颜色）
    logger.error(f"An error occurred: {exc_type.__name__}: {exc_value}")
    Console().print(tb)
    logger.error(f"[bold red blink]Oops, Coral has crashed.\U0001F605 Please check the logs for more information.[/]")
    logger.info(f"Detailed crash report saved to: [bold yellow]{log_file}[/]")
    logger.info("Coral will now shut down.")
    
    # 强制退出程序
    sys.exit(1)

# 设置全局异常钩子
sys.excepthook = global_exception_handler

from .config import Config
from .register import Register
from .plugin_manager import PluginManager
from .perm_system import PermSystem
from .event_bus import EventBus
from .adapter import AdapterManager
from .driver import DriverManager

try:
    config = Config(CONFIG_FILE)
    event_bus = EventBus()
    register = Register(event_bus)
    perm_system = PermSystem(register, config)
    plugin_manager = PluginManager(register, config, perm_system, PLUGIN_DIR)
    adapter_manager = AdapterManager(event_bus, config)
    driver_manager = DriverManager(config, adapter_manager)
except Exception as e:
    logger.critical(f"[red]Failed to initialize Coral Core.[/]")
    raise e
