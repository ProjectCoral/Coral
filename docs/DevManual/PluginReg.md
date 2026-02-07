# 插件注册

Coral 插件注册的行为分为三种类型：命令、监听事件、函数。

无论哪种，都需要在 `_init_.py` 中调用 `register` 类的方法 / 使用 `Coral` 内部装饰器，并传入相应的参数。

返回的数据格式请参考 [Protocol 文档](Protocol.md)。

## 注册命令

命令是指在操作台中，用户输入特定的命令时，插件可以执行一些操作。

在编写命令插件时，需要定义一个函数，并使用 `on_command` 装饰器进行装饰。


```python
from Coral import on_command, CommandEvent

@on_command('hello')
async def hello(event: CommandEvent):
    return 'Hello, world!' # str, MessageRequest, etc.
```

上面的代码定义了一个名为 `hello` 的命令，当用户输入 `hello` 时，插件会回复 `Hello, world!` 给用户。

`on_command` 装饰器参数：

- `name`：命令的名称，用户输入时需要用这个名称。
- `description`：命令的描述，用于帮助用户理解命令的作用。
- `permission`：命令的权限，用于控制用户是否有权限执行该命令。
  
你也可以使用 `filters` 来控制权限（你仍然需要注册权限，参考[权限系统](PermSystem.md)）。

```python
from Coral import on_command, CommandEvent
from Coral.filters import has_permission

@on_command(
    name = 'hello',
    description = 'Say hello to the world',
    filters = has_permission('admin'), # 权限过滤器
)
async def hello(event: CommandEvent):
    return 'Hello, world!'
```

你也可以导入全局配置 `config` 类，详情请参考 [config 文档](UseConfig.md)。

## 注册监听事件

监听事件是指插件可以监听到特定事件发生时，执行一些操作。

> Coral 预定义事件请参考[Protocol 文档](Protocol.md)。

目前 Coral 提供了以下装饰器：

- `on_message`：监听消息事件`MessageEvent`。
- `on_notice`：监听通知事件`NoticeEvent`。
- `on_event`：用以自定义监听事件。

装饰器参数：

- `name`：事件的名称，用于帮助用户理解事件的作用。
- `priority`：事件的优先级，用于控制事件的执行顺序。
- `event_type`：监听的事件类型，可以是 `MessageEvent`、`NoticeEvent`、`Event` 等（仅在 `on_event` 中使用）。

### 监听消息事件

依旧从 `Coral` 内部装饰器 `on_message` 开始。

```python
from Coral import on_message, MessageEvent

@on_message() # 监听所有消息事件
async def handle_message(event: MessageEvent):
    # 处理消息事件
    pass
```

你也可以使用 `filters` 来过滤消息事件。

```python
from Coral import on_message, MessageEvent
from Coral.filters import is_private

@on_message(filters=is_private())
async def handle_message(event: MessageEvent):
    # 处理消息事件
    pass
```

有关 `filter` 的具体使用，请查看 [Filters.md](Filters.md)。

### 监听通知事件

```python
from Coral import on_notice, NoticeEvent

@on_notice() # 监听所有通知事件
async def handle_notice(event: NoticeEvent):
    # 处理通知事件
    pass
```

### 自定义监听事件

```python
from Coral import on_event, MessageEvent

@on_event(event_type=MessageEvent) # 监听自定义事件
async def handle_custom_event(event: Event):
    # 处理自定义事件
    pass
```


### 注册高级事件

在重构的版本中，`register_event` 仍旧可以使用，其注册到了`GenericEvent`，可实现高级事件广播。

```python
from Coral import register
register.register_event(
    event_name='custom_event', # 自定义事件名称
    listener_name='handle_custom_event', # 自定义事件处理函数名称
    function=handle_custom_event, # 自定义事件处理函数
    priority=1 # 自定义事件优先级
)
```

## 注册函数

函数是指插件可以执行一些特定的功能，并返回一些数据。

在编写函数插件时，需要定义一个函数，并使用 `on_function` 装饰器进行装饰。

```python
from Coral import on_function

@on_function('hello')
async def hello():
    return 'Hello, world!'
```

上面的代码定义了一个名为 `hello` 的函数，当用户调用 `hello` 时，插件会返回 `Hello, world!` 给用户。

`on_function` 装饰器参数：

- `name`：函数的名称，插件调用时需要用这个名称。


## 注册权限

你可能已经注意到，在注册命令时，可以使用 `filters` 中的 `has_permission` 来控制用户是否有权限执行该命令。

权限系统是 Coral 提供的插件权限管理系统，它可以让你更精细地控制用户对插件的访问权限。

具体的权限控制逻辑，请参考 [权限系统](PermSystem.md)。

---

## 使用 PluginManager 进行插件管理

Coral 提供了强大的 PluginManager 系统，用于管理插件的完整生命周期。以下是使用 PluginManager 的指南：

### 1. 插件元数据声明

每个插件都应该在 `__init__.py` 文件的顶部声明元数据：

```python
__plugin_meta__ = {
    "name": "示例插件",
    "version": "1.0.0",
    "author": "开发者名称",
    "description": "插件功能描述",
    "compatibility": "250606",  # 与PluginManager兼容的最低版本
    
    # 可选：依赖声明
    "dependencies": ["other_plugin"],  # 依赖的其他插件
    "requirements": ["requests>=2.25.0"],  # Python包依赖
    
    # 可选：权限声明
    "permissions": {
        "example.command": "示例命令权限",
        "example.admin": "管理员权限"
    },
    
    # 可选：配置默认值
    "config": {
        "enabled": True,
        "max_retries": 3
    }
}
```

### 2. 插件生命周期钩子

