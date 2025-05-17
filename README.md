# 校园网登录器

## 项目背景

当电脑需要远程连接或下载文件时，需要长期保持校园网连接。但由于校园网系统会不定期踢人下线，导致连接中断。原项目   "https://github.com/Jin-Cheng-Ming/ZHKU-Connector"   因海珠校区更换为drcom系统而失效，因此开发了本项目，参考了 
  "https://github.com/drcoms/drcom-generic"   ,本项目借助Trae开发，实现了自动重连功能。

## 功能特点

- 自动检测网络连接状态，断线后自动重连
- 支持保存账号密码，避免每次手动输入
- 图形化界面操作简单
- 支持后台运行和系统托盘图标
- 断线自动重连机制保障稳定连接

## 使用场景

- 远程桌面连接时保持网络稳定
- 大文件下载时防止因断网中断
- 需要长期保持网络连接的场景

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行主程序：
```bash
python main.py
```
2. 输入校园网账号、密码和服务器地址
3. 勾选"自动登录"和"开机启动"选项
4. 点击"保存配置"保存设置

## 配置文件

配置文件位于项目根目录下的`ZhkuWangLuo.xml`，包含以下信息：
```xml
<config>
    <username>校园网账号</username>
    <password>校园网密码</password>
    <server>校园网认证服务器地址</server>
    <auto_login>true</auto_login>
    <auto_start>true</auto_start>
</config>
```

## 注意事项

1. 本程序仅适用于dr.com认证系统
2. 密码保存在本地，请注意隐私安全
3. 如遇登录问题请检查网络和账号信息

## 许可证

MIT License
