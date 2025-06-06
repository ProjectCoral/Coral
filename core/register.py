from collections import defaultdict, deque
import logging
import datetime
import random
import traceback
from .future import RegisterFuture
logger = logging.getLogger(__name__)

class Register:
    def __init__(self):
        self.event_queues = defaultdict(deque)
        self.commands = {}
        self.command_descriptions = {}
        self.command_permissions = {}
        self.functions = {}
        self.load_buildin_plugins = None
        self.future = RegisterFuture(self)
        self.default_events = ["coral_initialized", "coral_shutdown", "client_connected", "client_disconnected", "prepare_reply", "finish_reply"]
        self.crash_times = {}

    def hook_perm_system(self, perm_system: object):
        self.perm_system = perm_system

    def register_event(self, listener_queue: str, event_name: str, function: object, priority: int = 1):
        if listener_queue in self.event_queues and event_name in [event[0] for event in self.event_queues[listener_queue]]:
            logger.error(f"[red bold]Event [/]{event_name}[red bold] already registered in queue [/]{listener_queue}")
            return
        self.event_queues[listener_queue].append((event_name, function, priority))

    def register_command(self, command_name: str, description: str, function: object, permission: str = None):
        if command_name in self.commands:
            logger.error(f"[red bold]Command [/]{command_name}[red bold] already registered[/]")
            return
        self.commands[command_name] = function
        self.command_descriptions[command_name] = description
        if permission is not None:
            self.command_permissions[command_name] = permission

    def register_function(self, function_name: str, function: object):
        if function_name in self.functions:
            logger.error(f"[red bold]Function [/]{function_name}[red bold] already registered[/]")
            return
        self.functions[function_name] = function

    def unregister_event(self, listener_queue: str, event_name: str):
        to_remove = []
        for event, func, priority in self.event_queues[listener_queue]:
            if event == event_name:
                to_remove.append((event, func, priority))

        if to_remove:
            for item in to_remove:
                self.event_queues[listener_queue].remove(item)

    def unregister_command(self, command_name: str):
        if command_name in self.commands:
            del self.commands[command_name]
            del self.command_descriptions[command_name]
            if command_name in self.command_permissions:
                del self.command_permissions[command_name]

    def unregister_function(self, function_name: str):
        if function_name in self.functions:
            del self.functions[function_name]

    async def execute_function(self, function_name: str, *args, **kwargs):
        if function_name in self.functions:
            try:    
                result = await self.functions[function_name](*args, **kwargs)
            except Exception as e:
                logger.exception(f"[red]Error executing function {function_name}: {e}[/]")
                self.crash_record("function", function_name, str(e), traceback.format_exc())
                return None
            return result
        raise ValueError(f"Function {function_name} not found, probably you forget register it")

    def execute_command(self, command_name: str, user_id: int, group_id: int = -1, data: any = None):
        if self.perm_system is not None and command_name in self.command_permissions:
            if not self.perm_system.check_perm(self.command_permissions[command_name], user_id, group_id):
                return "You don't have permission to execute this command"
        if command_name in self.commands:
            if data is None:
                try:
                    return self.commands[command_name]()
                except Exception as e:
                    logger.exception(f"[red]Error executing command {command_name}: {e}[/]")
                    self.crash_record("command", command_name, str(e), traceback.format_exc())
                    return f"Error executing command {command_name}: {e}"
            logger.debug(f"Executing command {command_name} with data {data}")
            try:
                return self.commands[command_name](data)
            except Exception as e:
                logger.exception(f"[red]Error executing command {command_name}: {e}[/]")
                self.crash_record("command", command_name, str(e), traceback.format_exc())
                return f"Error executing command {command_name}: {e}"
        return self.no_command()
    
    def no_command(self):
        return "No command found"
    
    def get_command_description(self, command_name: str):
        return self.command_descriptions.get(command_name, "No description found")

    async def execute_event(self, event: str, *args) -> list:
        interrupted = False
        change_priority = None
        if event not in self.event_queues:
            raise ValueError(f"Event {event} not found, probably you forget register it")
        result_buffer = []
        for event_name, func, priority in self.event_queues[event]:
            logger.debug(f"Executing event {event_name} with args {args}")
            try:
                result = await func([*args, result_buffer])
            except Exception as e:
                logger.exception(f"[red]Error executing event {event_name}: {e}[/]")
                self.crash_record("event", event_name, str(e), traceback.format_exc(), event)
                result = None
            if result is not None:
                if isinstance(result, tuple) and len(result) == 3:
                    result_args, interrupt, new_priority = result
                    logger.debug(f"Event {event_name} returns {result_args}, interrupt: {interrupt}, new priority: {new_priority}")
                    if isinstance(result_args, list):
                        if isinstance(result_args[1], list):
                            result_buffer = result_args[1]
                        if result_args[0] is not None:
                            result_buffer = result_buffer.append(result_args[0])
                    elif result_args is not None:
                        result_buffer.append(result_args)
                    if interrupt:
                        interrupted = True
                        change_priority = (event_name, func, new_priority)
                        break
        if interrupted and change_priority:
            # 如果有中断，则将中断的监听器移动到队列的最前面
            self.event_queues[event].remove(change_priority)
            self.event_queues[event].appendleft(change_priority)
        if result_buffer:
            return result_buffer
        return []

    async def core_reload(self):
        for event_queue in self.event_queues.values():
            event_queue.clear()
        self.commands.clear()
        self.command_descriptions.clear()
        self.command_permissions.clear()
        self.functions.clear()
        self.crash_times.clear()
        logger.info("All events, commands, functions and permissions have been unloaded.")
        if self.load_buildin_plugins is not None:
            self.load_buildin_plugins()
        self.perm_system.save_user_perms()
        self.perm_system.registered_perms = {}
        self.perm_system.load_user_perms()
        logger.info("Coral Core has been reloaded.")

    def crash_record(self, type: str, function_name: str, error: str, traceback: str, *listener_queue):
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
            "Yet another bug has been found."
        ]
        with open(f"./logs/crash_{type}_{function_name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", "w", encoding="utf-8") as f:
            f.write(random.choice(crash_tips) + "\n")
            f.write(f"Coral Core has crashed in {type} {function_name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("----------------------------------------\n")
            f.write(f"Error: {error}\nTraceback:\n{traceback}")
        if self.crash_times[type][function_name] >= 3:
            logger.error(f"[red] Auto-disabling {type} [/]{function_name}[red] due to frequent crashes.[/]")
            match type:
                case "event":
                    self.unregister_event(listener_queue[0], function_name)
                case "command":
                    self.unregister_command(function_name)
                case "function":
                    self.unregister_function(function_name)
