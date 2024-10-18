# 插件开发指南

目前， Coral 项目支持插件注册以下行为：

-  event 事件：当用户触发某些事件时，插件可以执行一些操作。
-  command 命令：当用户输入特定的命令时，插件可以执行一些操作。
-  fuction 函数：当代码调用特定的函数时，插件可以执行一些操作。

本篇将介绍如何开发一个插件，以实现一个简单的功能为例。

你也可以参考 [plugins](https://github.com/project-coral/coral/tree/master/coral/plugins) 中的插件示例，了解插件开发的基本流程。

## 规范

1. 插件的目录结构：

```
plugin-name
├── main.py  # 插件主文件
├── * README.md  # 插件说明文档(可选)
├── * requirements.txt  # 插件依赖(可选)
└── ...  # 其他文件(可选)
```
2. 插件主文件： 

    插件的主文件必须为 `main.py`， 它必须包含名为 `register_command` /`register_event` / `register_function`  的函数，该函数会在插件被注册时被调用。

3. 插件配置：

    你可以选择在插件中自行添加配置加载逻辑，也可以选择使用 `config` 类注册全局配置。

## 注册命令

命令是指在操作台中，用户输入特定的命令时，插件可以执行一些操作。

1. 编写命令逻辑：

    在 `main.py` 中，定义一个函数/类，该函数会在用户输入命令时被调用。
    
    **注意**: 需要打印/传递的信息必须以 `return` 语句的形式返回。

    示例函数：
    ```python
    def sayhello(self, args):
        return f"Hello, {args}!"
    ```

    你也可以定义一个类，此时可以传递 Coral 的 `register` 和 `config` 类，这样可以调用其他行为\获取全局配置。

    示例类：
    ```python
    class TestCommand:
        register = None
        config = None

        def __init__(self, register, config):
            self.register = register
            self.config = config

        def howmanycommands(self):
            return len(self.register.commands)
        
        def fetch_bot_id(self):
            return self.config.get("bot_id", "unknown")
    ```


2. 注册命令：

    在 `main.py` 中，调用 `register_command` 函数，并传入命令名称、命令描述、命令执行函数。


    **注意**: 命令名称必须唯一，否则会覆盖已注册的命令。

    ```python
    def register_command(register, config):
        register.register_command("sayhello", "Say hello to someone", sayhello)

        register.register_command("howmanycommands", "How many commands are registered", TestCommand(register, config).howmanycommands)

        register.register_command("fetch_bot_id", "Fetch bot id", TestCommand(register, config).fetch_bot_id)
    ```

3. 调用命令：

    在操作台中，输入命令名称，即可调用命令。

## 注册事件

事件是指当用户触发某些事件时，插件可以执行一些操作。

1. 编写事件逻辑：

    在 `main.py` 中，定义一个**异步**函数/类，该**异步**函数会在用户触发事件时被调用。

    在返回数据时，你需要包含：
    - 处理后的信息(打包成字典)
    - 是否继续执行后续插件(`True` / `False`)
    - 中断后更改事件优先级(数字越小，优先级越高)
    
        关于优先级，数字越小，优先级越高， Coral 定义的事件优先级为 1，你可以根据自己的需求设置优先级为0/1/2...(**不建议，除非你知道你在做什么**)。
    
    示例函数：
    ```python
    async def on_message(self, message):
        logging.info(f"Received message: {message['raw_message']}")
        return message, False, 1
    ```

    你也可以定义一个类，此时可以传递 Coral 的 `register` 和 `config` 类，这样可以调用其他行为\获取全局配置。

    示例类：
    ```python
    class TestEvent:
        register = None
        config = None

        def __init__(self, register, config):
            self.register = register
            self.config = config

        async def on_message(self, message):
            logging.info(f"Received message: {message['raw_message']}")
        
        async def connected(self):
            logging.info("Client connected")
            return 0, False, 1
    ```

2. 注册事件：

    在 `main.py` 中，调用 `register_event` 函数，并传入事件类型、事件名称、事件执行函数、执行优先级。

    目前支持的事件类型有：
    - `client_connected`: 当客户端连接到 Coral 时触发。
    - `client_disconnected`: 当客户端断开连接时触发。
    - `prepare_reply`: 当收到一条消息时，Coral 准备回复时触发。
    - `finish_reply`: 当 Coral 完成回复时触发。


    **注意**: 事件名称可以不唯一，但我还是不推荐这么做，因为可能会导致事件的执行顺序混乱。

    ```python
    def register_event(register, config):
        register.register_event("prepare_reply", "Receivemessage", on_message, 1)

        register.register_event("prepare_reply", "Receivemessage",TestEvent(register, config).on_message, 1)

        register.register_event("client_connected", "Clientconnected", TestEvent(register, config).connected, 1)
    ```

## 注册函数

函数是指当代码调用特定的函数时，插件可以执行一些操作。

1. 编写函数逻辑：

    在 `main.py` 中，定义一个**异步**函数/类，该**异步**函数会在代码调用特定的函数时被调用。

    编写函数时，如果有互通的需求，我推荐使用类，这样可以传递 Coral 的 `register` 和 `config` 类，可以调用其他行为\获取全局配置。

    **注意**: 函数名称必须唯一，否则会覆盖已注册的函数。

    示例函数：
    ```python
    async def on_function_call(self, func_name, args):
        logging.info(f"Function {func_name} called with args: {args}")
        return None
    ```

    示例类：
    ```python
    class TestFunction:
        register = None
        config = None

        def __init__(self, register, config):
            self.register = register
            self.config = config

        async def on_function_call(self, func_name, args):
            logging.info(f"Function {func_name} called with args: {args}")
            return None
    ```

2. 注册函数：

    在 `main.py` 中，调用 `register_function` 函数，并传入函数名称、函数执行函数。

    ```python
    def register_function(register, config):
        register.register_function("on_function_call", on_function_call)

        register.register_function("on_function_call", TestFunction(register, config).on_function_call)
    ```

3. 调用函数：

    在代码中，使用 `register.execute_function` 调用函数，并传入函数名称和参数。

    ```python
    register.execute_function("on_function_call", "test_func", "arg1", "arg2")
    ```