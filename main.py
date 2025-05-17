#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园网登录器主程序
支持dr.com校园网终端自动登录
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import messagebox
import logging

from gui import LoginGUI
from drcom import DrcomClient
from config import Config


class DrcomApp:
    def __init__(self):
        self.config = Config()
        self.root = tk.Tk()
        self.root.withdraw()  # 先隐藏主窗口
        self.client = DrcomClient(self.config)
        self.gui = LoginGUI(self.root, self.config, self.login_callback, self.logout_callback, self.save_config_callback)
        
        # GUI创建后，日志处理器已设置，发送一条初始日志
        logging.info("应用程序已启动")
        
        self.login_thread = None
        self.check_thread = None
        self.running = False
        
    def start(self):
        """启动应用"""
        # 检查是否有保存的配置
        if self.config.load_config():
            # 如果设置了自动登录，则自动登录
            if self.config.auto_login:
                self.start_login_thread()
        
        # 显示GUI
        self.gui.show()
        self.root.mainloop()
    
    def login_callback(self, username, password, server, auto_login, auto_start, device_type):
        """登录回调函数"""
        self.config.username = username
        self.config.password = password
        self.config.server = server
        self.config.auto_login = auto_login
        self.config.auto_start = auto_start
        self.config.device_type = device_type
        self.config.save_config()
        
        self.start_login_thread()
    
    def start_login_thread(self):
        """启动登录线程"""
        if self.login_thread and self.login_thread.is_alive():
            return
            
        self.running = True
        self.login_thread = threading.Thread(target=self.login_task)
        self.login_thread.daemon = True
        self.login_thread.start()
        
        # 启动状态检查线程
        if not self.check_thread or not self.check_thread.is_alive():
            self.check_thread = threading.Thread(target=self.check_connection_task)
            self.check_thread.daemon = True
            self.check_thread.start()
    
    def login_task(self):
        """登录任务"""
        try:
            logging.info("正在登录...")
            result = self.client.login()
            if result['success']:
                logging.info(f"登录成功: {result['message']}")
                self.gui.set_login_state(True)
            else:
                logging.error(f"登录失败: {result['message']}")
                self.gui.set_login_state(False)
                # messagebox.showerror("登录失败", result['message']) # 错误信息将显示在日志框中
        except Exception as e:
            logging.error(f"登录异常: {str(e)}")
            self.gui.set_login_state(False)
            # messagebox.showerror("登录异常", str(e)) # 异常信息将显示在日志框中
    
    def logout_callback(self):
        """注销回调函数"""
        try:
            logging.info("正在注销...")
            result = self.client.logout()
            if result['success']:
                logging.info(f"注销成功: {result['message']}")
                self.gui.set_login_state(False)
            else:
                logging.error(f"注销失败: {result['message']}")
                # messagebox.showerror("注销失败", result['message']) # 错误信息将显示在日志框中
        except Exception as e:
            logging.error(f"注销异常: {str(e)}")
            # messagebox.showerror("注销异常", str(e)) # 异常信息将显示在日志框中
    
    def save_config_callback(self, username, password, server, auto_login, auto_start, device_type):
        """保存配置回调函数"""
        self.config.username = username
        self.config.password = password
        self.config.server = server
        self.config.auto_login = auto_login
        self.config.auto_start = auto_start
        self.config.device_type = device_type
        if self.config.save_config():
            logging.info("配置已保存")
            # messagebox.showinfo("保存成功", "配置已保存") # 成功信息将显示在日志框中
        else:
            logging.error("保存配置失败")
            # messagebox.showerror("保存失败", "保存配置失败") # 错误信息将显示在日志框中
    
    def check_connection_task(self):
        """检查网络连接状态任务"""
        while self.running:
            try:
                # 每30秒检查一次连接状态
                time.sleep(30)
                if not self.client.is_connected():
                    logging.warning("连接已断开，尝试重新登录...")
                    self.login_task()
                else:
                    logging.info("连接正常")
            except Exception as e:
                logging.error(f"检查连接异常: {str(e)}")
    
    def exit(self):
        """退出应用"""
        self.running = False
        if self.login_thread and self.login_thread.is_alive():
            self.login_thread.join(1)
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(1)
        self.root.destroy()


def main():
    # 创建应用实例
    app = DrcomApp()
    
    # 启动应用
    try:
        app.start()
    except KeyboardInterrupt:
        app.exit()
    except Exception as e:
        logging.critical(f"应用异常: {str(e)}")
        # messagebox.showerror("应用异常", str(e)) # 异常信息将显示在日志框中
        app.exit()


if __name__ == "__main__":
    main()