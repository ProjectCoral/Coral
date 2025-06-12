import logging

logger = logging.getLogger(__name__)


class RegisterFuture:
    def __init__(self, register: object):
        self.register = register
        logger.info(f"Loaded future feature for Register.")

    def register_command(
        self, command_name: str, description: str, permission: str = None
    ):
        def decorator(func):
            self.register.register_command(command_name, description, func, permission)
            return func

        return decorator

    def register_function(self, function_name: str):
        def decorator(func):
            self.register.register_function(function_name, func)
            return func

        return decorator

    def register_event(self, event_name: str, listener_name: str, priority: int = 1):
        def decorator(func):
            self.register.register_event(event_name, listener_name, func, priority)
            return func

        return decorator
