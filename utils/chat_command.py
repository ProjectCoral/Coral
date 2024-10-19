import logging

logger = logging.getLogger(__name__)

def register_event(register, config):
    register.register_event('prepare_reply', 'chat_command', ChatCommand(register).chat_command, 1)

class ChatCommand:
    register = None
    def __init__(self, register):
        self.register = register

    async def chat_command(self, message):
        raw_message = message['raw_message']
        sender_user_id = message['sender_user_id']
        group_id = message['group_id']

        if not raw_message.startswith('!'):
            return {"message": None, "sender_user_id": sender_user_id, "group_id": group_id}, False, 1
        
        logger.info(f"Received command: {raw_message}")
        command = raw_message.split(' ')[0][1:]
        args = raw_message.split(' ')[1:]

        send_message = self.register.execute_command(command, args)

        return {"message": send_message, "sender_user_id": sender_user_id, "group_id": group_id}, False, 1
