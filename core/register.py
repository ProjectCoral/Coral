from collections import defaultdict, deque
import logging
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

    def hook_perm_system(self, perm_system: object):
        self.perm_system = perm_system

    def register_event(self, listener_queue: str, event_name: str, function: object, priority: int = 1):
        self.event_queues[listener_queue].append((event_name, function, priority))

    def register_command(self, command_name: str, description: str, function: object, permission: str = None):
        self.commands[command_name] = function
        self.command_descriptions[command_name] = description
        if permission is not None:
            self.command_permissions[command_name] = permission

    def register_function(self, function_name: str, function: object):
        self.functions[function_name] = function

    def unregister_event(self, listener_queue: str, event_name: str, function: object):
        for event, func, priority in self.event_queues[listener_queue]:
            if event == event_name and func == function:
                self.event_queues[listener_queue].remove((event, func, priority))
                break

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
                raise e
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
                    raise e
            logger.debug(f"Executing command {command_name} with data {data}")
            try:
                return self.commands[command_name](data)
            except Exception as e:
                logger.exception(f"[red]Error executing command {command_name}: {e}[/]")
                raise e
        return self.no_command()
    
    def no_command(self):
        return "No command found"
    
    def get_command_description(self, command_name: str):
        return self.command_descriptions.get(command_name, "No description found")

    async def execute_event(self, event: str, *args):
        interrupted = False
        change_priority = None
        if event not in self.event_queues:
            raise ValueError(f"Event {event} not found, probably you forget register it")
        ori_args = args
        args_changed = False
        for event_name, func, priority in self.event_queues[event]:
            logger.debug(f"Executing event {event_name} with args {args}")
            try:
                result = await func(*args)
            except Exception as e:
                logger.exception(f"[red]Error executing event {event_name}: {e}[/]")
                raise e
            if result is not None:
                if isinstance(result, tuple) and len(result) == 4:
                    result_args, change_args, interrupt, new_priority = result
                    logger.debug(f"Event {event_name} returns {result_args}, change args to {change_args}, interrupt: {interrupt}, new priority: {new_priority}")
                    if change_args:
                        args = (result_args,)
                        args_changed = True
                    if interrupt:
                        interrupted = True
                        change_priority = (event_name, func, new_priority)
                        break
        if interrupted and change_priority:
            # 如果有中断，则将中断的监听器移动到队列的最前面
            self.event_queues[event].remove(change_priority)
            self.event_queues[event].appendleft(change_priority)
        if args == ori_args and not args_changed:
            return None
        if len(args) == 1 and isinstance(args[0], dict):
            return args[0]
        if len(args) == 1 and isinstance(args, tuple):
            return args[0]
        return args

    async def core_reload(self):
        for event_queue in self.event_queues.values():
            event_queue.clear()
        self.commands.clear()
        self.command_descriptions.clear()
        self.command_permissions.clear()
        self.functions.clear()
        logger.info("All events, commands, functions and permissions have been unloaded.")
        if self.load_buildin_plugins is not None:
            self.load_buildin_plugins()
        self.perm_system.save_user_perms()
        self.perm_system.registered_perms = {}
        self.perm_system.load_user_perms()
        logger.info("Coral Core has been reloaded.")