# 驱动器开发指南

驱动器负责与平台的实际通信（API调用/WebSocket等）

## 1. 继承基类

```python
from core.driver import BaseDriver

PROTOCOL = "my_platform"  # 必须与适配器协议一致

class MyPlatformDriver(BaseDriver):
    
```

## 2. 实现核心方法

```python
async def start(self):
    """启动驱动器"""
    self._session = aiohttp.ClientSession()
    self._task = asyncio.create_task(self._listen_events())

async def _listen_events(self):
    while self._running:
        # 实现事件监听逻辑
        data = await self._receive_from_platform()
        await self.handle_receive(data)

async def send_action(self, action: Dict[str, Any]):
    """执行平台动作"""
    if action["type"] == "ban":
        await self._call_api("POST", "/ban", json={
            "user_id": action["target"],
            "duration": action["data"]["duration"]
        })

async def stop(self):
    """停止驱动器"""
    self._running = False
    await self._task
    await self._session.close()
```

## 3. 实践建议

1. **错误处理**：

   ```python
   try:
       await self._call_api(...)
   except PlatformAPIError as e:
       logger.error(f"API调用失败: {e}")
   ```

2. **消息转换**：

   ```python
   def _convert_message(self, message: MessageRequest):
       # 将协议消息段转为平台格式
       segments = []
       for seg in message.message.segments:
           if seg.type == "text":
               segments.append({"type": "text", "content": seg.data})
           elif seg.type == "image":
               segments.append({"type": "image", "url": seg.data["url"]})
       return segments
   ```

3. **性能优化**：
   - 使用连接池管理API调用
   - 实现消息批量发送
   - 使用异步缓存机制

完整开发模板见框架的 `libraries/drivers` 目录，包含驱动器的完整实现示例。
