import os
import logging

logger = logging.getLogger("test_plugin")

def register_event(register, config):
    # register event handler for the test plugin
    register.register_event('client_connected', 'test_event_handler', TestEventHandler(register, config).handle_event, 1)

class TestEventHandler:
    register = None
    config = None

    def __init__(self, register, config):
        self.register = register
        self.config = config
        logger.info("Test event handler initialized")

    async def handle_event(self):
        logger.info("Client connected , Test event handler called")
        # do something here
        plugins = self.register.execute_command('plugins')
        logger.info(f"{plugins}")
        return None, False, 1