import logging

logger = logging.getLogger(__name__)

# Future feature for Coral

class RegisterFuture:
    def __init__(self, register: object):
        self.register = register
        logger.info(f"Loaded future feature for Register.")

    def register_command(self, command_name: str, description: str, permission: str = None):
        def decorator(func):
            self.register.register_command(command_name, description, func, permission)
            return func
        return decorator

    def register_function(self, function_name: str):
        def decorator(func):
            self.register.register_function(function_name, func)
            return func
        return decorator

    def register_event(self, listener_queue: str, event_name: str, priority: int = 1):
        def decorator(func):
            self.register.register_event(listener_queue, event_name, func, priority)
            return func