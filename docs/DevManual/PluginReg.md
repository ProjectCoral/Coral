# 插件注册

Coral 插件注册的行为分为三种类型：命令、监听事件、函数。

无论哪种，都需要在 `_init_.py` 中调用 `register` 类的方法 / 使用 `Coral` 内部装饰器，并传入相应的参数。

> [!important] 
> 在25/6/8的更新中，完全重构了注册方式，原先的[注册方式](PluginReg_old.md)仍然可以继续使用，但不再推荐。

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
  
你也可以使用`@perm_require` 装饰器来控制权限（你仍然需要注册权限，参考[权限系统](PermSystem.md)）。

```python
from Coral import on_command, CommandEvent, perm_require

@on_command(
    name = 'hello',
    description = 'Say hello to the world')
@perm_require('hello.use') # 控制用户是否有权限执行该命令
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

你可能已经注意到，在注册命令时，可以使用 `perm_require` 装饰器来控制用户是否有权限执行该命令。

权限系统是 Coral 提供的插件权限管理系统，它可以让你更精细地控制用户对插件的访问权限。

具体的权限控制逻辑，请参考 [权限系统](PermSystem.md)。