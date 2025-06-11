# NoneBot兼容层插件开发指南

> [!tip]是的，孩子们，我干了（指强兼Nonebot2）

Coral 为插件开发者提供了比较详细的注册方式，但可能比较复杂。

所以 Coral 引入了NoneBot兼容层，您可以利用熟悉的NoneBot API编写插件，同时享受框架的核心功能。<s>那么为什么不直接使用Nonebot2呢？</s>

## 快速开始

```python
from core.nonebot_compat import on_command, permission_control, Bot, MessageEvent

# 创建一个简单的命令插件
@on_command("hello", aliases={"hi", "你好"}, priority=5)
@permission_control("basic")
async def hello_command(bot: Bot, event: MessageEvent):
    await bot.send(event, "你好！我是CoralBot")
```

## 事件处理

### 消息事件

```python
from core.nonebot_compat import on_message, Bot, MessageEvent

@on_message(priority=10)
async def handle_message(bot: Bot, event: MessageEvent):
    if "你好" in event.message.extract_plain_text():
        await bot.send(event, "你好！有什么可以帮您的？")
```

### 通知事件

```python
from core.nonebot_compat import on_notice, Bot, NoticeEvent

@on_notice(priority=5)
async def handle_notice(bot: Bot, event: NoticeEvent):
    if event.notice_type == "group_increase":
        await bot.send(event, f"欢迎新成员@{event.user_id}加入群聊！")
```

### 命令事件

```python
from core.nonebot_compat import on_command, Bot, CommandEvent

@on_command("weather", priority=5)
async def weather_command(bot: Bot, event: CommandEvent):
    city = event.args[0] if event.args else "北京"
    await bot.send(event, f"正在查询{city}的天气...")
```

## 消息构造与发送

### 发送简单消息

```python
await bot.send(event, "这是一条文本消息")
```

### 发送复合消息

```python
from core.nonebot_compat import MessageSegment

message = MessageSegment.text("你好") + \
          MessageSegment.at(event.user_id) + \
          MessageSegment.text("，这是一条复合消息！") + \
          MessageSegment.image("https://example.com/image.png")

await bot.send(event, message)
```

### 使用消息模板

```python
from core.nonebot_compat import MessageTemplate

template = MessageTemplate("你好{user}，当前时间是{time}")
message = template.format(user=event.user_id, time=current_time)

await bot.send(event, message)
```

## 权限控制

```python
from core.nonebot_compat import permission_control, on_command

# 单个权限检查
@on_command("admin")
@permission_control("admin")
async def admin_command(bot: Bot, event: MessageEvent):
    await bot.send(event, "管理员命令执行成功")

# 多个权限检查（满足任意一个即可）
@on_command("moderate")
@permission_control(["moderator", "admin"])
async def moderate_command(bot: Bot, event: MessageEvent):
    await bot.send(event, "内容管理命令执行")
```

## 规则系统

### to_me规则（仅当@机器人时触发）

```python
from core.nonebot_compat import on_message, to_me

@on_message(priority=5)
@to_me()
async def reply_to_me(bot: Bot, event: MessageEvent):
    await bot.send(event, "您提到了我，有什么需要帮助的吗？")
```

### 自定义规则

```python
from core.nonebot_compat import rule_checker, on_message

def is_group_admin() -> Callable:
    @rule_checker
    async def checker(bot: Bot, event: MessageEvent):
        return event.raw_event.user.roles and "admin" in event.raw_event.user.roles
    return checker

@on_message(priority=5)
@is_group_admin()
async def admin_message(bot: Bot, event: MessageEvent):
    await bot.send(event, "管理员消息已接收")
```

## 生命周期管理

```python
from core.nonebot_compat import on_startup, on_shutdown

@on_startup
async def init_plugin():
    print("插件正在初始化...")
    # 执行初始化操作，如数据库连接
    
@on_shutdown
async def cleanup_plugin():
    print("插件正在清理...")
    # 执行清理操作，如关闭数据库连接
```

## 实践建议

1. **优先级管理**：

   ```python
   # 高优先级插件（0-4）：核心功能、安全控制
   # 中优先级插件（5-9）：主要功能
   # 低优先级插件（10+）：辅助功能
   @on_message(priority=3)  # 高优先级
   ```

2. **错误处理**：

   ```python
   @on_command("calculate")
   async def calculate_command(bot: Bot, event: CommandEvent):
       try:
           result = eval(" ".join(event.args))
           await bot.send(event, f"计算结果: {result}")
       except Exception as e:
           await bot.send(event, f"计算错误: {str(e)}")
   ```

3. **复用消息处理**：

   ```python
   async def send_welcome(bot: Bot, event: Union[MessageEvent, NoticeEvent]):
       await bot.send(event, "欢迎使用本机器人！")
   
   # 多个事件复用同一处理函数
   @on_message(priority=5)
   @on_notice(priority=5)
   async def handle_welcome(bot: Bot, event: Union[MessageEvent, NoticeEvent]):
       await send_welcome(bot, event)
   ```

4. **命令别名支持**：

   ```python
   # 支持 "help", "帮助", "帮助文档" 三种命令形式
   @on_command("help", aliases={"帮助", "帮助文档"})
   async def help_command(bot: Bot, event: CommandEvent):
       await bot.send(event, "这里是帮助文档...")
   ```

## 调试技巧

1. 查看原始事件数据：

   ```python
   @on_message()
   async def debug_event(bot: Bot, event: MessageEvent):
       print("原始事件数据:", event.raw_event)
   ```

2. 权限调试：

   ```python
   @permission_control("special")
   async def special_command(bot: Bot, event: CommandEvent):
       # 如果未触发，检查权限系统日志
       await bot.send(event, "特殊权限命令执行")
   ```

3. 使用框架日志：

   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   @on_startup
   async def log_init():
       logger.info("插件初始化完成")
   ```
