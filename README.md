# unturned-server-assistant
Unturned服务器助手机器人
# Unturned服务器助手机器人

一个基于NoneBot2和OneBot标准的QQ机器人插件，为Unturned服务器提供全方位的管理和监控功能。

## 功能特性

### 1. API消息发送功能
- 提供FastAPI接口，支持通过HTTP请求向指定QQ群或私聊发送消息
- 包含API密钥认证机制，确保消息发送安全性
- 支持文本消息和格式化内容发送
- 提供健康检查和机器人信息查询API

### 2. 服务器监控功能
- 实时监控Unturned服务器状态（在线/离线）
- 自动记录服务器状态变化历史到数据库
- 支持服务器异常状态自动通知（如服务器崩溃、重启）
- 提供管理员手动检查服务器状态命令
- 实现定时轮询检查机制，可配置检查间隔

### 3. 玩家管理系统
- SteamID与QQ账号绑定功能
- 玩家签到系统，支持每日签到获取奖励
- 个人信息查询，包括签到次数、游戏时长等统计数据
- 玩家数据存储与管理

### 4. 权限管理系统
- 超级用户（管理员）权限验证
- 群管理权限验证机制
- 针对不同用户组的命令访问控制

### 5. 实用命令系统
- 帮助命令：显示所有可用命令及使用说明
- 绑定命令：绑定SteamID与QQ账号
- 签到命令：每日签到获取奖励
- 个人信息命令：查询玩家个人统计数据
- 广播命令：管理员向所有群发送公告
- 服务器状态命令：查询当前服务器运行状态

## 安装指南

### 前提条件
- Python 3.8+ 
- NoneBot2框架
- OneBot协议兼容的QQ机器人客户端（如go-cqhttp）

### 安装步骤

1. 克隆或下载本插件到您的NoneBot2项目插件目录
   ```bash
   cd f:\UnturnedServer
   git clone https://github.com/yourusername/UnturnedServerAssistant.git NoneBot2Plugin
   ```

2. 安装依赖
   ```bash
   cd NoneBot2Plugin
   pip install -r requirements.txt
   ```

3. 配置环境变量
   - 复制并重命名`.env.example`为`.env`
   - 根据您的实际情况修改`.env`文件中的配置项

4. 启动NoneBot2机器人
   ```bash
   nb run
   ```

## 配置说明

### 环境变量配置（.env文件）
- `SUPERUSERS`: 超级用户列表，用逗号分隔
- `API_KEY`: API接口密钥，用于验证请求
- `DATABASE_URL`: 数据库连接URL
- `UNTURNED_SERVERS`: Unturned服务器配置
- 更多配置项请参考`.env`文件中的注释

### 默认配置（config.py）
- 命令前缀、权限等级、消息格式等默认配置
- 如需修改，请直接编辑`config.py`文件

## API接口文档

### 基础URL
```
http://{API_HOST}:{API_PORT}/api
```

### 认证方式
所有API请求需要在请求头中包含`Authorization`字段，值为`Bearer {API_KEY}`

### 可用接口

#### 1. 发送私聊消息
- URL: `/send_private_msg`
- 方法: POST
- 参数:
  - `user_id`: QQ号
  - `message`: 消息内容
- 响应: JSON格式，包含状态码和消息ID

#### 2. 发送群消息
- URL: `/send_group_msg`
- 方法: POST
- 参数:
  - `group_id`: 群号
  - `message`: 消息内容
- 响应: JSON格式，包含状态码和消息ID

#### 3. 健康检查
- URL: `/health`
- 方法: GET
- 响应: JSON格式，包含机器人运行状态和版本信息

#### 4. 查询服务器状态
- URL: `/server_status`
- 方法: GET
- 参数（可选）:
  - `server_name`: 服务器名称
- 响应: JSON格式，包含服务器详细状态信息

## 命令列表

| 命令 | 权限 | 说明 | 使用方式 |
|------|------|------|----------|
| help | 所有人 | 显示帮助信息 | `un.help [命令]` |
| bind | 所有人 | 绑定SteamID与QQ账号 | `un.bind <SteamID>` |
| signin | 所有人 | 每日签到获取奖励 | `un.signin` |
| profile | 所有人 | 查询个人信息 | `un.profile [QQ号]` |
| server_status | 所有人 | 查询服务器状态 | `un.server_status [服务器名称]` |
| broadcast | 管理员 | 发送广播消息 | `un.broadcast <消息>` |
| add_admin | 超级管理员 | 添加管理员 | `un.add_admin <QQ号> <权限等级>` |
| remove_admin | 超级管理员 | 移除管理员 | `un.remove_admin <QQ号>` |
| group_config | 群管理 | 配置群组设置 | `un.group_config <设置项> <值>` |

## 数据库结构

本插件使用SQLite作为默认数据库，存储以下信息：

- **QQBotPlayers**: 存储QQ用户与SteamID绑定信息
- **PlayerStats**: 存储玩家游戏统计数据
- **Uconomy**: 存储玩家游戏内经济数据
- **ServerStatus**: 记录服务器状态历史
- **DailySignIn**: 存储玩家签到记录
- **GroupManagement**: 存储群管理配置
- **CommandLogs**: 记录命令执行日志
- **Announcements**: 存储系统公告

## OneBot HTTP POST集成

本插件支持通过OneBot HTTP POST协议与Unturned游戏插件进行通信。游戏插件可以通过发送HTTP请求到机器人API接口，实现以下功能：

1. 向指定QQ群或玩家发送游戏内事件通知
2. 获取玩家绑定信息
3. 查询服务器状态
4. 执行管理操作

详细的API文档请参考：[OneBot V11 HTTP POST](https://283375.github.io/onebot_v11_vitepress/communication/http-post.html)

## 注意事项

1. 请妥善保管您的API密钥，避免泄露
2. 定期备份数据库文件，防止数据丢失
3. 合理设置服务器监控间隔，避免对服务器造成过大压力
4. 使用过程中如遇到问题，请查看日志文件获取详细错误信息

## 常见问题

### Q: 机器人无法启动
A: 请检查Python版本是否满足要求，以及是否正确安装了所有依赖包

### Q: 无法绑定SteamID
A: 请确保输入的SteamID格式正确，支持纯数字ID、STEAM_0:0:12345678格式或Steam个人资料URL

### Q: 服务器监控功能不工作
A: 请检查服务器配置是否正确，确保机器人能够访问到Unturned服务器

## 更新日志

### v1.0.0
- 初始版本发布
- 实现API消息发送、服务器监控、玩家管理、权限管理和实用命令系统

## 贡献

欢迎提交Issue和Pull Request来帮助改进本插件。

## 许可证

[MIT License](LICENSE)
