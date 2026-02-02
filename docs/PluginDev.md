# 插件开发指南

## 快速导航

- [插件开发规范](#插件开发规范)
- [快速入门](#快速入门)
  - [插件元数据](#1-插件元数据)
  - [注册命令](#2-注册命令)
  - [注册事件处理器](#3-注册事件处理器)
  - [注册功能函数](#4-注册功能函数)
  - [使用权限系统](#5-使用权限系统)
- [插件示例](#智能问候插件示例)
- [Protocol v3 新特性](#protocol-v3-新特性)
- [开发建议与最佳实践](#开发建议与最佳实践)
- [相关文档链接](#相关文档链接)

---

## 插件开发规范

### 1. 插件目录结构

```
plugin-name/
├── __init__.py      # 插件主文件（必需）
├── README.md        # 插件说明文档（可选）
├── requirements.txt # 插件依赖声明（可选）
└── ...              # 其他文件（可选）
```

- **插件主文件**：必须为 `__init__.py`，插件名称自动取自目录名称
- **依赖管理**：`requirements.txt` 用于声明插件依赖(可选)，若存在则会检查依赖是否满足并自动安装(我还是建议你搞个脚本，自动安装用的是 pip，网不好就抽风)
- **数据存储**：建议将插件数据放在 `./data/插件名/` 目录下
- **配置存储**：建议将配置信息放在 `./config/插件名/` 目录下

### 2. 插件元数据声明

在插件顶部声明元数据：

```python
__plugin_meta__ = {
    "name": "示例插件",
    "version": "1.0.0",
    "author": "开发者名称",
    "description": "插件功能描述",
    "compatibility": "250606"  # 与PluginManager兼容的最低版本
}
```

### 3. 插件开发基础

- **插件注册**：插件主文件在插件被注册时调用，详情参考 [插件注册文档](DevManual/PluginReg.md)
- **通信协议**：插件与框架通信使用内部协议，详情参考 [Protocol 文档](DevManual/Protocol.md)
- **API 规范**：返回数据格式或 API 请求数据参考 [API 文档](DevManual/api.md)
- **权限系统**：可选择接入 Coral 内置权限系统，参考 [权限系统开发文档](DevManual/PermSystem.md)
- **全局配置**：使用 `config` 类注册全局配置，参考 [调用全局配置](DevManual/UseConfig.md)

> [!NOTE] 
> 如果需要自行添加配置加载逻辑，请尽量把配置信息放在 `./config/插件名`  目录下，<s>不要到处乱拉</s>。

---

## 快速入门

### 1. 插件元数据

```python
__plugin_meta__ = {
    "name": "示例插件",
    "version": "1.0.0",
    "author": "开发者名称",
    "description": "插件功能描述",
    "compatibility": "250606"
}
```

### 2. 注册命令

```python
from Coral import on_command
from Coral.protocol import MessageRequest, MessageChain, MessageSegment

@on_command(
    name="hello", 
    description="打招呼命令",
    permission="example.hello"  # 可选权限要求
)
async def hello_command(event):
    return MessageRequest(
        platform=event.platform,
        event_id=event.event_id,
        self_id=event.self_id,
        message=MessageChain([
            MessageSegment(type="text", data=f"你好，{event.user.nickname}！")
        ]),
        user=event.user,
        group=event.group if event.group else None
    )
```

### 3. 注册事件处理器（使用过滤系统）

Coral 提供了强大的消息过滤系统，简化插件开发：

#### 3.1 基础过滤条件

```python
from Coral import on_message
from Coral.protocol import MessageRequest
from Coral.filters import contains, starts_with, from_user, in_group

# 包含关键词过滤
@on_message(name="问候处理器", filters=contains("你好"))
async def greet_handler(event):
    return MessageRequest(
        platform=event.platform,
        event_id=event.event_id,
        self_id=event.self_id,
        message=MessageChain([
            MessageSegment(type="text", data=f"你好，{event.user.nickname}！")
        ]),
        user=event.user,
        group=event.group if event.group else None
    )
```

#### 3.2 组合过滤条件

```python
from Coral import on_message
from Coral.filters import and_, or_, not_, has_permission

# 逻辑与组合
@on_message(
    name="精确匹配处理器",
    filters=and_(
        starts_with("天气"),
        in_group([10001])
    )
)
async def weather_handler(event):
    city = event.message.text.replace("天气", "").strip()
    return f"{city}的天气是..."
```

#### 3.3 高级过滤功能

```python
from Coral import on_message
from Coral.filters import regex, rate_limit, message_type, custom
import re

# 正则表达式过滤
@on_message(name="正则处理器", filters=regex(r"^查询\s+(\w+)$"))
async def regex_handler(event):
    match = re.match(r"^查询\s+(\w+)$", event.message.text)
    if match:
        keyword = match.group(1)
        return f"查询关键词：{keyword}"
    return None
```

### 4. 注册功能函数

```python
from Coral import on_function

@on_function("get_weather")
async def get_weather(city: str):
    """获取城市天气"""
    return {"city": city, "weather": "晴天"}
```

### 5. 使用权限系统

```python
from Coral import on_command

@on_command(
    name = "admin",
    description = "管理员命令",
    permission="example.admin"
)
async def admin_command(event):
    return "管理员操作成功"
```

---

## 智能问候插件示例

```python
__plugin_meta__ = {
    "name": "智能问候插件",
    "version": "2.0.0",
    "author": "Coral开发者",
    "description": "使用过滤系统实现的智能问候插件",
    "compatibility": "250606"
}

from Coral import on_message, on_command
from Coral.filters import contains, starts_with, or_, and_, from_user, in_group, has_permission
from Coral.protocol import MessageRequest, MessageChain, MessageSegment
import datetime

# 基础问候 - 包含"你好"关键词
@on_message(name="基础问候", filters=contains("你好"))
async def basic_greet(event):
    return MessageRequest(
        platform=event.platform,
        event_id=event.event_id,
        self_id=event.self_id,
        message=MessageChain([
            MessageSegment.text(f"你好，{event.user.nickname}！")
        ]),
        user=event.user,
        group=event.group
    )

# 时间问候 - 多种问候语
@on_message(
    name="时间问候",
    filters=or_(
        contains("早上好"),
        contains("早安"),
        contains("下午好"),
        contains("晚上好"),
        contains("晚安")
    )
)
async def time_greet(event):
    text = event.message.to_plain_text()
    current_hour = datetime.datetime.now().hour
    
    if "早上好" in text or "早安" in text:
        return "早上好！今天也是充满活力的一天！"
    elif "下午好" in text:
        return "下午好！工作学习辛苦了！"
    elif "晚上好" in text:
        return "晚上好！今天过得怎么样？"
    elif "晚安" in text:
        return "晚安，做个好梦！"
    
    # 根据时间自动问候
    if 5 <= current_hour < 12:
        return "早上好！"
    elif 12 <= current_hour < 18:
        return "下午好！"
    else:
        return "晚上好！"

# 管理员专用命令 - 需要权限和指定用户
@on_command(
    name="admin_greet",
    description="管理员问候命令",
    permission="admin.greet",
    filters=and_(
        from_user([123456, 789012]),  # 只允许指定管理员
        has_permission("admin.access")  # 需要管理员权限
    )
)
async def admin_greet_command(event):
    return f"管理员{event.user.nickname}，欢迎使用管理命令！"

# 群组专用功能 - 只在指定群组生效
@on_message(
    name="群组欢迎",
    filters=and_(
        in_group([10001, 10002, 10003]),  # 只在指定群组
        contains("新人")  # 包含"新人"关键词
    )
)
async def group_welcome(event):
    return f"欢迎新人加入{event.group.name if event.group else '本群'}！"

# 速率限制示例 - 防止滥用
@on_message(
    name="查询功能",
    filters=and_(
        starts_with("查询"),
        has_permission("query.allow")  # 需要查询权限
    )
)
async def query_handler(event):
    keyword = event.message.text.replace("查询", "").strip()
    return f"正在查询：{keyword}，请稍候..."
```

---

## Protocol v3 新特性

Coral Protocol v3 引入了多项新功能，使插件开发更加简洁高效：

### 1. 事件便捷回复

所有事件类都新增了 `reply()` 方法：

```python
@on_message(filters=contains("你好"))
async def greet_handler(event):
    # 简单回复
    return event.reply("你好！")
    
    # 带选项的回复
    return event.reply("你好！", at_sender=True, recall_duration=60)
```

### 2. MessageChain 链式构建

使用链式调用构建复杂消息：

```python
@on_message(filters=contains("欢迎"))
async def welcome_handler(event):
    welcome_msg = MessageChain() \
        .add_text("欢迎 ") \
        .add_at(event.user.user_id) \
        .add_text(" ！\n") \
        .add_text("请查看群公告了解规则~") \
        .add_image("http://example.com/welcome.jpg")
    
    return event.reply(welcome_msg)
```

### 3. MessageRequest 构建器

使用构建器模式创建复杂消息请求：

```python
@on_message(filters=contains("帮助"))
async def help_handler(event):
    return MessageRequest.builder(event) \
        .text("可用命令：") \
        .text("\n1. 帮助 - 显示此帮助") \
        .text("\n2. 天气 <城市> - 查询天气") \
        .text("\n3. 时间 - 显示当前时间") \
        .set_at_sender() \
        .build()
```

### 4. Bot 链式调用

主动发送消息时使用链式调用：

```python
from Coral import get_bot

async def send_notification():
    bot = get_bot("qq", "bot_123")
    
    # 链式调用发送通知
    await bot.to_group("10001").send("系统通知：服务器维护中")
    await bot.to_user("123456").recall_after(300).send("这条消息5分钟后撤回")
```

### 5. 天气查询插件示例

```python
__plugin_meta__ = {
    "name": "天气查询插件",
    "version": "2.0.0",
    "description": "使用新Protocol功能的天气查询插件"
}

from Coral import on_command, on_message, contains
from Coral.protocol import MessageChain

@on_command("weather", "查询天气")
async def weather_command(event):
    if not event.args:
        return event.reply("请指定城市，例如：天气 北京")
    
    city = event.args[0]
    weather_data = {"北京": "☀️ 晴天 25°C", "上海": "🌧️ 小雨 22°C"}
    weather = weather_data.get(city, "未知城市")
    
    return event.reply(
        MessageChain()
            .add_text(f"{city}天气：")
            .add_text(f"\n{weather}")
            .add_text("\n\n建议：")
            .add_text("适合外出" if "晴" in weather else "建议带伞")
    )
```

---

## 相关文档链接

| 文档 | 描述 | 链接 |
|------|------|------|
| **插件注册** | 插件注册机制和流程 | [PluginReg.md](DevManual/PluginReg.md) |
| **通信协议** | Coral 内部通信协议 | [Protocol.md](DevManual/Protocol.md) |
| **API 文档** | API 接口和数据格式 | [api.md](DevManual/api.md) |
| **权限系统** | 权限系统开发指南 | [PermSystem.md](DevManual/PermSystem.md) |
| **过滤系统** | 消息过滤系统使用 | [Filters.md](DevManual/Filters.md) |
| **全局配置** | 配置系统使用方法 | [UseConfig.md](DevManual/UseConfig.md) |
| **适配器开发** | 适配器开发指南 | [AdapterDev.md](DevManual/AdapterDev.md) |
| **驱动开发** | 驱动开发指南 | [DriverDev.md](DevManual/DriverDev.md) |
| **事件总线** | 事件总线系统 | [EventBus.md](DevManual/EventBus.md) |

> **提示**：更多开发资源请参考 [plugins](https://github.com/ProjectCoral/Coral/blob/main/plugins) 中的插件示例。