插件可以定义生命周期钩子函数，这些函数会在插件加载和卸载时自动调用：

```python
async def plugin_load():
    """插件加载时调用"""
    print("插件加载完成")
    # 初始化数据库连接、加载配置等
    return True  # 返回True表示加载成功

async def plugin_unload():
    """插件卸载时调用"""
    print("插件卸载完成")
    # 关闭数据库连接、保存状态等
    return True  # 返回True表示卸载成功
```

### 3. 使用 Protocol v3 新特性

Coral Protocol v3 提供了更简洁的API，建议在新插件中使用：

#### 事件便捷回复
```python
@on_message(filters=contains("你好"))
async def greet_handler(event):
    # 使用便捷回复方法
    return event.reply("你好！", at_sender=True)
```

#### MessageChain 链式构建
```python
@on_command("welcome")
async def welcome_command(event):
    welcome_msg = MessageChain() \
        .add_text("欢迎 ") \
        .add_at(event.user.user_id) \
        .add_text(" ！\n") \
        .add_text("请查看群公告了解规则~") \
        .add_image("http://example.com/welcome.jpg")
    
    return event.reply(welcome_msg)
```

#### MessageRequest 构建器
```python
@on_message(filters=contains("帮助"))
async def help_handler(event):
    return MessageRequest.builder(event) \
        .text("可用命令：") \
        .text("\n1. 帮助 - 显示此帮助") \
        .text("\n2. 天气 <城市> - 查询天气") \
        .set_at_sender() \
        .build()
```

### 4. 插件管理命令

PluginManager 提供了一套完整的插件管理命令：

```bash
# 加载插件
plugin load example_plugin

# 卸载插件
plugin unload example_plugin

# 启用/禁用插件
plugin enable example_plugin
plugin disable example_plugin

# 列出插件
plugin list all           # 所有插件
plugin list loaded        # 已加载的插件
plugin list enabled       # 已启用的插件
plugin list disabled      # 已禁用的插件

# 查看统计信息
plugin stats              # 总体统计
plugin stats example_plugin  # 特定插件统计

# 查看插件信息
plugin info example_plugin

# 重新加载插件
plugin reload example_plugin  # 重新加载单个插件
plugin reload all             # 重新加载所有插件
```

### 5. 依赖管理

插件可以声明依赖关系，PluginManager 会自动处理依赖解析：

```python
__plugin_meta__ = {
    # ... 其他元数据 ...
    "dependencies": ["database", "cache"],  # 依赖的其他插件
    "requirements": [                        # Python包依赖
        "sqlalchemy>=1.4.0",
        "redis>=3.5.0"
    ]
}
```

### 6. 权限集成

插件可以声明和使用权限系统：

```python
# 在元数据中声明权限
__plugin_meta__ = {
    # ... 其他元数据 ...
    "permissions": {
        "weather.query": "查询天气权限",
        "weather.admin": "天气管理权限"
    }
}

# 在命令中使用权限检查
from Coral.filters import has_permission

@on_command(
    "weather_admin",
    "天气管理命令",
    filters=has_permission("weather.admin")
)
async def weather_admin_command(event):
    return "管理员操作成功"
```

### 7. 完整插件示例

```python
"""
天气查询插件示例
"""

__plugin_meta__ = {
    "name": "天气查询插件",
    "version": "2.0.0",
    "author": "Coral开发者",
    "description": "查询城市天气信息",
    "compatibility": "250606",
    "dependencies": [],
    "requirements": ["requests>=2.25.0"],
    "permissions": {
        "weather.query": "查询天气权限",
        "weather.admin": "天气管理权限"
    }
}

from Coral import on_command, on_message, contains
from Coral.protocol import MessageChain
import asyncio

# 插件生命周期钩子
async def plugin_load():
    print("天气插件加载完成")
    return True

async def plugin_unload():
    print("天气插件卸载完成")
    return True

# 注册命令
@on_command("weather", "查询天气")
async def weather_command(event):
    if not event.args:
        return event.reply("请指定城市，例如：天气 北京")
    
    city = event.args[0]
    weather_info = await get_weather(city)
    
    return event.reply(
        MessageChain()
            .add_text(f"{city}天气：")
            .add_text(f"\n{weather_info}")
    )

# 注册消息处理器
@on_message(filters=contains("天气怎么样"))
async def weather_message(event):
    # 从消息中提取城市
    message = event.message.to_plain_text()
    city = extract_city(message) or "北京"
    
    weather_info = await get_weather(city)
    return event.reply(f"{city}的天气：{weather_info}")

# 辅助函数
async def get_weather(city: str) -> str:
    """获取天气信息（模拟）"""
    await asyncio.sleep(0.1)  # 模拟网络请求
    weather_data = {
        "北京": "☀️ 晴天 25°C 湿度 45%",
        "上海": "🌧️ 小雨 22°C 湿度 85%",
        "广州": "⛅ 多云 28°C 湿度 70%"
    }
    return weather_data.get(city, "未知城市")

def extract_city(message: str) -> str:
    """从消息中提取城市名"""
    for city in ["北京", "上海", "广州", "深圳"]:
        if city in message:
            return city
    return None
```

## 相关文档

- [PluginManager 文档](./PluginManager.md) - 插件管理器详细指南
- [Protocol 文档](./Protocol.md) - Coral通信协议
- [插件开发指南](../PluginDev.md) - 插件开发完整指南
- [权限系统](./PermSystem.md) - 权限系统使用指南
- [过滤系统](./Filters.md) - 消息过滤系统
- [API 文档](./api.md) - 完整API参考

> **提示**：更多插件示例请参考 [plugins](https://github.com/ProjectCoral/Coral/blob/main/plugins) 目录。
