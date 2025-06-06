import json
import logging

logger = logging.getLogger(__name__)

class OnebotAdapter:
    def __init__(self):
        logger.info("OnebotAdapter initialized")

    def build_onebot_message(self, coral_message: dict) -> str:
        logger.info("Converting Coral message to Onebot message")
        match coral_message["action"]:
            case "send_msg":
                return self.send_msg_to_onebot(coral_message)
            case "delete_msg":
                return self.delete_msg_to_onebot(coral_message)
            case "get_msg":
                return self.get_msg_to_onebot(coral_message)
            case "get_forward_msg":
                return self.get_forward_msg_to_onebot(coral_message)
            case "send_like":
                return self.send_like_to_onebot(coral_message)
            case "set_group_kick":
                return self.set_group_kick_to_onebot(coral_message)
            case "set_group_ban":
                return self.set_group_ban_to_onebot(coral_message)
            case "set_group_anonymous_ban":
                return self.set_group_anonymous_ban_to_onebot(coral_message)
            case "set_group_whole_ban":
                return self.set_group_whole_ban_to_onebot(coral_message)
            case "set_group_admin":
                return self.set_group_admin_to_onebot(coral_message)
            case "set_group_anonymous":
                return self.set_group_anonymous_to_onebot(coral_message)
            case "set_group_card":
                return self.set_group_card_to_onebot(coral_message)
            case "set_group_name":
                return self.set_group_name_to_onebot(coral_message)
            case "set_group_leave":
                return self.set_group_leave_to_onebot(coral_message)
            case "set_group_special_title":
                return self.set_group_special_title_to_onebot(coral_message)
            case "set_friend_add_request":
                return self.set_friend_add_request_to_onebot(coral_message)
            case "set_group_add_request":
                return self.set_group_add_request_to_onebot(coral_message)
            case "get_login_info":
                return self.get_login_info_to_onebot(coral_message)
            case "get_stranger_info":
                return self.get_stranger_info_to_onebot(coral_message)
            case "get_friend_list":
                return self.get_friend_list_to_onebot(coral_message)
            case "get_group_info":
                return self.get_group_info_to_onebot(coral_message)
            case "get_group_list":
                return self.get_group_list_to_onebot(coral_message)
            case "get_group_member_info":
                return self.get_group_member_info_to_onebot(coral_message)
            case "get_group_member_list":
                return self.get_group_member_list_to_onebot(coral_message)
            case "get_group_honor_info":
                return self.get_group_honor_info_to_onebot(coral_message)
            case "get_cookies":
                return self.get_cookies_to_onebot(coral_message)
            case "get_csrf_token":
                return self.get_csrf_token_to_onebot(coral_message)
            case "get_credentials":
                return self.get_credentials_to_onebot(coral_message)
            case "get_record":
                return self.get_record_to_onebot(coral_message)
            case "get_image":
                return self.get_image_to_onebot(coral_message)
            case "can_send_image":
                return self.can_send_image_to_onebot(coral_message)
            case "can_send_record":
                return self.can_send_record_to_onebot(coral_message)
            case "get_status":
                return self.get_status_to_onebot(coral_message)
            case "get_version_info":
                return self.get_version_info_to_onebot(coral_message)
            case "set_restart":
                return self.set_restart_to_onebot(coral_message)
            case "clean_cache":
                return self.clean_cache_to_onebot(coral_message)
            case _:
                logger.error(f"Unsupported message type: {coral_message['type']}")
                return None

    def send_msg_to_onebot(self, coral_message):
        message = coral_message["message"]
        sender_user_id = coral_message["sender_user_id"]
        group_id = coral_message["group_id"]
        if group_id == -1:
            data = {
                "action": "send_msg",
                "params": {
                    "message_type": "private",
                    "user_id": sender_user_id,
                    "message": message
                }
            }
            return json.dumps(data, ensure_ascii=False)
        else:
            data = {
                "action": "send_msg",
                "params": {
                    "message_type": "group",
                    "group_id": group_id,
                    "message": message
                }
            }
            return json.dumps(data, ensure_ascii=False)
        
    def delete_msg_to_onebot(self, coral_message):
        message_id = coral_message["message_id"]
        data = {
            "action": "delete_msg",
            "params": {
                "message_id": message_id
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_msg_to_onebot(self, coral_message):
        message_id = coral_message["message_id"]
        data = {
            "action": "get_msg",
            "params": {
                "message_id": message_id
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def get_forward_msg_to_onebot(self, coral_message):
        message_id = coral_message["message_id"]
        data = {
            "action": "get_forward_msg",
            "params": {
                "message_id": message_id
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def send_like_to_onebot(self, coral_message):
        user_id = coral_message["user_id"]
        times = coral_message["times"] if coral_message["times"] < 10 else 10
        data = {
            "action": "send_like",
            "params": {
                "user_id": user_id,
                "times": times
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_kick_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        reject_add_request = coral_message["reject_add_request"] if "reject_add_request" in coral_message else False
        data = {
            "action": "set_group_kick",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "reject_add_request": reject_add_request
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def set_group_ban_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        duration = coral_message["duration"] if "duration" in coral_message else 5 * 60
        data = {
            "action": "set_group_ban",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "duration": duration
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_anonymous_ban_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        duration = coral_message["duration"] if "duration" in coral_message else 5 * 60
        if 'anonymous' in coral_message:
            data = {
                "action": "set_group_anonymous_ban",
                "params": {
                    "group_id": group_id,
                    "duration": duration,
                    "anonymous": coral_message["anonymous"]
                }
            }
        elif 'flag' in coral_message:
            data = {
                "action": "set_group_anonymous_ban",
                "params": {
                    "group_id": group_id,
                    "duration": duration,
                    "flag": coral_message["flag"]
                }
            }
        else:
            logger.error("Anonymous or flag not found in set_group_anonymous_ban_to_onebot")
            return None
        return json.dumps(data, ensure_ascii=False)

    def set_group_whole_ban_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        enable = coral_message["enable"] if "enable" in coral_message else True
        data = {
            "action": "set_group_whole_ban",
            "params": {
                "group_id": group_id,
                "enable": enable
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def set_group_admin_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        enable = coral_message["enable"] if "enable" in coral_message else True
        data = {
            "action": "set_group_admin",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "enable": enable
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_anonymous_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        enable = coral_message["enable"] if "enable" in coral_message else False
        data = {
            "action": "set_group_anonymous",
            "params": {
                "group_id": group_id,
                "enable": enable
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_card_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        card = coral_message["card"] if "card" in coral_message else ""
        data = {
            "action": "set_group_card",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "card": card
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def set_group_name_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        group_name = coral_message["group_name"]
        data = {
            "action": "set_group_name",
            "params": {
                "group_id": group_id,
                "group_name": group_name
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_leave_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        is_dismiss = coral_message["is_dismiss"] if "is_dismiss" in coral_message else False
        data = {
            "action": "set_group_leave",
            "params": {
                "group_id": group_id,
                "is_dismiss": is_dismiss
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_special_title_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        special_title = coral_message["special_title"] if "special_title" in coral_message else ""
        duration = coral_message["duration"] if "duration" in coral_message else -1
        data = {
            "action": "set_group_special_title",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "special_title": special_title,
                "duration": duration
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def set_friend_add_request_to_onebot(self, coral_message):
        flag = coral_message["flag"]
        approve = coral_message["approve"] if "approve" in coral_message else True
        data = {
            "action": "set_friend_add_request",
            "params": {
                "flag": flag,
                "approve": approve
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def set_group_add_request_to_onebot(self, coral_message):
        flag = coral_message["flag"]
        sub_type = coral_message["sub_type"]
        approve = coral_message["approve"] if "approve" in coral_message else True
        reason = coral_message["reason"] if "reason" in coral_message else ""
        data = {
            "action": "set_group_add_request",
            "params": {
                "flag": flag,
                "sub_type": sub_type,
                "approve": approve,
                "reason": reason
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def get_login_info_to_onebot(self, coral_message):
        data = {
            "action": "get_login_info"
        }
        return json.dumps(data, ensure_ascii=False)

    def get_stranger_info_to_onebot(self, coral_message):
        user_id = coral_message["user_id"]
        no_cache = coral_message["no_cache"] if "no_cache" in coral_message else False
        data = {
            "action": "get_stranger_info",
            "params": {
                "user_id": user_id,
                "no_cache": no_cache
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_friend_list_to_onebot(self, coral_message):
        data = {
            "action": "get_friend_list"
        }
        return json.dumps(data, ensure_ascii=False)

    def get_group_info_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        no_cache = coral_message["no_cache"] if "no_cache" in coral_message else False
        data = {
            "action": "get_group_info",
            "params": {
                "group_id": group_id,
                "no_cache": no_cache
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def get_group_list_to_onebot(self, coral_message):
        data = {
            "action": "get_group_list"
        }
        return json.dumps(data, ensure_ascii=False)

    def get_group_member_info_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        user_id = coral_message["user_id"]
        no_cache = coral_message["no_cache"] if "no_cache" in coral_message else False
        data = {
            "action": "get_group_member_info",
            "params": {
                "group_id": group_id,
                "user_id": user_id,
                "no_cache": no_cache
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_group_member_list_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        data = {
            "action": "get_group_member_list",
            "params": {
                "group_id": group_id
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_group_honor_info_to_onebot(self, coral_message):
        group_id = coral_message["group_id"]
        type = coral_message["type"] if coral_message["type"] in ["talkative", "performer", "legend", "strong_newbie", "emotion", "all"] else "talkative"
        data = {
            "action": "get_group_honor_info",
            "params": {
                "group_id": group_id,
                "type": type
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_cookies_to_onebot(self, coral_message):
        domain = coral_message["domain"] if "domain" in coral_message else ""
        data = {
            "action": "get_cookies",
            "params": {
                "domain": domain
            }
        }
        return json.dumps(data, ensure_ascii=False)
        
    def get_csrf_token_to_onebot(self, coral_message):
        data = {
            "action": "get_csrf_token"
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_credentials_to_onebot(self, coral_message):
        domain = coral_message["domain"] if "domain" in coral_message else ""
        data = {
            "action": "get_credentials",
            "params": {
                "domain": domain
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_record_to_onebot(self, coral_message):
        file = coral_message["file"]
        out_format = coral_message["out_format"] if "out_format" in coral_message else "wav"
        data = {
            "action": "get_record",
            "params": {
                "file": file,
                "out_format": out_format
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_image_to_onebot(self, coral_message):
        file = coral_message["file"]
        data = {
            "action": "get_image",
            "params": {
                "file": file
            }
        }
        return json.dumps(data, ensure_ascii=False)

    def can_send_image_to_onebot(self, coral_message):
        data = {
            "action": "can_send_image"
        }
        return json.dumps(data, ensure_ascii=False)
    
    def can_send_record_to_onebot(self, coral_message):
        data = {
            "action": "can_send_record"
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_status_to_onebot(self, coral_message):
        data = {
            "action": "get_status"
        }
        return json.dumps(data, ensure_ascii=False)
    
    def get_version_info_to_onebot(self, coral_message):
        data = {
            "action": "get_version_info"
        }
        return json.dumps(data, ensure_ascii=False)
    
    def set_restart_to_onebot(self, coral_message):
        delay = coral_message["delay"] if "delay" in coral_message else 2000
        data = {
            "action": "set_restart",
            "params": {
                "delay": delay
            }
        }
        return json.dumps(data, ensure_ascii=False)
    
    def clean_cache_to_onebot(self, coral_message):
        data = {
            "action": "clean_cache"
        }
        return json.dumps(data, ensure_ascii=False)
    
