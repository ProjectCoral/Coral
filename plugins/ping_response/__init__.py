__plugin_meta__ = {
    "name": "Ping Response",
    "version": "1.0.0",
    "author": "NaivG",
    "description": "简单的Ping响应插件，当用户发送'Ping'时回复'Pong!'。",
    "compatibility": "250606"
}

from Coral import on_message
from Coral.filters import starts_with
from Coral.protocol import MessageEvent

@on_message(
    name="Ping Response",
    filters=starts_with("Ping"),
)
async def ping_response_handler(event: MessageEvent):
    return event.reply("Pong!")
