import os
import logging

def register_event(register, config):
    # register event handler for the test plugin
    register.register_event('client_connected', 'test_event_handler', TestEventHandler(register, config).handle_event, 1)

class TestEventHandler:
    register = None
    config = None

    def __init__(self, register, config):
        self.register = register
        self.config = config

    async def handle_event(self):
        logging.info("Client connected , Test event handler called")
        # do something here
        plugins = self.register.execute_command('plugins')
        logging.info(f"{plugins}")
        return 0, False, 1