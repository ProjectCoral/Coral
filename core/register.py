from collections import defaultdict
import logging
import datetime
import random
import traceback
from typing import Union, List
from .future import RegisterFuture
from .protocol import (
    CommandEvent,
    MessageEvent,
    NoticeEvent,
    MessageRequest,
    MessageChain,
    MessageSegment,
    GenericEvent,
    MessageBase,
)
from .event_bus import EventBus
from .perm_system import PermSystem

logger = logging.getLogger(__name__)


class Register:
    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.commands = {}  # 命令名: (handler, permission)
        self.command_descriptions = {}
        self.functions = {}
        self.load_buildin_plugins: callable = None
        self.future = RegisterFuture(self)
        self.crash_times = {}
        self._event_handlers = defaultdict(
            dict
        )  # event_name: handler_func -> wrapper_func
        self.perm_system = None

        self.event_bus.subscribe(CommandEvent, self.execute_command)

    def hook_perm_system(self, perm_system: PermSystem):
        self.perm_system = perm_system
        logger.info("Permission system has been hooked with Register.")

    def register_event(
        self, event_name: str, listener_name: str, function: callable, priority: int = 1
    ):
        if (
            event_name in self._event_handlers
            and function in self._event_handlers[event_name]
        ):
            logger.error(
                f"[red bold]Event [/]{event_name}[red bold] already registered for [/]{listener_name}"
            )
            return

        async def wrapper(event: GenericEvent):
            if event.name == event_name:
                try:
                    await function()
                except Exception as e:
                    logger.exception(f"[red]Error in event handler: {e}[/]")
                    self.crash_record(
                        "event",
                        event_name,
                        str(e),
                        traceback.format_exc(),
                        listener_name,
                    )

        self._event_handlers[event_name][function] = wrapper
        self.event_bus.subscribe(GenericEvent, wrapper, priority)

    def register_command(
        self,
        command_name: str,
        description: str,
        function: callable,
        permission: Union[str, List, None] = None,
    ):
        if command_name in self.commands:
            logger.warning(
                f"[yellow]Command [/]{command_name}[yellow] already registered, overwriting...[/]"
            )
        self.commands[command_name] = function, permission
        self.command_descriptions[command_name] = description

    def register_function(self, function_name: str, function: callable):
        if function_name in self.functions:
            logger.error(
                f"[red bold]Function [/]{function_name}[red bold] already registered[/]"
            )
            return
        self.functions[function_name] = function

    def unregister_event(self, listener_queue: str, event_name: str):
        """取消注册事件"""
        if event_name in self._event_handlers:
            for function, wrapper in self._event_handlers[event_name].items():
                self.event_bus.unsubscribe(GenericEvent, wrapper)
            del self._event_handlers[event_name]

    def unregister_command(self, command_name: str):
        """取消注册命令"""
        if command_name in self.commands:
            del self.commands[command_name]
        if command_name in self.command_descriptions:
            del self.command_descriptions[command_name]

    def unregister_function(self, function_name: str):
        """取消注册功能函数"""
        if function_name in self.functions:
            del self.functions[function_name]

    async def execute_function(self, function_name: str, *args, **kwargs):
        if function_name in self.functions:
            try:
                result = await self.functions[function_name](*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"[red]Error executing function {function_name}: {e}[/]"
                )
                self.crash_record(
                    "function", function_name, str(e), traceback.format_exc()
                )
                return None
            return result
        raise ValueError(
            f"Function {function_name} not found, probably you forget register it"
        )

    async def execute_command(self, event: CommandEvent) -> Union[MessageBase, None]:
        """执行命令"""
        logger.debug(
            f"Executing command {event.command} from {event.user.user_id} in {event.group.group_id if event.group else None} with args {event.args}"
        )

        if event.command not in self.commands:
            return MessageRequest(
                platform=event.platform,
                event_id=event.event_id,
                self_id=event.self_id,
                message=MessageChain([MessageSegment.text(self.no_command())]),
                user=event.user,
                group=event.group if event.group else None,
            )

        handler, permission = self.commands[event.command]

        # 权限检查
        if permission and not self.perm_system.check_perm(
            permission, event.user.user_id, event.group.group_id if event.group else -1
        ):
            # return "Permission denied"
            return MessageRequest(
                platform=event.platform,
                event_id=event.event_id,
                self_id=event.self_id,
                message=MessageChain([MessageSegment.text("Permission denied")]),
                user=event.user,
                group=event.group if event.group else None,
            )

        try:
            result = await handler(event)
            if isinstance(result, MessageBase):
                return result
            else:
                return MessageRequest(
                    platform=event.platform,
                    event_id=event.event_id,
                    self_id=event.self_id,
                    message=MessageChain([MessageSegment.text(result)]),
                    user=event.user,
                    group=event.group if event.group else None,
                )

        except Exception as e:
            logger.exception(f"[red]Error executing command {event.command}: {e}[/]")
            self.crash_record("command", event.command, str(e), traceback.format_exc())
            return MessageRequest(
                platform=event.platform,
                event_id=event.event_id,
                self_id=event.self_id,
                message=MessageChain(
                    [
                        MessageSegment.text(
                            f"Error executing command {event.command}: {e}"
                        )
                    ]
                ),
                user=event.user,
                group=event.group if event.group else None,
            )

    def no_command(self):
        return "No command found"

    def get_command_description(self, command_name: str):
        return self.command_descriptions.get(command_name, "No description found")

    async def execute_event(self, event_name: str, platform: str = "coral"):
        """执行事件（通过发布GenericEvent）"""

        event = GenericEvent(name=event_name, platform=platform)

        await self.event_bus.publish(event)

    async def core_reload(self):

        for _, handlers in self._event_handlers.items():
            for _, wrapper in handlers.items():
                self.event_bus.unsubscribe(GenericEvent, wrapper)
        self._event_handlers.clear()
        self.event_bus._subscribers[MessageEvent].clear()
        self.event_bus._subscribers[NoticeEvent].clear()
        self.commands.clear()
        self.command_descriptions.clear()
        self.functions.clear()
        self.crash_times.clear()
        self.perm_system.save_user_perms()
        self.perm_system.registered_perms = {}
        logger.info(
            "All events, commands, functions and permissions have been unloaded."
        )
        self.perm_system.load_user_perms()
        if self.load_buildin_plugins:
            self.load_buildin_plugins()
        logger.info("Coral Core has been reloaded.")

    def crash_record(
        self, type: str, function_name: str, error: str, traceback: str, *listener_queue
    ):
        if type not in self.crash_times:
            self.crash_times[type] = {}
        if function_name not in self.crash_times[type]:
            self.crash_times[type][function_name] = 0
        self.crash_times[type][function_name] += 1
        crash_tips = [
            "Oops!",
            "No worries, Coral is still running.",
            "No, this shouldn't happen.",
            "Smells like a *bug*.",
            "I'm sorry, Dave. I'm afraid I can't do that.",
            "What the heck is going on here?",
            "Houston, we have a problem.",
            "You're not supposed to be here.",
            "Yet another bug has been found.",
        ]
        with open(
            f"./logs/crash_{type}_{function_name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(random.choice(crash_tips) + "\n")
            f.write(
                f"Coral Core has crashed in {type} {function_name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write("----------------------------------------\n")
            f.write(f"Error: {error}\nTraceback:\n{traceback}")
        if self.crash_times[type][function_name] >= 3:
            logger.error(
                f"[red] Auto-disabling {type} [/]{function_name}[red] due to frequent crashes.[/]"
            )
            match type:
                case "event":
                    self.unregister_event(listener_queue[0], function_name)
                case "command":
                    self.unregister_command(function_name)
                case "function":
                    self.unregister_function(function_name)
