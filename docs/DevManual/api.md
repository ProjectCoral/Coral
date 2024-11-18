# Coral API 接口

目前 Coral 的返回数据要求如下：

- 函数返回值：函数的返回值没有特殊要求，可以是任意类型，但推荐为 `dict` 。
- 命令返回值：命令的返回值必须为 `str`，表示命令执行的结果。
- 事件返回值：事件的返回值可以为任意类型，或是 `list`，表示事件更改了 `result_buffer` 回复缓冲区中的数据。

若你想要发送信息，可以接入适配器调用 API 。

> Coral 的 api 接口仍在开发中，大部分功能受限。

Coral 的 API 接口与 Onebot 保持一致，但有一些细微的差别，例如取消了`prams`传参，具体如下：

## 请求格式

请求数据必须为`dict`，格式如下：

```json
{
    "action": "send_msg",
    "sender_user_id": 123456,
    "message": "Hello, world!",
    "group_id": -1
}
```

包含*号的字段为可选字段，不填则使用默认值。

# 接口列表

## `send_msg` 发送消息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
sender_user_id | int | - | 对方 QQ 号（私聊需要 group 为 `-1`）
group_id | int | - | 群号（群聊需要）
message | string or list | - | 需要发送的内容

## `delete_msg` 撤回消息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
message_id | int | - | 消息 ID

## `get_msg` 获取消息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
message_id | int | - | 消息 ID

## `get_forward_msg` 获取合并转发消息 

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
message_id | int | - | 消息 ID

## `send_like` 点赞

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
user_id | int | - | 被点赞用户 QQ 号
times | int | - | 点赞次数（若超过10 次，则默认为 10 次）

## `set_group_kick` 群组踢人

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
user_id | int | - | 被踢用户 QQ 号
*reject_add_request | bool | False | 拒绝再次加群请求

## `set_group_ban` 群组单人禁言

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
user_id | int | - | 被禁言用户 QQ 号
*duration | int | 5min | 禁言时长，单位秒，0 表示取消禁言

## `set_group_anonymous_ban` 群组匿名用户禁言

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*duration | int | 5min | 禁言时长，单位秒，0 表示取消禁言
anonymous | str | - | 匿名用户名称，需要和上报的名称一致
flag | str | - | 匿名用户 flag，需要和上报的 flag 一致

注：anonymous 和 flag 只能同时使用一个。

## `set_group_whole_ban` 群组全员禁言

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*enable | bool | True | 是否禁言

## `set_group_admin` 设置群组管理员

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
user_id | int | - | 被设置管理员用户 QQ 号
*enable | bool | True | 是否设置为管理员

## `set_group_anonymous` 设置群组匿名

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*enable | bool | True | 是否允许匿名聊天

## `set_group_card` 设置群名片

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
user_id | int | - | 被设置群名片用户 QQ 号
card | str | '' | 群名片内容，不填或空字符串表示删除群名片

## `set_group_name` 设置群名称

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
group_name | str | - | 新的群名称

## `set_group_leave` 退出群组

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*is_dismiss | bool | False | 是否解散，如果登录号是群主，则仅在此项为 True 时能够解散

## `set_group_special_title` 设置群组专属头衔

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
user_id | int | - | 被设置头衔用户 QQ 号
*special_title | str | '' | 专属头衔，不填或空字符串表示删除头衔
*duration | int | -1 | 专属头衔有效期，单位秒，-1 表示永久，不过此项似乎没有效果，可能是只有某些特殊的时间长度有效

## `set_friend_add_request` 处理加好友请求

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
flag | str | - | 加好友请求的 flag（需从上报的数据中获得）
*approve | bool | True | 是否同意请求

## `set_group_add_request` 处理加群请求或邀请

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
flag | str | - | 加群请求的 flag（需从上报的数据中获得）
sub_type | str | add | add 或 invite，请求类型（需要和上报消息中的 sub_type 字段相符）
*approve | bool | True | 是否同意请求
*reason | str | '' | 拒绝理由（仅在拒绝时有效）

## `get_login_info` 获取登录号信息

### 参数

无

## `get_stranger_info` 获取陌生人信息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
user_id | int | - | 陌生人 QQ 号
*no_cache | bool | False | 是否不使用缓存（使用缓存可能返回旧数据）

## `get_friend_list` 获取好友列表

### 参数

无

## `get_group_list` 获取群列表

### 参数

无

## `get_group_member_info` 获取群成员信息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*no_cache | bool | False | 是否不使用缓存（使用缓存可能返回旧数据）

## `get_group_member_list` 获取群成员列表

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号

## `get_group_honor_info` 获取群荣誉信息

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
group_id | int | - | 群号
*type | str | talkative | 群荣誉类型，目前支持 "talkative", "performer", "legend", "strong_newbie", "emotion", "all"

## `get_cookies` 获取 Cookies

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
*domain | str | - | 域名（不填则为当前域名）

## `get_csrf_token` 获取 CSRF Token

### 参数

 无

## `get_credentials` 获取凭据

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
*domain | str | - | 域名（不填则为当前域名）

## `get_image` 获取图片

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
file | str | - | 收到的图片文件名（消息段的 file 参数）

## `get_record` 获取语音

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
file | str | - | 收到的语音文件名（消息段的 file 参数）

## `can_send_image` 能否发送图片

### 参数

无

## `can_send_record` 能否发送语音

### 参数

无

## `get_status` 获取插件状态

### 参数

无

## `get_version_info` 获取版本信息

### 参数

无

## `set_restart` 重启 onebot 实例

### 参数

字段名 | 数据类型 | 默认值 | 说明
-|-|-|-
delay | int | 2000ms | 等待时间（ms）

## `clean_cache` 清理缓存

### 参数

无
