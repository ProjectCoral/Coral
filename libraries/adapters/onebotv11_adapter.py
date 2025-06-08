import logging
import json
from typing import Any, Dict, Optional
from core.protocol import MessageEvent, ActionRequest, MessageRequest, MessageChain, MessageSegment, UserInfo, GroupInfo, NoticeEvent, BotResponse
from core.adapter import BaseAdapter
from core.driver import BaseDriver
from Coral import config as coral_config

logger = logging.getLogger(__name__)

class Onebotv11Adapter(BaseAdapter):
    """OneBot V11协议适配器"""
    
    def __init__(self, driver: BaseDriver, adapter_name: str, config: Dict[str, Any]):
        super().__init__(driver, adapter_name, config)
        self.self_id = coral_config.get('self_id', '')
        logger.info(f"OneBotV11 Adapter initialized for bot: {self.self_id}")
    
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理来自驱动器的原始OneBot事件"""
        try:
            event = self.convert_to_protocol(raw_data)
            if event:
                await self.publish_event(event)
        except Exception as e:
            logger.error(f"Error handling incoming event: {e}", exc_info=True)
    
    def convert_to_protocol(self, event: Dict[str, Any]) -> Optional[MessageEvent]:
        """将OneBot原生事件转换为协议事件"""
        post_type = event.get('post_type')
        
        if post_type == 'message':
            return self._handle_message_event(event)
        elif post_type == 'notice':
            return self._handle_notice_event(event)
        # 其他事件类型可以继续扩展
        else:
            logger.debug(f"Unhandled event type: {post_type}")
            return None
    
    def _handle_message_event(self, event: Dict) -> MessageEvent:
        """处理消息事件"""
        message_chain = MessageChain()
        if isinstance(event['message'], list):
            for seg in event['message']:
                if seg['type'] == 'text':
                    message_chain.append(MessageSegment.text(seg['data']['text']))
                elif seg['type'] == 'image':
                    message_chain.append(MessageSegment.image(seg['data']['url']))
                elif seg['type'] == 'at':
                    message_chain.append(MessageSegment.at(seg['data']['qq']))
        elif isinstance(event['message'], str):
            message_chain.append(MessageSegment.text(event['message']))
        
        user = UserInfo(
            platform=self.name,
            user_id=str(event.get('user_id', '')),
            nickname=event.get('sender', {}).get('nickname', '')
        )
        
        group = None
        if 'group_id' in event:
            group = GroupInfo(
                platform=self.name,
                group_id=str(event['group_id']),
                name=event.get('group_name', '')
            )
        
        return MessageEvent(
            event_id=str(event.get('message_id', event.get('time', 0))),
            platform=self.name,
            self_id=self.self_id,
            message=message_chain,
            user=user,
            group=group,
            raw=event
        )
    
    def _handle_notice_event(self, event: Dict) -> NoticeEvent:
        """处理通知事件"""
        notice_type = event.get('notice_type')
        user = UserInfo(
            platform=self.name,
            user_id=str(event.get('user_id', ''))
        )
        
        group = None
        if 'group_id' in event:
            group = GroupInfo(
                platform=self.name,
                group_id=str(event['group_id'])
                )
        
        # 群成员增加事件
        if notice_type == 'group_increase':
            return NoticeEvent(
                event_id=f"{event['time']}_{notice_type}",
                platform=self.name,
                self_id=self.self_id,
                type="group_member_increase",
                user=user,
                group=group,
                operator=UserInfo(
                    platform=self.name,
                    user_id=str(event.get('operator_id', ''))
                ),
                raw=event
            )
        # 其他通知类型可以继续扩展
        
        return None
    
    async def handle_outgoing_action(self, action: ActionRequest):
        """处理主动动作请求"""
        try:
            # 根据动作类型构建OneBot API请求
            api_request = {
                'action': action.type,
                'params': action.data
            }
            
            # 添加机器人ID
            api_request['params']['self_id'] = self.self_id
            
            # 通过驱动器发送请求
            await self.driver.send_action(api_request)
            
            # 返回成功响应
            return BotResponse(success=True, message="Action sent")
        except Exception as e:
            logger.error(f"Error handling outgoing action: {e}")
            return BotResponse(success=False, message=str(e))
    
    async def handle_outgoing_message(self, message: MessageRequest):
        """处理消息回复"""
        try:
            # 构建OneBot消息格式
            onebot_message = []
            for seg in message.message.segments:
                if seg.type == 'text':
                    onebot_message.append({
                        'type': 'text',
                        'data': {'text': seg.data}
                    })
                elif seg.type == 'image':
                    onebot_message.append({
                        'type': 'image',
                        'data': {'file': seg.data.get('url', '')}
                    })
                elif seg.type == 'at':
                    onebot_message.append({
                        'type': 'at',
                        'data': {'qq': seg.data.get('user_id', '')}
                    })
            
            # 构建API参数
            params = {
                'message': onebot_message,
                'message_type': 'group' if message.group else 'private'
            }
            
            # 设置接收者
            if message.group:
                params['group_id'] = message.group.group_id
            else:
                params['user_id'] = message.user.user_id
            
            # 构建API请求
            api_request = {
                'action': 'send_msg',
                'params': params
            }
            
            # 通过驱动器发送请求
            await self.driver.send_action(api_request)
            
            # 返回成功响应
            return BotResponse(success=True, message="Message sent")
        except Exception as e:
            logger.error(f"Error handling outgoing message: {e}")
            return BotResponse(success=False, message=str(e))