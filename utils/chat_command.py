import logging
from Coral import register, perm_system, event_bus, MessageEvent, CommandEvent, MessageRequest, MessageChain, MessageSegment

logger = logging.getLogger(__name__)

def register_plugin():
    # register.register_event('prepare_reply', 'chat_command', ChatCommand(register, perm_system).chat_command, 1)
    event_bus.subscribe(MessageEvent, ChatCommand(register, perm_system).chat_command, 1)
    perm_system.register_perm("chat_command", "Base Permission")
    perm_system.register_perm("chat_command.execute", "Allows the user to execute commands in chat")

class ChatCommand:
    def __init__(self, register, perm_system):
        self.register = register
        self.perm_system = perm_system

    async def chat_command(self, message: MessageEvent):
        ori_message = message.message
        raw_message = ori_message.to_plain_text()
        sender_user_id = message.user.user_id
        group_id = message.group.group_id if message.group else None

        if not raw_message.startswith('!'):
            return None

        logger.info(f"Received command: {raw_message}")
        if not self.perm_system.check_perm(["chat_command", "chat_command.execute"], sender_user_id, group_id):
            return None
        parts = raw_message.split(' ', 1)
        command = parts[0][1:]
        args = parts[1].strip() if len(parts) > 1 else ""
        args = args.split() if args else []

        try:
            if command == "stop":
                await event_bus.publish(
                    MessageRequest(
                        platform=message.platform,
                        event_id=message.event_id,
                        self_id=message.self_id,
                        message=MessageChain([MessageSegment.text("Stopping Coral...")]),
                        user=message.user,
                        group=message.group if message.group else None
                    )
                )
        except Exception as e:
            pass

        try:
            send_message = await self.register.execute_command(
                CommandEvent(
                    event_id=message.event_id,
                    platform=message.platform,
                    self_id=message.self_id,
                    time=message.time,
                    user=message.user,
                    group=message.group if message.group else None,
                    command=command,
                    args=args,
                    raw_message=message.message
                )
            )
            logger.debug(f"Command {command} executed with args {args} and returned {send_message}")
        except Exception as e:
            return MessageRequest(
                platform=message.platform,
                event_id=message.event_id,
                self_id=message.self_id,
                message=MessageChain([MessageSegment.text(f"Error executing command: {e}")]),
                user=message.user,
                group=message.group if message.group else None
            )

        return send_message
