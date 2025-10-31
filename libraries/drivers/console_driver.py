import asyncio
import logging
from typing import Dict, Any
from Coral.driver import BaseDriver
from Coral.adapter import BaseAdapter
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import threading

logger = logging.getLogger(__name__)

prompt_style = Style.from_dict({
        # User input (default text).
        '':          "#f2ff00",
        # Prompt.
        'pound':    '#00aa00', # 通过pound来进行关联，可以改成别的名字
    })

prompt_message = [
    ('class:pound',    '> '), # pound对应'>'  
]


class ConsoleDriver(BaseDriver):
    """控制台驱动器 - 处理控制台输入输出"""
    PROTOCOL = "console"
    
    def __init__(self, adapter: BaseAdapter, config: Dict[str, Any] = {}):
        super().__init__(adapter, config)
        self.self_id = "Console"
        self.input_queue = asyncio.Queue()
        self.prompt_session = PromptSession(prompt_message, style=prompt_style)
        # 控制台驱动器启动时就创建Bot对象
        self.on_connect()
    
    async def start(self):
        """启动控制台输入监听"""
        self._running = True
        asyncio.get_event_loop().run_in_executor(None, self._read_console_input)
        logger.info("Console driver started")
    
    async def stop(self):
        """停止驱动器"""
        self._running = False
        # 停止时移除Bot对象
        self.on_disconnect()
        logger.info("Console driver stopped")
    
    def _read_console_input(self):
        """读取控制台输入"""
        while self._running:
            try:
                # line = await self.prompt_session.prompt_async()
                line = self.prompt_session.prompt()
                if line.strip():
                    # 将输入传递给适配器处理
                    asyncio.run(self.handle_receive({"text": line}))
            except (EOFError, KeyboardInterrupt):
                asyncio.run(self.handle_receive({"text": "stop"}))
                break
            except Exception as e:
                logger.error(f"Console input error: {e}")
    
    async def send_action(self, action: Dict[str, Any]):
        """输出到控制台"""
        if message := action.get("message"):
            print(message)