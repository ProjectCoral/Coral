# 插件注册

Coral 插件注册的行为分为三种类型：命令、监听事件、函数。

无论哪种，都需要在 `main.py` 中调用 `register` 类的方法，并传入相应的参数。

> 在24/11月的更新中，新增了对修饰器的支持，可以更方便地注册命令。

> 在25/6月的更新中，重构了注册逻辑，现在注册可以直接调用。

返回的数据格式或是 API 请求数据请参考 [API 文档](api.md)。

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

    在 `main.py` 中，导入 `register` 类，并调用 `register_command` 方法，传入命令名称、命令描述、命令执行函数。


    **注意**: 命令名称必须唯一，否则会覆盖已注册的命令。

    ```python
    from Coral import register, config

    register.register_command("sayhello", "Say hello to someone", sayhello)

    register.register_command("howmanycommands", "How many commands are registered", TestCommand(register, config).howmanycommands)

    register.register_command("fetch_bot_id", "Fetch bot id", TestCommand(register, config).fetch_bot_id)

    @register.future.register_command("sayhi", "Say hi to someone")
    async def sayhi(*args):
        # add your code here
    ```

3. 调用命令：

    在操作台中，输入命令名称，即可调用命令。

    或是在代码中，使用 `register.execute_command` 调用命令，并传入命令名称、用户 ID、群组 ID、命令参数(可选)。

    ```python
    register.execute_command("sayhello", user_id, group_id, "world")

    register.execute_command("howmanycommands", user_id, group_id)

    register.execute_command("fetch_bot_id", user_id, group_id)
    ```

    若想要仅在代码处调用，不考虑用户侧，可以将 `user_id` 设置为 `Console`，`group_id` 设置为 任意值(详情请参考 [权限系统用户文档](https://github.com/ProjectCoral/Coral/blob/main/docs/UserManual/PermSystem.md))。

    ```python
    register.execute_command("fetch_bot_id", "Console", -1)
    ```

    > 关于 `user_id, group_id` 参数，请参考 [注册权限](#注册权限)。

## 注册事件

事件是指当用户触发某些事件时，插件可以执行一些操作。

1. 编写事件逻辑：

    在 `main.py` 中，定义一个**异步**函数/类，该**异步**函数会在用户触发事件时被调用。

    在调用函数时，会传入事件数据`list`，包括：
    - 调用函数传入的参数(`Any`)
    - 回复缓冲区`result_buffer`(`list`)

    在返回数据时，你需要包含：
    - 处理后的信息 (`Any`|`list`)
    > 如果你想更改回复缓冲区，请返回格式为 `[result, result_buffer]`的 `list`。
    - 是否继续执行后续插件(`True` / `False`)
    - 中断后更改事件优先级(数字越小，优先级越高)

        关于优先级，数字越小，优先级越高， Coral 定义的事件优先级为 1，你可以根据自己的需求设置优先级为0/1/2...(**不建议，除非你知道你在做什么**)。

    示例函数：

    ```python
    async def on_message(self, message):
        logging.info(f"Received message: {message['message']}")
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
            logging.info(f"Received message: {message['message']}")
        
        async def connected(self):
            logging.info("Client connected")
            return None, False, 1
    ```

2. 注册事件：

    在 `main.py` 中，导入 `register` 类，并调用 `register_event` 方法，传入事件类型、事件名称、事件执行函数、执行优先级。

    目前支持的事件类型有：
    - `client_connected`: 当客户端连接到 Coral 时触发。
    - `client_disconnected`: 当客户端断开连接时触发。
    - `prepare_reply`: 当收到一条消息时，Coral 准备回复时触发。
    - `finish_reply`: 当 Coral 完成回复时触发。


    **注意**: 事件名称可以不唯一，但我还是不推荐这么做，因为可能会导致事件的执行顺序混乱。

    ```python
    from Coral import register, config

    register.register_event("prepare_reply", "Receivemessage", on_message, 1)

    register.register_event("prepare_reply", "Receivemessage",TestEvent(register, config).on_message, 1)

    register.register_event("client_connected", "Clientconnected", TestEvent(register, config).connected, 1)

    @register.future.register_event("client_disconnected", "Clientdisconnected", 1)
    async def client_disconnected():
        # add your code here
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

    在 `main.py` 中，导入 `register` 类，并调用 `register_function` 方法，传入函数名称、函数执行函数。

    ```python
    from Coral import register, config

    register.register_function("on_function_call", on_function_call)

    register.register_function("on_function_call", TestFunction(register, config).on_function_call)

    @register.future.register_function("test_func", 1)
    async def test_func(*args):
        # add your code here
    ```

3. 调用函数：

    在代码中，使用 `register.execute_function` 调用函数，并传入函数名称和参数。

    ```python
    register.execute_function("on_function_call", "test_func", "arg1", "arg2")
    ```

# 注册权限

你可能已经注意到，在注册命令、事件、函数时，都需要传入 `perm_system`，这是实现权限控制的接口。

具体的权限控制逻辑，请参考 [权限系统](PermSystem.md)。