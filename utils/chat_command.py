import logging
from typing import Optional, List
from Coral import register, perm_system, event_bus
from Coral.protocol import MessageEvent, CommandEvent, MessageRequest, MessageChain, MessageSegment

logger = logging.getLogger(__name__)

def register_plugin() -> None:
    """
    Register the chat command plugin with the Coral system.
    
    This plugin handles command execution from chat messages starting with '!'.
    """
    chat_command_instance = ChatCommand(register, perm_system)
    event_bus.subscribe(MessageEvent, chat_command_instance.chat_command, 1)
    
    # Register permissions for chat command execution
    perm_system.register_perm("chat_command", "Base Permission")
    perm_system.register_perm("chat_command.execute", "Allows the user to execute commands in chat")
    
    logger.debug("Chat command plugin registered")

class ChatCommand:
    """Handler for chat-based command execution."""
    
    def __init__(self, register, perm_system):
        """
        Initialize the chat command handler.
        
        Args:
            register: Coral register instance
            perm_system: Coral permission system instance
        """
        self.register = register
        self.perm_system = perm_system
    
    def _parse_command(self, raw_message: str) -> tuple[str, List[str]]:
        """
        Parse a raw message into command and arguments.
        
        Args:
            raw_message: The raw message string starting with '!'
            
        Returns:
            Tuple of (command_name, arguments_list)
        """
        # Remove the '!' prefix
        command_text = raw_message[1:].strip()
        
        if not command_text:
            return "", []
        
        # Split into command and arguments
        parts = command_text.split(' ', 1)
        command = parts[0]
        args = parts[1].strip() if len(parts) > 1 else ""
        
        # Split arguments by whitespace
        args_list = args.split() if args else []
        
        return command, args_list
    
    async def chat_command(self, message: MessageEvent) -> Optional[MessageRequest]:
        """
        Handle incoming chat messages and execute commands starting with '!'.
        
        Args:
            message: The incoming message event
            
        Returns:
            MessageRequest with response or None if no command was executed
        """
        # Extract raw message text
        raw_message = message.message.to_plain_text().strip()
        
        # Check if this is a command (starts with '!')
        if not raw_message.startswith('!'):
            return None
        
        # Extract user and group information
        sender_user_id = message.user.user_id
        group_id = message.group.group_id if message.group else None
        
        logger.info(f"Received command from user {sender_user_id}: {raw_message}")
        
        # Check permissions
        if not self.perm_system.check_perm(["chat_command", "chat_command.execute"], 
                                          sender_user_id, group_id):
            logger.warning(f"User {sender_user_id} lacks permission to execute commands")
            return None
        
        # Parse command and arguments
        command, args = self._parse_command(raw_message)
        
        if not command:
            logger.warning("Empty command received")
            return MessageRequest(
                platform=message.platform,
                event_id=message.event_id,
                self_id=message.self_id,
                message=MessageChain([MessageSegment.text("Error: Empty command")]),
                user=message.user,
                group=message.group if message.group else None
            )
        
        logger.debug(f"Parsed command: '{command}' with args: {args}")
        
        # Handle special commands
        if command == "stop":
            try:
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
                logger.debug("Stop command executed")
            except Exception as e:
                logger.error(f"Error publishing stop event: {e}")
        
        # Execute the command through the register system
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
            
            logger.info(f"Command '{command}' executed successfully with args {args}")
            logger.debug(f"Command result: {send_message}")
            
            return send_message
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}", exc_info=True)
            
            # Return error message to user
            return MessageRequest(
                platform=message.platform,
                event_id=message.event_id,
                self_id=message.self_id,
                message=MessageChain([MessageSegment.text(f"Error executing command '{command}': {str(e)}")]),
                user=message.user,
                group=message.group if message.group else None
            )
