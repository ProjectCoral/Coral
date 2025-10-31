# Bot 管理

Coral框架现在支持Bot对象管理，允许插件获取和操作特定平台的Bot实例。

## 概述

每个连接到Coral的平台都会创建一个或多个Bot对象，这些对象代表在该平台上的机器人身份。插件可以获取这些Bot对象并使用它们发送消息或执行操作。

当驱动器（Driver）连接到平台时，系统会自动创建相应的Bot对象。当驱动器断开连接时，系统会自动移除相应的Bot对象。

## 获取Bot对象

### 1. 通过self_id获取特定Bot

```python
from Coral import get_bot

# 获取特定ID的Bot
bot = get_bot("123456789")
if bot:
    # 使用Bot发送消息
    await bot.send_message("Hello, World!")
```

### 2. 通过平台获取所有Bot

```python
from Coral import get_bots_by_platform

# 获取特定平台的所有Bot
bots = get_bots_by_platform("onebotv11")
for bot in bots:
    print(f"Bot ID: {bot.self_id}")
```

## Bot对象方法

### send_message(message, user=None, group=None, at_sender=False)

发送消息到指定用户或群组。

参数:

- `message`: 消息内容，可以是字符串或MessageChain对象
- `user`: 目标用户（可选）
- `group`: 目标群组（可选）
- `at_sender`: 是否@发送者（仅在群组中有效）

示例:

```python
# 发送简单文本消息
await bot.send_message("Hello!")

# 发送复杂消息
from Coral.protocol import MessageChain, MessageSegment
message = MessageChain([
    MessageSegment.text("Hello, "),
    MessageSegment.at("123456789"),
    MessageSegment.text("!")
])
await bot.send_message(message)
```

### send_action(action_type, target, **kwargs)

执行特定平台的操作。

参数:

- `action_type`: 操作类型（如"kick_member", "delete_message"等）
- `target`: 操作目标（用户或群组）
- `**kwargs`: 操作特定参数

示例:

```python
from Coral.protocol import UserInfo

# 踢出用户
user = UserInfo(platform="onebotv11", user_id="987654321")
await bot.send_action("kick_member", user, group_id="123456")
```

## Bot生命周期管理

### 自动创建和移除

当驱动器（Driver）连接到平台时，系统会自动创建Bot对象。当驱动器断开连接时，系统会自动移除Bot对象。

Bot的self_id从驱动器配置中获取。

### Driver和Adapter协作

Driver负责与平台通信，并在连接状态改变时通知Adapter：

- 当Driver连接时，调用Adapter的`create_bot_for_driver`方法
- 当Driver断开连接时，调用Adapter的`remove_bot_for_driver`方法

Adapter负责创建和管理Bot对象，并确保它们在全局注册表中正确注册。

### 可复用的Adapter

Adapter现在是可复用的，可以与多个具有不同self_id的Driver实例配合工作。每个Driver连接时都会创建一个独立的Bot对象。

示例:

```python
# 一个Adapter可以服务于多个Driver
adapter = Onebotv11Adapter(config)

# 每个Driver连接时都会创建一个Bot对象
driver1 = ReversewsDriver(adapter, {"self_id": "123456"})
driver2 = ReversewsDriver(adapter, {"self_id": "789012"})

# 当driver1连接时，创建Bot "123456"
driver1.on_connect()  # 创建Bot "123456"

# 当driver2连接时，创建Bot "789012"
driver2.on_connect()  # 创建Bot "789012"
```

## 在插件中使用Bot对象

```python
from Coral import on_command, get_bots_by_platform

@on_command("broadcast", "向所有平台广播消息")
async def broadcast_command(event):
    # 获取所有OneBot V11平台的Bot
    bots = get_bots_by_platform("onebotv11")
    
    # 向所有Bot发送消息
    for bot in bots:
        await bot.send_message(
            f"Broadcast: {event.raw_message.to_plain_text()}", 
            group=event.group
        )
    
    return "消息已广播到所有平台"
```

## 注意事项

1. Bot对象在驱动器连接时自动创建，在断开连接时自动移除
2. 如果平台断开连接，对应的Bot对象会被自动清理
3. 在使用Bot对象前，建议检查其是否仍然有效
4. 不同平台的Bot可能支持不同的操作类型
5. 一个Adapter可以与多个Driver配合使用，每个Driver有自己独立的self_id
