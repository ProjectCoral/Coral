import logging
from typing import Any, Dict, Union
from Coral.protocol import (
    MessageEvent, 
    ActionRequest, 
    MessageRequest, 
    MessageChain, 
    MessageSegment, 
    UserInfo, 
    GroupInfo, 
    NoticeEvent, 
    BotResponse,
    ShareType
)
from Coral.adapter import BaseAdapter
from Coral import config as coral_config

logger = logging.getLogger(__name__)


class Onebotv11Adapter(BaseAdapter):
    """OneBot V11协议适配器"""
    PROTOCOL = "onebotv11"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.self_id = coral_config.get('self_id', '')
        logger.info(f"OneBotV11 Adapter initialized")
    
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理来自驱动器的原始OneBot事件"""
        try:
            event = self.convert_to_protocol(raw_data)
            if event:
                await self.publish_event(event)
        except Exception as e:
            logger.error(f"Error handling incoming event: {e}", exc_info=True)
    
    def convert_to_protocol(self, event: Dict[str, Any]) -> Union[MessageEvent, NoticeEvent, None]:
        """将OneBot原生事件转换为协议事件"""
        post_type = event.get('post_type')
        
        if post_type == 'message':
            return self._handle_message_event(event)
        elif post_type == 'notice':
            return self._handle_action_event(event)
        elif post_type == 'request':
            # 处理请求事件（如加好友、加群请求）
            logger.debug(f"Request event received: {event}")
            return None
        elif post_type == 'meta_event':
            # 处理元事件（如心跳包）
            logger.debug(f"Meta event received: {event}")
            # 处理连接事件
            if event.get('meta_event_type') == 'lifecycle' and event.get('sub_type') == 'connect':
                self_id = str(event.get('self_id', self.self_id))
                logger.info(f"Connected to bot {self_id}")
            return None
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
                elif seg['type'] == 'record':
                    # OneBot的record对应Coral的audio，且record=True表示是录音
                    message_chain.append(MessageSegment.audio(seg['data'].get('url', ''), record=True))
                elif seg['type'] == 'video':
                    message_chain.append(MessageSegment.video(seg['data'].get('url', '')))
                elif seg['type'] == 'share':
                    # OneBot的share对应Coral的website类型分享
                    message_chain.append(MessageSegment.share_website(
                        seg['data'].get('title', ''),
                        seg['data'].get('url', '')
                    ))
                elif seg['type'] == 'location':
                    # OneBot的location对应Coral的location类型分享
                    try:
                        lon = float(seg['data'].get('lon', 0))
                        lat = float(seg['data'].get('lat', 0))
                        message_chain.append(MessageSegment.share_location(lon, lat))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid location data: {seg['data']}")
                elif seg['type'] == 'music':
                    # OneBot的music对应Coral的music类型分享
                    music_type = seg['data'].get('type', '')
                    if music_type != 'custom':  # 只处理平台音乐，不处理自定义音乐
                        message_chain.append(MessageSegment.share_music(
                            '',  # 名称未知
                            music_type,
                            seg['data'].get('id', '')
                        ))
                    else:
                        logger.debug(f"Ignoring custom music share: {seg['data']}")
                else:
                    logger.debug(f"Unhandled message segment type: {seg['type']}")
        elif isinstance(event['message'], str):
            message_chain.append(MessageSegment.text(event['message']))
        
        logger.debug(f"Message event received: {event}")
        
        user = UserInfo(
            platform=self.PROTOCOL,
            user_id=str(event.get('user_id', '')),
            nickname=event.get('sender', {}).get('nickname', '')
        )
        
        group = None
        if 'group_id' in event:
            group = GroupInfo(
                platform=self.PROTOCOL,
                group_id=str(event['group_id']),
                name=event.get('group_name', '')
            )
        
        return MessageEvent(
            event_id=str(event.get('message_id', event.get('time', 0))),
            platform=self.PROTOCOL,
            self_id=str(event.get('self_id', self.self_id)),
            message=message_chain,
            user=user,
            group=group,
            raw=event
        )
    
    def _handle_action_event(self, event: Dict) -> Union[NoticeEvent, None]:
        """处理动作事件（原通知事件）"""
        notice_type = event.get('notice_type')
        if not notice_type:
            logger.debug(f"Invalid action event: {event}")
            return None
        logger.debug(f"Action event received: {event}")
        user = UserInfo(
            platform=self.PROTOCOL,
            user_id=str(event.get('user_id', ''))
        )

        group = None
        if 'group_id' in event:
            group = GroupInfo(
                platform=self.PROTOCOL,
                group_id=str(event['group_id'])
                )
        
        operator = None
        if 'operator_id' in event:
            operator = UserInfo(
                platform=self.PROTOCOL,
                user_id=str(event['operator_id'])
            )
        
        return NoticeEvent(
            event_id=f"{event['time']}_{notice_type}",
            platform=self.PROTOCOL,
            self_id=str(event.get('self_id', self.self_id)),
            type=notice_type,  # 直接使用OneBot原生类型
            user=user,
            group=group,
            operator=operator,
            raw=event
        )
    
    async def handle_outgoing_action(self, action: ActionRequest) -> Union[BotResponse, None]:
        """处理主动动作请求"""
        try:
            # 根据动作类型构建OneBot API请求
            api_request = {
                'action': action.type.value,  # 获取枚举值
                'params': action.data
            }
            
            # 添加机器人ID
            api_request['params']['self_id'] = action.self_id
            
            # 通过驱动器发送请求
            await self.send_to_driver(api_request)
            
            # 返回成功响应
            return BotResponse(success=True, message="Action sent")
        except Exception as e:
            logger.error(f"Error handling outgoing action: {e}")
            return BotResponse(success=False, message=str(e))
    
    async def handle_outgoing_message(self, message: MessageRequest) -> Union[BotResponse, None]:
        """处理消息回复"""
        try:
            onebot_message = []
            if message.at_sender and message.user:
                onebot_message.append({
                    'type': 'at',
                    'data': {'qq': message.user.user_id}
                })

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
                    }) if isinstance(seg.data, dict) else None
                elif seg.type == 'at':
                    onebot_message.append({
                        'type': 'at',
                        'data': {'qq': seg.data.get('user_id', '')}
                    }) if isinstance(seg.data, dict) else None
                elif seg.type == 'audio':
                    # OneBot只支持约60s的语音录音，不支持普通音频文件
                    if isinstance(seg.data, dict) and seg.data.get('record', False):
                        # 只有录音可以发送
                        onebot_message.append({
                            'type': 'record',
                            'data': {'file': seg.data.get('url', '')}
                        })
                    else:
                        logger.warning("OneBot只支持约60s的语音录音，不支持普通音频文件，已忽略")
                elif seg.type == 'video':
                    onebot_message.append({
                        'type': 'video',
                        'data': {'file': seg.data.get('url', '')}
                    }) if isinstance(seg.data, dict) else None
                elif seg.type == 'share':
                    # 需要根据share的类型进行转换
                    if isinstance(seg.data, dict):
                        share_data = seg.data
                        share_type = share_data.get('type', '')
                        
                        if share_type == ShareType.WEBSITE.value:
                            onebot_message.append({
                                'type': 'share',
                                'data': {
                                    'url': share_data.get('url', ''),
                                    'title': share_data.get('name', '')
                                }
                            })
                        elif share_type == ShareType.MUSIC.value:
                            onebot_message.append({
                                'type': 'music',
                                'data': {
                                    'type': share_data.get('platform', ''),
                                    'id': share_data.get('id', '')
                                }
                            })
                        elif share_type == ShareType.LOCATION.value:
                            onebot_message.append({
                                'type': 'location',
                                'data': {
                                    'lon': str(share_data.get('lon', 0)),
                                    'lat': str(share_data.get('lat', 0))
                                }
                            })
                        elif share_type == ShareType.VIDEO.value:
                            logger.warning(f"OneBot不支持视频分享类型，已忽略")
                        else:
                            logger.warning(f"未知的分享类型: {share_type}，已忽略")
                    else:
                        logger.warning(f"Invalid share data format: {seg.data}")
                else:
                    logger.debug(f"Unhandled message segment type: {seg.type}")
            
            # 构建API参数
            params = {
                'message': onebot_message,
                'message_type': 'group' if message.group else 'private'
            }
            
            # 设置接收者
            if message.group:
                if not message.group.group_id.isdigit():
                    logger.warning(f"Onebotv11 requires numeric group ID, but got {type(message.group.group_id)}")
                    return BotResponse(success=False, message=f"Invalid group ID")
                params['group_id'] = message.group.group_id
            else:
                if message.user is None or not message.user.user_id.isdigit():
                    logger.warning("Onebotv11 requires numeric user ID, but got %s", type(message.user.user_id) if message.user else "None")
                    return BotResponse(success=False, message=f"Invalid user ID")
                params['user_id'] = message.user.user_id if message.user else None # 不应该出现这种情况
            
            # 构建API请求
            api_request = {
                'action': 'send_msg',
                'params': params
            }
            
            # 通过驱动器发送请求
            await self.send_to_driver(api_request)
            
            # 返回成功响应
            return BotResponse(success=True, message="Message sent")
        except Exception as e:
            logger.error(f"Error handling outgoing message: {e}")
            return BotResponse(success=False, message=str(e))
