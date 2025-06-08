# 插件开发指南

目前， Coral 项目支持插件注册以下行为：

-  event 事件：当用户触发某些事件时，插件可以执行一些操作。
-  command 命令：当用户输入特定的命令时，插件可以执行一些操作。
-  fuction 函数：当代码调用特定的函数时，插件可以执行一些操作。

你也可以参考 [plugins](https://github.com/ProjectCoral/Coral/blob/main/plugins) 中的插件示例，了解插件开发的基本流程。

## 规范

1. 插件的目录结构：

    ```
    plugin-name
    ├── __init__.py  # 插件主文件
    ├── * README.md  # 插件说明文档(可选)
    ├── * requirements.txt  # 插件依赖(可选)
    └── ...  # 其他文件(可选)
    ```

    - 插件的主文件必须为 `__init__.py`，插件名称自动取自目录名称。

    - `requirements.txt` 用于声明插件依赖(可选)，若存在则会检查依赖是否满足并自动安装(我还是建议你搞个脚本，自动安装用的是 pip，网不好就抽风)。

2. 插件元数据：
   
   你可以在插件顶部声明元数据：

    ```python
    __plugin_meta__ = {
        "name": "示例插件",
        "version": "1.0.0",
        "author": "开发者名称",
        "description": "插件功能描述",
        "conpatibility": "250606"  # 与PluginManager兼容的版本
    }
    ```

3. 插件逻辑： 

    - 插件的主文件会在插件被注册时被调用，具体的注册方式请参考 [插件注册](DevManual/PluginReg.md)。

    - 插件与框架通信时使用内部协议，详情请参考 [Protocol 文档](DevManual/Protocol.md)。
  
    - 返回的数据格式或是 API 请求数据请参考 [API 文档](DevManual/api.md)。

    - 当编写插件时你可以选择接入 Coral 内置的权限系统(详情请参考 [权限系统开发文档](DevManual/PermSystem.md))，也可以自己实现权限系统。

    - 我建议你将插件的 data 目录放在`./data/插件名`  目录下，这样可以方便管理插件数据。
  
    - 目前你可以引入以下模块：
        ```python
        from coral import register, config, perm_system
        ```

4. 插件配置：

    - 你可以选择使用 `config` 类注册全局配置，详情请参考 [调用全局配置](DevManual/UseConfig.md)。

    - 如果需要自行添加配置加载逻辑，请尽量把配置信息放在 `./config/插件名`  目录下，<s>不要到处乱拉</s>。
  
---

## 快速入门

### 1. 插件元数据

在插件顶部声明元数据：
```python
__plugin_meta__ = {
    "name": "示例插件",
    "version": "1.0.0",
    "author": "开发者名称",
    "description": "插件功能描述",
    "conpatibility": "250606"  # 与PluginManager兼容的版本
}
```

### 2. 注册命令

```python
from Coral import on_command, MessageRequest

@on_command(
    name="hello", 
    description="打招呼命令",
    permission="example.hello"  # 可选权限要求
)
async def hello_command(event):
    # return f"你好，{event.user.nickname}！" # 不建议直接返回字符串，虽然会转换，但不符合规范
    return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([MessageSegment(type="text", data=f"你好，{event.user.nickname}！")]),
            user=event.user,
            group=event.group if event.group else None
        ) # 使用MessageRequest/ActionRequest返回消息更加灵活
```

### 3. 注册事件处理器

```python
from Coral import on_message, MessageRequest

@on_message(
    name="消息处理器", 
    priority=3  # 优先级(1-10)，默认为5
)
async def message_handler(event):
    if "你好" in event.message.to_plain_text():
        return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([MessageSegment(type="text", data="你好！")]),
            user=event.user,
            group=event.group if event.group else None
        )
```

### 4. 注册功能函数

```python
from Coral import on_function

@on_function("get_weather")
async def get_weather(city: str): # 供其他插件调用的功能函数
    """获取城市天气"""
    # 这里实现天气查询逻辑
    return {"city":city, "weather":"晴天"}
```

### 5. 使用权限系统

```python
from Coral import perm_require

@on_command("admin", "管理员命令")
@perm_require("admin.permission")  # 权限检查装饰器
async def admin_command(event):
    return "管理员操作成功" # 此处返回字符串自动转换为MessageRequest，也可以返回MessageRequest/ActionRequest对象
```

## 完整插件示例

```python
__plugin_meta__ = {
    "name": "问候插件",
    "version": "1.0.0",
    "description": "提供基本的问候功能"
}

from Coral import on_command, on_message, on_function

# 注册命令
@on_command("greet", "打招呼命令")
async def greet_command(event):
    return f"你好，{event.user.nickname}！很高兴见到你！"

# 注册消息事件处理器
@on_message(priority=7)
async def auto_greet(event):
    text = event.message.to_plain_text()
    if "早上好" in text:
        return "早上好！今天也是充满活力的一天！"
    elif "晚安" in text:
        return "晚安，做个好梦！"

# 注册功能函数
@on_function("get_greeting")
async def get_greeting(time_of_day: str):
    """获取时间问候语"""
    greetings = {
        "morning": "早上好！",
        "afternoon": "下午好！",
        "evening": "晚上好！"
    }
    return greetings.get(time_of_day.lower(), "你好！")
```

## 其他开发建议

1. **权限管理**：
   - 使用 `perm_system.register_perm()` 注册权限
   - 在命令中使用 `permission` 参数声明所需权限

2. **错误处理**：
   ```python
   try:
       # 可能出错的代码
   except Exception as e:
       logger.error(f"插件错误: {e}")
       return "抱歉，出错了！"
   ```

3. **资源管理**：
   - 配置文件存储在 `./config/插件名/`
   - 数据文件存储在 `./data/插件名/`

4. **依赖声明**：
   在 requirements.txt 中声明依赖：
   ```plaintext
   requests==2.28.2
   beautifulsoup4==4.12.2
   ```