#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
dr.com校园网登录模块
实现dr.com校园网终端的登录和注销功能
"""

import re
import time
import requests
import socket
import logging
from urllib.parse import quote

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DrcomClient')


class DrcomClient:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        # 默认使用PC的User-Agent
        self.pc_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        # 移动设备的User-Agent
        self.mobile_user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        
        # 根据设备类型设置User-Agent
        if hasattr(config, 'device_type') and config.device_type == "Mobile":
            self.session.headers.update({
                'User-Agent': self.mobile_user_agent
            })
        else:
            self.session.headers.update({
                'User-Agent': self.pc_user_agent
            })
            
        self.login_url = None
        self.logout_url = None
        self.status_url = None
        self.init_urls()
    
    def init_urls(self):
        """初始化URL"""
        server = self.config.server
        if not server.startswith('http'):
            server = f'http://{server}'
        
        # 登录URL
        self.login_url = f"{server}/drcom/login"
        # 注销URL
        self.logout_url = f"{server}/drcom/logout"
        # 状态检查URL
        self.status_url = server
    
    def login(self):
        """登录校园网"""
        try:
            # 检查当前状态
            if self.is_connected():
                return {'success': True, 'message': '已经登录'}
            
            # 获取时间戳
            timestamp = str(int(round(time.time() * 1000)))
            
            # 构建登录参数
            params = {
                'callback': f'dr{timestamp}',
                'DDDDD': self.config.username,
                'upass': quote(self.config.password),
                '0MKKey': '123456',
                'R1': '0',
                'R3': '0',
                'R6': '0',
                'para': '00',
                'v6ip': '',
                '_': timestamp
            }

            # 根据设备类型添加不同的参数和请求头
            if self.config.device_type == "Mobile":
                # 移动设备参数
                params['type'] = '1'  # 移动设备
                # 移动设备可能不需要对密码进行URL编码
                params['upass'] = self.config.password
                
                # 更新为移动设备的完整请求头
                self.session.headers.update({
                    'User-Agent': self.mobile_user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'Connection': 'keep-alive',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                    'X-Requested-With': 'com.apple.mobilesafari',
                    'Referer': self.status_url
                })
                
                # 尝试直接使用POST方法登录（完全模拟网页表单提交）
                try:
                    # 构建完整的表单数据，模拟网页登录
                    post_data = {
                        'DDDDD': f",0,{self.config.username}",  # 特殊格式：,0,用户名
                        'upass': self.config.password,
                        '0MKKey': '123456789',  # 使用更常见的值
                        'R1': '0',
                        'R2': '',
                        'R3': '0',
                        'R6': '0',
                        'para': '00',
                        'v6ip': '',
                        'terminal_type': '1',
                        'type': '1',
                        'lang': 'zh'
                    }
                    
                    # 尝试POST方式登录
                    post_url = f"{self.config.server}/drcom/login"
                    if not post_url.startswith('http'):
                        post_url = f"http://{post_url}"
                        
                    post_response = self.session.post(post_url, data=post_data, timeout=10)
                    
                    if post_response.status_code == 200 and ('result":1' in post_response.text or '注销页' in post_response.text):
                        logger.info(f"POST方式登录成功: {self.config.username}")
                        return {'success': True, 'message': 'POST方式登录成功'}
                        
                except Exception as e:
                    logger.warning(f"POST方式登录失败，尝试GET方式: {str(e)}")
                    # 继续使用GET方式登录
            else:  # PC
                params['type'] = '2'  # PC设备
                # 更新为PC设备的User-Agent
                self.session.headers.update({
                    'User-Agent': self.pc_user_agent
                })
            
            # 发送登录请求
            response = self.session.get(self.login_url, params=params, timeout=10)
            
            # 检查响应
            if response.status_code == 200:
                # 解析响应内容
                content = response.text
                if 'result":1' in content:
                    # 登录成功
                    logger.info(f"登录成功: {self.config.username}")
                    return {'success': True, 'message': '登录成功'}
                else:
                    # 登录失败，尝试提取错误信息
                    error_match = re.search(r'"msg":"(.*?)"', content)
                    error_msg = error_match.group(1) if error_match else '未知错误'
                    logger.error(f"登录失败: {error_msg}")
                    return {'success': False, 'message': f'登录失败: {error_msg}'}
            else:
                # HTTP错误
                logger.error(f"HTTP错误: {response.status_code}")
                return {'success': False, 'message': f'HTTP错误: {response.status_code}'}
        
        except requests.exceptions.RequestException as e:
            # 请求异常
            logger.error(f"请求异常: {str(e)}")
            return {'success': False, 'message': f'请求异常: {str(e)}'}
        except Exception as e:
            # 其他异常
            logger.error(f"登录异常: {str(e)}")
            return {'success': False, 'message': f'登录异常: {str(e)}'}
    
    def logout(self):
        """注销登录"""
        try:
            # 检查当前状态
            if not self.is_connected():
                return {'success': True, 'message': '已经注销'}
            
            # 获取时间戳
            timestamp = str(int(round(time.time() * 1000)))
            
            # 构建注销参数
            params = {
                'callback': f'dr{timestamp}',
                '_': timestamp
            }
            
            # 发送注销请求
            response = self.session.get(self.logout_url, params=params, timeout=10)
            
            # 检查响应
            if response.status_code == 200:
                logger.info("注销成功")
                return {'success': True, 'message': '注销成功'}
            else:
                # HTTP错误
                logger.error(f"注销HTTP错误: {response.status_code}")
                return {'success': False, 'message': f'注销HTTP错误: {response.status_code}'}
        
        except requests.exceptions.RequestException as e:
            # 请求异常
            logger.error(f"注销请求异常: {str(e)}")
            return {'success': False, 'message': f'注销请求异常: {str(e)}'}
        except Exception as e:
            # 其他异常
            logger.error(f"注销异常: {str(e)}")
            return {'success': False, 'message': f'注销异常: {str(e)}'}
    
    def is_connected(self):
        """检查是否已连接"""
        try:
            # 发送请求到状态URL
            response = self.session.get(self.status_url, timeout=5)
            
            # 检查响应内容
            if response.status_code == 200:
                content = response.text
                # 检查页面标题，如果包含"注销页"则表示已登录
                title_match = re.search(r'<title>(.*?)</title>', content)
                if title_match and title_match.group(1) == '注销页':
                    # 尝试连接外网验证是否真的能上网
                    try:
                        # 使用更可靠的外网测试
                        test_urls = ['http://www.baidu.com', 'http://www.qq.com', 'http://www.bing.com']
                        for test_url in test_urls:
                            try:
                                test_response = self.session.get(test_url, timeout=3)
                                if test_response.status_code == 200:
                                    logger.info(f"成功连接到外网: {test_url}")
                                    return True
                            except:
                                continue
                        
                        # 如果所有测试URL都失败，则可能是校园网认证成功但没有真正连接到互联网
                        logger.warning("校园网认证页面显示已登录，但无法连接到外网")
                        return False
                    except Exception as e:
                        logger.error(f"外网连接测试异常: {str(e)}")
                        # 虽然测试失败，但校园网页面显示已登录，返回True
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"检查连接异常: {str(e)}")
            return False
    
    def check_network(self):
        """检查网络状态"""
        try:
            # 检查是否能访问校园网登录页面
            response = self.session.get(self.status_url, timeout=5)
            if response.status_code != 200:
                return {'success': False, 'message': '无法访问校园网登录页面'}
            
            # 检查是否已登录
            if self.is_connected():
                return {'success': True, 'message': '已登录并连接互联网'}
            else:
                return {'success': False, 'message': '未登录或无法连接互联网'}
        
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'网络请求异常: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'网络检查异常: {str(e)}'}