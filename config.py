#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园网登录器配置模块
负责保存和加载用户配置
"""

import os
import json
import logging
import xml.etree.ElementTree as ET

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Config')


class Config:
    def __init__(self):
        # 默认配置
        self.username = ""
        self.password = ""
        self.server = "172.31.255.1"
        self.auto_login = False
        self.auto_start = False
        self.device_type = "PC"  # 新增：设备类型，默认为PC
        
        # 配置文件路径
        # 配置文件路径
        # 将配置文件保存在当前脚本所在的目录下
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ZhkuWangLuo.xml")
        
        # 不再需要创建配置目录，因为文件直接保存在当前目录
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 创建XML根元素
            root = ET.Element("Config")
            
            # 添加配置项
            ET.SubElement(root, "username").text = self.username
            ET.SubElement(root, "password").text = self.password
            ET.SubElement(root, "server").text = self.server
            ET.SubElement(root, "auto_login").text = str(self.auto_login)
            ET.SubElement(root, "auto_start").text = str(self.auto_start)
            ET.SubElement(root, "device_type").text = self.device_type
            
            # 创建XML树并写入文件
            tree = ET.ElementTree(root)
            tree.write(self.config_file, encoding="utf-8", xml_declaration=True)
            
            # 设置开机启动
            self.set_auto_start(self.auto_start)
            
            logger.info("配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def load_config(self):
        """从文件加载配置"""
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file):
                logger.info("配置文件不存在，使用默认配置")
                return False
            
            # 读取配置文件
            tree = ET.parse(self.config_file)
            root = tree.getroot()
            
            # 更新配置
            self.username = root.findtext("username", "")
            self.password = root.findtext("password", "")
            self.server = root.findtext("server", "10.10.42.3")
            self.auto_login = root.findtext("auto_login", "False").lower() == 'true'
            self.auto_start = root.findtext("auto_start", "False").lower() == 'true'
            self.device_type = root.findtext("device_type", "PC")
            
            logger.info("配置已加载")
            return True
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return False
    
    def set_auto_start(self, enable):
        """设置开机启动"""
        try:
            # 获取当前脚本路径
            script_path = os.path.abspath(sys.argv[0])
            
            # Windows系统使用注册表设置开机启动
            if os.name == "nt":
                import winreg
                key_name = "DrcomLogin"
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                
                try:
                    # 打开注册表键
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    
                    if enable:
                        # 添加开机启动项
                        winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, f'"{script_path}" --minimize')
                        logger.info("已添加开机启动项")
                    else:
                        # 删除开机启动项
                        try:
                            winreg.DeleteValue(key, key_name)
                            logger.info("已删除开机启动项")
                        except FileNotFoundError:
                            pass
                    
                    winreg.CloseKey(key)
                except Exception as e:
                    logger.error(f"设置开机启动失败: {str(e)}")
            
            # Linux系统使用桌面文件设置开机启动
            elif os.name == "posix":
                autostart_dir = os.path.join(os.path.expanduser("~"), ".config", "autostart")
                autostart_file = os.path.join(autostart_dir, "drcom-login.desktop")
                
                if enable:
                    # 创建自启动目录
                    if not os.path.exists(autostart_dir):
                        os.makedirs(autostart_dir)
                    
                    # 创建桌面文件
                    with open(autostart_file, "w", encoding="utf-8") as f:
                        f.write(f"[Desktop Entry]\n")
                        f.write(f"Type=Application\n")
                        f.write(f"Name=DrcomLogin\n")
                        f.write(f"Exec={script_path} --minimize\n")
                        f.write(f"Terminal=false\n")
                        f.write(f"Hidden=false\n")
                    
                    logger.info("已添加开机启动项")
                else:
                    # 删除桌面文件
                    if os.path.exists(autostart_file):
                        os.remove(autostart_file)
                        logger.info("已删除开机启动项")
            
            return True
        except Exception as e:
            logger.error(f"设置开机启动异常: {str(e)}")
            return False


# 导入sys模块（用于set_auto_start方法）
import sys