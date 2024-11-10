import os
import json
import uvicorn
import logging
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

def build_reply_json(reply_item, sender_user_id, group_id):
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
        self.receive_data_task = None 
        self.lock = asyncio.Lock()

        @self.app.websocket("/ws/api")
        async def websocket_endpoint(websocket: WebSocket):
            logger.info("WebSocket initializing")
            self.WebsocketPort_instance = WebsocketPort(self, self.register, websocket)
            await websocket.accept()
            logger.info("WebSocket connected")
            self.WebsocketPort_instance.connected = True
            if 'client_connected' in self.register.event_queues:
                await self.register.execute_event('client_connected')
            try:
                while True:
                    if not websocket.application_state == WebSocketState.CONNECTED:
                        raise WebSocketDisconnect()
                    
                    async with self.lock:
                        if self.receive_data_task and not self.receive_data_task.done():
                            await asyncio.sleep(1)
                            continue

                        self.receive_data_task = asyncio.create_task(websocket.receive_text())
                    
                    done, pending = await asyncio.wait(
                        [self.receive_data_task]
                    )
                    if not self.receive_data_task.done():
                        await asyncio.sleep(0.5)
                        continue

                    if self.receive_data_task in done:
                        try:
                            data = self.receive_data_task.result()
                        except asyncio.CancelledError:
                            print("Task was cancelled")
                            await asyncio.sleep(0.5)
                            continue
                    else:
                        self.receive_data_task.cancel()
                        try:
                            await self.receive_data_task  # 确保任务被取消
                        except asyncio.CancelledError:
                            pass
                        continue

                    formatted_data = self.process_data(data)
                    if formatted_data is None:
                        continue

                    if 'prepare_reply' in self.register.event_queues:
                        prepared_result = await self.register.execute_event('prepare_reply', formatted_data)
                        if prepared_result['message'] is not None:
                            logger.info(f"回复{prepared_result['message']}")
                            if isinstance(prepared_result['message'], list):
                                for item in prepared_result['message']:
                                    reply_json = build_reply_json(item, prepared_result['sender_user_id'], prepared_result['group_id'])
                                    await websocket.send_text(reply_json)
                            else:
                                reply_json = build_reply_json(prepared_result['message'], prepared_result['sender_user_id'], prepared_result['group_id'])
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
                            reply_json = build_reply_json(item, sender_user_id, group_id)
                            await websocket.send_text(reply_json)
                    else:
                        reply_json = build_reply_json(reply_item, sender_user_id, group_id)
                        await websocket.send_text(reply_json)

            except json.JSONDecodeError:
                logger.error("[red]JSONDecodeError[/]")
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                self.WebsocketPort_instance.connected = False
                if 'client_disconnected' in self.register.event_queues:
                    await self.register.execute_event('client_disconnected')
            except Exception as e:
                logger.exception(f"[red]WebSocket error: {e}[/]")
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
                    logger.error(f"发送/接收数据错误： {data['status']}")
                return None
            
            elif 'post_type' in data and data['post_type'] == 'message':
                sender_user_id = data.get('sender', {}).get('user_id')
                raw_message = data['raw_message']
                if data['message_type'] == 'private':
                    group_id = -1
                    logger.info(f"私聊消息： {raw_message} ，来自 {sender_user_id} ")
                elif data['message_type'] == 'group':
                    group_id = data.get('group_id')
                    logger.info(f"群聊消息： {raw_message} ，来自 {sender_user_id} ，群号 {group_id} ")
                else:
                    logger.warning(f"未知消息类型： {data['message_type']}")
                    return None
                return {"message": raw_message,"sender_user_id": sender_user_id, "group_id": group_id}
            
            else:
                logger.warning(f"未知数据类型： {data}")
                return None
        except Exception as e:
            logger.exception(f"[red]数据处理错误: {e}[/]")
            raise e

    def start(self):
        uvicorn.run(self.app, host="127.0.0.1", port=self.websocket_port)



class WebsocketPort:
    ReverseWS_instance = None
    register = None
    websocket: WebSocket = None

    def __init__(self, ReverseWS_instance, register, websocket: WebSocket):
        self.ReverseWS_instance = ReverseWS_instance
        self.connected = False
        self.register = register
        self.websocket = websocket
        self.register.register_function('ws_send', self.ws_sender)
        self.register.register_command('send', "send message to websocket", self.command_sender)
        
    async def ws_sender(self, result, **kwargs):
        if not self.connected:
            logger.warning("WebSocket未连接")
            return None
        try:
            reply_item = result['message']
            sender_user_id = result['sender_user_id']
            group_id = result['group_id']
        except KeyError:
            logger.error("Invalid arguments.\n Usage: ws_send <{message:str|list, sender_user_id:int, group_id:int}>")
            return None
        logger.info(f"发送{reply_item}")
        if self.ReverseWS_instance.receive_data_task is not None and not self.ReverseWS_instance.receive_data_task.done():
            logger.info("正在处理消息，取消当前任务")
            self.ReverseWS_instance.receive_data_task.cancel()
            self.ReverseWS_instance.lock = asyncio.Lock()
        if isinstance(reply_item, list):
            for item in reply_item:
                reply_json = build_reply_json(item, sender_user_id, group_id)
                await self.websocket.send_text(reply_json)
        else:
            reply_json = build_reply_json(reply_item, sender_user_id, group_id)
            await self.websocket.send_text(reply_json)
        logger.info("已发送")


    def command_sender(self, *args):
        if not self.connected:
            return "WebSocket未连接"
        try:
            args_str = " ".join(args)
            message, sender_user_id, group_id = args_str.split(" ", 2)
        except ValueError:
            return "Invalid arguments.\n Usage: ws_send <{message:str|list> <sender_user_id> <group_id>"
        processed_message = {"message": message, "sender_user_id": sender_user_id, "group_id": group_id}
        asyncio.run(self.ws_sender(processed_message))
        return "已发送"