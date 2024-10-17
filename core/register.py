from collections import defaultdict, deque

class Register:
    def __init__(self):
        self.event_queues = defaultdict(deque)
        self.commands = {}
        self.command_descriptions = {}
        self.functions = {}

    def register_event(self, listener_queue, event_name, function, priority=1):
        self.event_queues[listener_queue].append((event_name, function, priority))

    def register_command(self, command_name, description, function):
        self.commands[command_name] = function
        self.command_descriptions[command_name] = description

    def register_function(self, function_name, function):
        self.functions[function_name] = function

    def unregister_event(self, listener_queue, event_name, function):
        for event, func, priority in self.event_queues[listener_queue]:
            if event == event_name and func == function:
                self.event_queues[listener_queue].remove((event, func, priority))
                break

    def unregister_command(self, command_name):
        if command_name in self.commands:
            del self.commands[command_name]
            del self.command_descriptions[command_name]

    def unregister_function(self, function_name):
        if function_name in self.functions:
            del self.functions[function_name]

    async def execute_function(self, function_name, *args, **kwargs):
        if function_name in self.functions:
            result = await self.functions[function_name](*args, **kwargs)
            return result
        raise ValueError(f"Function {function_name} not found, probably you forget register it")

    def execute_command(self, command_name, data = None):
        if command_name in self.commands:
            if data is None:
                return self.commands[command_name]()
            return self.commands[command_name](data)
        return self.no_command()
    
    def no_command(self):
        return "No command found"
    
    def get_command_description(self, command_name):
        return self.command_descriptions.get(command_name, "No description found")

    async def execute_event(self, event, *args):
        interrupted = False
        change_priority = None
        if event not in self.event_queues:
            raise ValueError(f"Event {event} not found, probably you forget register it")
        for event_name, func, priority in self.event_queues[event]:
            result = await func(event, *args)
            if result is not None:
                args = result[0]
                if isinstance(result, tuple) and len(result) == 3:
                    _, interrupt, new_priority = result
                    if interrupt:
                        interrupted = True
                        change_priority = (event_name, func, new_priority)
                        break
        if interrupted and change_priority:
            # 如果有中断，则将中断的监听器移动到队列的最前面
            self.event_queues[event].remove(change_priority)
            self.event_queues[event].appendleft(change_priority)
        return args

 