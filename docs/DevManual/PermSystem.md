# 接入权限系统

Coral 内置了权限系统，用户可以根据自己的需求进行权限控制。

关于权限系统的权限的定义/使用，请参阅 [权限系统用户文档](https://github.com/ProjectCoral/Coral/blob/main/docs/UserManual/PermSystem.md)。

## 接入 command

通常来说，command 都是需要权限控制的，因此建议在 command 中加入权限控制的逻辑。

1. 注册权限

    ```python
    from Coral import on_command, config
    @on_command("fetch_self_id", "Fetch self id")
    async def fetch_self_id(*args):
        ...
    ```

    这里，我们注册了一个 `fetch_self_id` 命令，我们想要限制只有拥有权限的用户才能执行。

    如何注册权限？我们可以导入 `perm_system` ，它是一个 `PermSystem` 类的实例，我们可以调用它的 `register_perm` 方法来注册权限：

    ```python
    from Coral import perm_system
    perm_system.register_perm("test_perm", "Test permission")
    perm_system.register_perm("test_perm.sub_perm", "Sub permission")
    ```
    这里，我们注册了两个权限，`test_perm` 和 `test_perm.sub_perm`。

    我建议你注册一个主权限，然后再注册一些子权限，<s>这样可以每个命令都来几个权限</s>。

2. 绑定权限

    接下来，我们需要在函数中绑定权限。

    Coral 内置的权限系统已经提供了一个快速绑定方式，只需在注册时传入即可：

    ```python
    from Coral import on_command, config
    @on_command(
        name = "fetch_self_id", 
        description = "Fetch self id", 
        permission = ["test_perm", "test_perm.sub_perm"]
    )
    async def fetch_self_id(*args):
        ...
    ```

    或是使用过滤器中的 `has_permission`:

    ```python
    from Coral import on_command, config
    from Coral.filters import has_permission

    @on_command(
        name = "fetch_self_id", 
        description = "Fetch self id",
        filters = has_permission(
            ["test_perm", "test_perm.sub_perm"]
        ),
    )
    async def fetch_self_id(*args):
        ...
    ```

    这里，我们传入了 `["test_perm", "test_perm.sub_perm"]` 作为权限列表，表示只有拥有这两个权限的用户才能执行 `fetch_self_id` 命令。

    **注意**：这里的权限列表可以是任意多个权限，只要用户拥有其中任意一个权限，就能执行命令。

3. 使用

    如果没有意外，你的权限应该已经可以正常工作了。

    > 输入 `perms show` 查看目前注册的权限，输入 `perms <add|remove> <perm_name> <user_id> <group_id>`  来授予或回收权限。详情请参阅 [权限系统用户文档](https://github.com/ProjectCoral/Coral/blob/main/docs/UserManual/PermSystem.md)。

    你可以在代码中，使用 `register.execute_command` 调用命令。

    ```python
    from Coral import register, CommandEvent, MessageChain, UserInfo
    register.execute_command(
        event_id="123",
        platform="qq",
        self_id="12345",
        command="fetch_self_id",
        raw_message=MessageChain([...]),
        user=UserInfo(...),
        args=[]
    )
    ```

    若想要仅在代码处调用，不考虑用户侧，可以将 `user` 设置为 `Console`，`group` 设置为 None。

    ```python
    register.execute_command(
        CommandEvent(
            event_id=f"console-{time.time()}",
            platform="console",
            self_id="Console",
            command="fetch_self_id",
            raw_message=MessageChain([MessageSegment.text(f"fetch_self_id")]),
            user=UserInfo(
                platform="system",
                user_id="Console"
            ),
            args=[]
        )
    )
    ```

## 手动接入其他功能

Coral 内置的权限系统并没有为其他功能提供快捷的接入方式，因为这些行为理论上不会被普通用户频繁使用。

如果你的功能需要权限控制，请继续阅读。

这里以 Coral 内置插件 `chat_command` 为例，它提供了用户侧的执行命令功能。

1. 注册权限

    首先，我们需要注册权限：

    ```python
    from Coral import perm_system
    perm_system.register_perm("chat_command", "Base Permission")
    perm_system.register_perm("chat_command.execute", "Allows the user to execute commands in chat")
    ```

2. 编写权限检查代码

    接下来，我们需要编写权限检查代码。

    ```python
    class ChatCommand:
        register = None
        perm_system = None
        
        def __init__(self, register, perm_system):
            self.register = register
            self.perm_system = perm_system

        async def chat_command(self, message: MessageEvent):
            ori_message = message.message
            raw_message = ori_message.to_plain_text()
            sender_user_id = message.user.user_id
            group_id = message.group.group_id if message.group else None

            if not raw_message.startswith('!'):
                return None

            logger.info(f"Received command: {raw_message}")
            if not self.perm_system.check_perm(["chat_command", "chat_command.execute"], sender_user_id, group_id):
                return None
            # ...
    ```

    这里，我们在 `chat_command` 函数中检查 `chat_command` 和 `chat_command.execute` 两个权限，并使用 `check_perm` 方法进行检查。

    若用户没有这两个权限，则直接返回 `None`，表示不执行命令。