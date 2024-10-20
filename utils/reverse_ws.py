import os
import json
import uvicorn
import logging
from colorama import Fore

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

async def build_reply_json(reply_item, sender_user_id, group_id):
    if reply_item is None:
        return None
    if group_id == -1:
        data = {
            "action": "send_private_msg",
            "params": {
                "user_id": sender_user_id,
                "message": reply_item
            }
        }
        return json.dumps(data, ensure_ascii=False)
    else:
        data = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": reply_item
            }
        }
        return json.dumps(data, ensure_ascii=False)

class ReverseWS:
    websocket_port = 21050
    config = None
    processing_reply = None

    def __init__(self, config, register, process_reply):
        self.app = FastAPI()
        self.config = config
        self.register = register
        self.websocket_port = self.config.get("websocket_port", 21050)
        self.process_reply = process_reply

        @self.app.websocket("/ws/api")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            logger.info("WebSocket connected")
            if 'client_connected' in self.register.event_queues:
                await self.register.execute_event('client_connected')
            try:
                while True:
                    data = await websocket.receive_text()

                    formatted_data = self.process_data(data)
                    if formatted_data is None:
                        continue

                    if 'prepare_reply' in self.register.event_queues:
                        prepared_result = await self.register.execute_event('prepare_reply', formatted_data)
                        if prepared_result['message'] is not None:
                            logger.info(f"回复{prepared_result['message']}")
                            if isinstance(prepared_result['message'], list):
                                for item in prepared_result['message']:
                                    reply_json = await build_reply_json(item, prepared_result['sender_user_id'], prepared_result['group_id'])
                                    await websocket.send_text(reply_json)
                            else:
                                reply_json = await build_reply_json(prepared_result['message'], prepared_result['sender_user_id'], prepared_result['group_id'])
                                await websocket.send_text(reply_json)
                            continue
                            
                    result = await self.process_reply(formatted_data)
                    if result is None:
                        continue
                    
                    if 'finish_reply' in self.register.event_queues:
                        await self.register.execute_event('finish_reply', result)
                    reply_item = result['message']
                    sender_user_id = result['sender_user_id']
                    group_id = result['group_id']

                    logger.info(f"回复{reply_item}")

                    if isinstance(reply_item, list):
                        for item in reply_item:
                            reply_json = await build_reply_json(item, sender_user_id, group_id)
                            await websocket.send_text(reply_json)
                    else:
                        reply_json = await build_reply_json(reply_item, sender_user_id, group_id)
                        await websocket.send_text(reply_json)

            except json.JSONDecodeError:
                logger.error(Fore.RED + "JSONDecodeError" + Fore.RESET)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                if 'client_disconnected' in self.register.event_queues:
                    await self.register.execute_event('client_disconnected')
            except Exception as e:
                raise e

    def process_data(self, data):
        try:
            data = json.loads(data)
            if 'post_type' in data and data['post_type'] == 'meta_event':
                if data['meta_event_type'] == 'lifecycle':
                    if data['sub_type'] == 'connect':
                        logger.info(f"已链接")
                        return None
                elif data['meta_event_type'] == 'heartbeat':
                    return None
            
            if 'status' in data:
                if data['status'] != 'ok':
                    logger.error(f"发送/接收数据错误：{data['status']}")
                return None
            
            elif 'post_type' in data and data['post_type'] == 'message':
                sender_user_id = data.get('sender', {}).get('user_id')
                raw_message = data['raw_message']
                if data['message_type'] == 'private':
                    group_id = -1
                    logger.info(f"私聊消息：{raw_message}，来自{sender_user_id}")
                elif data['message_type'] == 'group':
                    group_id = data.get('group_id')
                    logger.info(f"群聊消息：{raw_message}，来自{sender_user_id}，群号{group_id}")
                else:
                    logger.warning(f"未知消息类型：{data['message_type']}")
                    return None
                return {"raw_message": raw_message,"sender_user_id": sender_user_id, "group_id": group_id}
            
            else:
                logger.warning(f"未知数据类型：{data}")
                return None
        except Exception as e:
            raise e

    def start(self):
        uvicorn.run(self.app, host="127.0.0.1", port=self.websocket_port)