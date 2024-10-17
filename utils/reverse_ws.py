import os
import json
import uvicorn
import logging

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

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

    def __init__(self, config, process_reply):
        self.app = FastAPI()
        self.config = config
        self.websocket_port = self.config.get("websocket_port", 21050)
        self.process_reply = process_reply

        @self.app.websocket("/ws/api")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            logging.info("WebSocket connected")
            try:
                while True:
                    data = await websocket.receive_text()

                    formatted_data = self.process_data(data)
                    if formatted_data is None:
                        continue

                    result = await self.process_reply(formatted_data)
                    if result is None:
                        continue

                    reply_item, sender_user_id, group_id = result

                    logging.info(f"回复{reply_item}")
                    reply_json = await build_reply_json(reply_item, sender_user_id, group_id)
                    await websocket.send_text(reply_json)

            except json.JSONDecodeError:
                logging.error("JSONDecodeError")
            except WebSocketDisconnect:
                logging.info("WebSocket disconnected")
            except Exception as e:
                raise e

    def process_data(self, data):
        try:
            data = json.loads(data)
            if 'post_type' in data and data['post_type'] == 'meta_event':
                if data['meta_event_type'] == 'lifecycle':
                    if data['sub_type'] == 'connect':
                        logging.info(f"已链接")
                        return None
                elif data['meta_event_type'] == 'heartbeat':
                    return None
                
            elif 'post_type' in data and data['post_type'] == 'message':
                sender_user_id = data.get('sender', {}).get('user_id')
                raw_message = data['raw_message']
                if data['message_type'] == 'private':
                    group_id = -1
                    logging.info(f"私聊消息：{raw_message}，来自{sender_user_id}")
                elif data['message_type'] == 'group':
                    group_id = data.get('group_id')
                    logging.info(f"群聊消息：{raw_message}，来自{sender_user_id}，群号{group_id}")
                else:
                    logging.warning(f"未知消息类型：{data['message_type']}")
                    return None
                return {"raw_message": raw_message,"sender_user_id": sender_user_id, "group_id": group_id}
            
            else:
                logging.warning(f"未知数据类型：{data}")
                return None
        except Exception as e:
            raise e

    def start(self):
        uvicorn.run(self.app, host="127.0.0.1", port=self.websocket_port)