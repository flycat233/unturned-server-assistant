# Unturned服务器助手机器人

一个基于NoneBot2的Unturned游戏服务器管理助手机器人，提供玩家管理、服务器监控、签到系统等功能。

## 功能特性

- 🔧 **玩家管理**：QQ账号与SteamID绑定、个人信息查询
- 📅 **签到系统**：每日签到领取积分，支持连续签到奖励
- 🖥️ **服务器监控**：实时监控Unturned服务器状态，状态变化通知
- 📡 **API服务**：提供RESTful API接口，方便与其他系统集成
- 📢 **广播功能**：向所有监控群发送广播消息
- 📊 **玩家统计**：记录和查询玩家游戏数据

## 快速开始

### 环境要求

- Python 3.8+ 
- NoneBot2
- MySQL数据库
- OneBot协议机器人（如go-cqhttp）

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/your-username/unturned-bot.git
cd unturned-bot
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

复制`.env.example`文件并重命名为`.env`，然后根据你的环境修改配置：

```bash
cp .env.example .env
# 使用文本编辑器编辑.env文件
```

4. **创建数据库**

确保MySQL数据库已创建，然后运行机器人自动初始化表结构：

```bash
python start_bot.py
```

### 启动机器人

```bash
python start_bot.py
```

## 命令列表

### 基础命令
- `/help` - 查看帮助信息
- `/bind <SteamID>` - 绑定QQ与Steam账号
- `/sign` - 每日签到领取积分
- `/me` - 查看个人信息
- `/server` - 查看服务器状态

### 管理员命令
- `/broadcast <消息>` - 广播消息到所有监控群

## 配置说明

详细配置说明请参考[配置文档](https://github.com/your-username/unturned-bot/wiki/配置说明)。

## API文档

启动机器人后，可以访问 `http://<API_HOST>:<API_PORT>/docs` 查看Swagger API文档。

## 开发指南

如果你想参与开发，请参考[开发文档](https://github.com/your-username/unturned-bot/wiki/开发指南)。

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

## 致谢

- [NoneBot2](https://github.com/nonebot/nonebot2) - 机器人框架
- [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) - OneBot协议实现