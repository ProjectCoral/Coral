from enum import Enum

class TypeElement:
    """类型元素基类"""
    def super_type(self):
        return self.__class__

class GroupEventType(TypeElement, Enum):
    """
    ## 群组事件类型

    - Group.UPLOAD 群文件上传
    - Group.SET_ADMIN 设置群管理员
    - Group.UNSET_ADMIN 取消群管理员
    - Group.MEMBER_DECREASE 群成员减少
    - Group.MEMBER_INCREASE 群成员增加
    - Group.BAN 群禁言
    - Group.LIFT_BAN 解除群禁言
    - Group.RECALL 撤回消息
    - Group.POKE 群戳一戳
    - Group.HONOR 群成员荣誉变更
    - Group.ADD_REQUEST 加群请求
    - Group.INVITE_REQUEST 邀请入群请求
    """
    UPLOAD = "group_upload"
    SET_ADMIN = "set_group_admin"
    UNSET_ADMIN = "unset_group_admin"
    MEMBER_DECREASE = "group_decrease"
    MEMBER_INCREASE = "group_increase"
    BAN = "group_ban"
    LIFT_BAN = "group_lift_ban"
    RECALL = "group_recall"
    POKE = "group_poke"
    HONOR = "group_honor"
    ADD_REQUEST = "group_add_request"
    INVITE_REQUEST = "group_invite_request"

class FriendEventType(TypeElement, Enum):
    """
    ## 好友事件类型
    
    - Friend.FRIEND_ADD 好友添加
    - Friend.RECALL 好友消息撤回
    - Friend.ADD_REQUEST 好友添加请求
    """
    FRIEND_ADD = "friend_add"
    RECALL = "friend_recall"
    ADD_REQUEST = "friend_add_request"

class BotEventType(TypeElement, Enum):
    """
    ## 机器人事件类型

    - Bot.LIFECYCLE 生命周期事件
    - Bot.HEARTBEAT 心跳事件
    """
    LIFECYCLE = "lifecycle"
    HEARTBEAT = "heartbeat"
    
class EventType:
    """事件类型基类"""
    Group = GroupEventType
    Friend = FriendEventType
    Bot = BotEventType

class MessageActionType(TypeElement, Enum):
    """
    ## 消息动作类型
    
    - Message.SEND_MSG 发送消息
    - Message.DELETE_MSG 撤回消息
    - Message.GET_MSG 获取消息详情
    - Message.GET_FORWARD_MSG 获取合并转发消息
    """
    SEND_MSG = "send_msg"
    DELETE_MSG = "delete_msg"
    GET_MSG = "get_msg"
    GET_FORWARD_MSG = "get_forward_msg"

class GroupActionType(TypeElement, Enum):
    """
    ## 群组动作类型

    - Group.KICK 群成员踢出
    - Group.BAN 群成员禁言
    - Group.ANONYMOUS_BAN 匿名用户禁言
    - Group.WHOLE_BAN 群全员禁言
    - Group.SET_ADMIN 群成员设置管理员
    - Group.SET_CARD 群成员设置群名片
    - Group.SET_NAME 群设置群名
    - Group.LEAVE 群成员退群
    - Group.SET_SPECIAL_TITLE 群成员设置专属头衔
    - Group.ADD_REQUEST 群组添加请求
    - Group.GET_INFO 获取群信息
    - Group.GET_MEMBER_LIST 获取群成员列表
    - Group.GET_MEMBER_INFO 获取群成员信息
    """
    KICK = "set_group_kick"
    BAN = "set_group_ban"
    ANONYMOUS_BAN = "set_group_anonymous_ban"
    WHOLE_BAN = "set_group_whole_ban"
    SET_ADMIN = "set_group_admin"
    SET_CARD = "set_group_card"
    SET_NAME = "set_group_name"
    LEAVE = "set_group_leave"
    SET_SPECIAL_TITLE = "set_group_special_title"
    ADD_REQUEST = "set_group_add_request"
    GET_INFO = "get_group_info"
    GET_MEMBER_LIST = "get_group_member_list"
    GET_MEMBER_INFO = "get_group_member_info"

class FriendActionType(TypeElement, Enum):
    """
    ## 好友动作类型

    - Friend.SEND_LIKE 点赞
    - Friend.ADD_REQUEST 发送好友请求
    - Friend.GET_LIST 获取好友列表
    """
    SEND_LIKE = "send_like"
    ADD_REQUEST = "set_friend_add_request"
    GET_LIST = "get_friend_list"

class BotActionType(TypeElement, Enum):
    """
    ## 机器人动作类型

    - Bot.GET_LOGIN_INFO 获取登录信息
    - Bot.GET_STRANGER_INFO 获取陌生人信息
    - Bot.GET_FRIEND_LIST 获取好友列表
    - Bot.GET_GROUP_LIST 获取群列表
    - Bot.GET_COOKIES 获取Cookies
    - Bot.GET_CSRF_TOKEN 获取CSRF Token
    - Bot.GET_CREDENTIALS 获取凭据
    - Bot.GET_RECORD 获取语音
    - Bot.GET_IMAGE 获取图片
    - Bot.CAN_SEND_IMAGE 能否发送图片
    - Bot.CAN_SEND_RECORD 能否发送语音
    - Bot.GET_STATUS 获取Bot状态
    - Bot.GET_VERSION 获取Bot版本
    - Bot.SET_RESTART 重启协议
    - Bot.CLEAN_CACHE 清理缓存
    """
    GET_LOGIN_INFO = "get_login_info"
    GET_STRANGER_INFO = "get_stranger_info"
    GET_FRIEND_LIST = "get_friend_list"
    GET_GROUP_LIST = "get_group_list"
    GET_COOKIES = "get_cookies"
    GET_CSRF_TOKEN = "get_csrf_token"
    GET_CREDENTIALS = "get_credentials"
    GET_RECORD = "get_record"
    GET_IMAGE = "get_image"
    CAN_SEND_IMAGE = "can_send_image"
    CAN_SEND_RECORD = "can_send_record"
    GET_STATUS = "get_status"
    GET_VERSION = "get_version"
    SET_RESTART = "set_restart"
    CLEAN_CACHE = "clean_cache"

class ActionType:
    """动作类型基类"""
    Group = GroupActionType
    Friend = FriendActionType
    Bot = BotActionType
    Message = MessageActionType
