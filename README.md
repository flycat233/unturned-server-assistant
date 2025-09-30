# Unturned服务器助手机器人

这是一个基于NoneBot2的Unturned服务器助手机器人，可以帮助管理员管理和监控Unturned游戏服务器。

## 功能特性

- 服务器状态监控
- 启动和关闭通知
- 基础命令管理
- 简易API接口

## 环境要求

- Python 3.8+
- 安装依赖：`pip install -r requirements.txt`

## 快速开始

1. 复制`.env.example`并重命名为`.env`
2. 编辑`.env`文件，配置超级用户ID等参数
3. 运行机器人：`python start_bot.py` 或 `nb run`

## 配置说明

### 超级用户配置
```
SUPERUSERS="1049217020"
```
可以设置多个超级用户ID，用逗号分隔。

### 命令配置
```
COMMAND_START=["/", "!", "！"]
COMMAND_SEP=["|"]
```
配置机器人响应的命令前缀。

### API服务配置
```
API_ENABLED=true
API_HOST=127.0.0.1
API_PORT=8080
```
控制是否启用API服务及监听地址端口。

## 使用方法

### 基础命令
使用配置的命令前缀加上命令名称来调用机器人功能。

### 自定义插件
可以在当前目录下添加自定义插件来扩展机器人功能。

## 注意事项

- 确保已安装所有依赖包
- 修改配置后需要重启机器人才能生效
- 建议定期备份数据库文件

## License
MIT