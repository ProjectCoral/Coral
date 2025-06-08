import asyncio
import logging
import json
from typing import Any, Dict
from core.driver import BaseDriver
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import threading
import uvicorn

logger = logging.getLogger(__name__)

class Onebotv11Driver(BaseDriver):
    """反向WebSocket驱动器（FastAPI实现）"""
    
    def __init__(self, driver_name: str, config: Dict[str, Any]):
        super().__init__(driver_name, config)
        self.websocket = None
        self.path = config.get('path', '/ws/api')
        self.port = config.get('port', 21050)
        self.app = FastAPI()
        self.thread = None
    
    def register_to_fastapi(self, app: FastAPI):
        """注册WebSocket路由到FastAPI应用"""
        self.app = app
        self.app.websocket(self.path)(self._handle_connection)
        logger.info(f"Reverse WebSocket route registered at {self.path}")
    
    async def start(self):
        """启动"""
        self._running = True
        self.register_to_fastapi(self.app)
        self.thread = threading.Thread(target=uvicorn.run, args=(self.app,), kwargs={'port': self.port}, daemon=True)
        self.thread.start()
        logger.info("Reverse WebSocket driver started")
    
    async def stop(self):
        """停止WebSocket服务"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
            self.websocket = None
        self._running = False
        logger.info("Reverse WebSocket driver stopped")
    
    async def send_action(self, action: Dict[str, Any]):
        """发送动作到平台"""
        if not self.websocket:
            logger.warning("No active WebSocket connection, cannot send action")
            return
        
        try:
            # 添加回显标识
            if 'echo' not in action:
                action['echo'] = f"action_{id(action)}"
            
            await self.websocket.send_text(json.dumps(action))
            logger.debug(f"Action sent: {action}")
        except Exception as e:
            logger.error(f"Error sending action: {e}")
    
    async def _handle_connection(self, websocket: WebSocket):
        """处理WebSocket连接（FastAPI路由处理函数）"""
        # 接受连接并设置子协议
        logger.info("Waiting for OneBot implementation to connect")
        # await websocket.accept(subprotocol="onebot11")
        await websocket.accept()
        
        self.websocket = websocket
        logger.info("OneBot implementation connected")
        
        try:
            while True:
                message = await websocket.receive_text()
                await self._process_message(message)
        except WebSocketDisconnect:
            logger.info("OneBot implementation disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket = None
    
    async def _process_message(self, message: str):
        """处理接收到的消息（保持不变）"""
        try:
            data = json.loads(message)
            
            # 处理API响应
            if 'echo' in data and 'retcode' in data:
                logger.debug(f"Received API response: {data}")
                return
            
            # 处理事件
            await self.handle_receive(data)
            logger.debug(f"Event processed: {data.get('post_type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")