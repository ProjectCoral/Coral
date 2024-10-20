import logging

logger = logging.getLogger(__name__)

def register_plugin(register, config, perm_system):
    register.register_event('prepare_reply', 'chat_command', ChatCommand(register, perm_system).chat_command, 1)
    perm_system.register_perm("chat_command", "Base Permission")
    perm_system.register_perm("chat_command.execute", "Allows the user to execute commands in chat")

class ChatCommand:
    register = None
    perm_system = None
    
    def __init__(self, register, perm_system):
        self.register = register
        self.perm_system = perm_system

    async def chat_command(self, message, **kwargs):
        raw_message = message['raw_message']
        sender_user_id = message['sender_user_id']
        group_id = message['group_id']

        if not raw_message.startswith('!'):
            return {"message": None, "sender_user_id": sender_user_id, "group_id": group_id}, False, 1

        logger.info(f"Received command: {raw_message}")
        if not self.perm_system.check_perm(["chat_command", "chat_command.execute"], sender_user_id, group_id):
            return {"message": None, "sender_user_id": sender_user_id, "group_id": group_id}, False, 1
        parts = raw_message.split(' ', 1)
        command = parts[0][1:]
        args = parts[1].strip() if len(parts) > 1 else ""

        try:
            send_message = self.register.execute_command(command, sender_user_id, group_id, args)
            logger.debug(f"Command {command} executed with args {args} and returned {send_message}")
        except Exception as e:
            return {"message": f"Error: {e}", "sender_user_id": sender_user_id, "group_id": group_id}, False, 1

        return {"message": send_message, "sender_user_id": sender_user_id, "group_id": group_id}, False, 1
