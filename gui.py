#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园网登录器GUI界面模块
实现登录器的图形用户界面 - 现代化设计版本 (优化版)
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from PIL import Image, ImageTk, ImageFilter, ImageDraw
from tkinter.scrolledtext import ScrolledText
import logging

# 自定义主题颜色 - 黄绿色主题
PRIMARY_COLOR = "#9ACD32"  # 黄绿色 (用于渐变起始)
SECONDARY_COLOR = "#FFFF00"  # 黄色 (用于渐变结束)
BACKGROUND_COLOR = "#F5F5F5"  # 浅灰色背景
CARD_BASE_COLOR = "#F0F0F0"  # 卡片基色
TEXT_COLOR = "#333333"  # 深灰色文字
ACCENT_COLOR = "#4CAF50"  # 绿色强调色
BUTTON_TEXT_COLOR = "#FFFFFF"  # 按钮文字颜色

# 毛玻璃效果参数
GLASS_ALPHA = 200  # 卡片透明度 (0-255)
BLUR_RADIUS = 10  # 卡片模糊半径


class ModernUI:
    @staticmethod
    def create_rounded_rectangle(width, height, radius, fill_color):
        """创建圆角矩形"""
        if width <= 0 or height <= 0:  # 防止尺寸无效
            width, height = 1, 1
        if radius * 2 > min(width, height):  # 防止半径过大
            radius = min(width, height) // 2

        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # 透明背景
        draw = ImageDraw.Draw(image)

        if isinstance(fill_color, str):
            try:
                r, g, b = tuple(int(fill_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                fill_color_rgba = (r, g, b, 255)
            except ValueError:
                fill_color_rgba = (255, 255, 255, 255)  # 默认白色
        elif isinstance(fill_color, tuple) and len(fill_color) == 3:
            fill_color_rgba = (*fill_color, 255)
        elif isinstance(fill_color, tuple) and len(fill_color) == 4:
            fill_color_rgba = fill_color
        else:
            fill_color_rgba = (255, 255, 255, 255)  # 默认白色

        draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=fill_color_rgba)
        return image

    @staticmethod
    def apply_gaussian_blur(image, radius=2):
        """应用高斯模糊效果"""
        return image.filter(ImageFilter.GaussianBlur(radius))


class ModernButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=120, height=40,
                 bg_color=PRIMARY_COLOR, hover_color="#4CAF50",
                 text_color=BUTTON_TEXT_COLOR, corner_radius=10, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.command = command
        self.text = text
        self.width = width
        self.height = height

        self._draw_button()

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def _draw_button(self, current_bg_color=None):
        """绘制按钮"""
        if current_bg_color is None:
            current_bg_color = self.bg_color

        self.normal_image = ModernUI.create_rounded_rectangle(
            self.width, self.height, self.corner_radius, self.bg_color)
        self.hover_image = ModernUI.create_rounded_rectangle(
            self.width, self.height, self.corner_radius, self.hover_color)

        self.normal_photo = ImageTk.PhotoImage(self.normal_image)
        self.hover_photo = ImageTk.PhotoImage(self.hover_image)

        self.delete("all")

        active_photo = self.normal_photo
        if hasattr(self, '_hovering') and self._hovering:
            active_photo = self.hover_photo

        self.bg_id = self.create_image(self.width / 2, self.height / 2, image=active_photo)
        self.text_id = self.create_text(self.width / 2, self.height / 2, text=self.text,
                                        fill=self.text_color, font=("Microsoft YaHei UI", 10, "bold"))

    def on_enter(self, event):
        self._hovering = True
        self.itemconfig(self.bg_id, image=self.hover_photo)

    def on_leave(self, event):
        self._hovering = False
        self.itemconfig(self.bg_id, image=self.normal_photo)

    def on_click(self, event):
        if self.command:
            self.command()

    def config(self, **kwargs):
        """更新按钮属性"""
        if 'bg_color' in kwargs:
            self.bg_color = kwargs.pop('bg_color')
        if 'hover_color' in kwargs:
            self.hover_color = kwargs.pop('hover_color')
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
        if 'command' in kwargs:
            self.command = kwargs.pop('command')
        if 'text_color' in kwargs:
            self.text_color = kwargs.pop('text_color')

        super().config(**kwargs)
        self._draw_button()


class LoginGUI:
    def __init__(self, root, config, login_callback, logout_callback, save_config_callback):
        self.root = root
        self.config = config
        self.login_callback = login_callback
        self.logout_callback = logout_callback
        self.save_config_callback = save_config_callback

        self._photo_references = {}  # 用于保存PhotoImage的引用
        self.is_logged_in = False
        self.log_text = None
        self.card_bg_photo = None
        self.tray_icon = None
        self._resize_job = None
        self._card_resize_job = None

        self.setup_window()

    def show(self):
        """显示主窗口"""
        self.root.deiconify()

    def _store_photo(self, name, photo_image):
        """存储PhotoImage防止被垃圾回收"""
        self._photo_references[name] = photo_image

    def update_card_background(self, event=None):
        """更新卡片背景图像，应用毛玻璃效果"""
        if not hasattr(self, 'card_frame') or not self.card_frame.winfo_exists():
            return

        if threading.current_thread() is not threading.main_thread():
             self.root.after(0, self.update_card_background)
             return

        width = self.card_frame.winfo_width()
        height = self.card_frame.winfo_height()

        if width <= 0 or height <= 0:
            return

        base_image = ModernUI.create_rounded_rectangle(width, height, 20, CARD_BASE_COLOR)
        blurred_image = ModernUI.apply_gaussian_blur(base_image, BLUR_RADIUS)
        alpha_channel = blurred_image.split()[-1]
        alpha_channel = alpha_channel.point(lambda i: i * (GLASS_ALPHA / 255.0))
        blurred_image.putalpha(alpha_channel)

        card_bg_photo = ImageTk.PhotoImage(blurred_image)
        self._store_photo("card_bg", card_bg_photo)

        if hasattr(self, 'card_bg_label'):
            self.card_bg_label.config(image=self._photo_references["card_bg"])
        else:
            self.card_bg_label = tk.Label(self.card_frame, image=self._photo_references["card_bg"])
            self.card_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.card_bg_label.lower()

    def create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            import pystray

            icon_size = 64
            icon_image = ModernUI.create_rounded_rectangle(icon_size, icon_size, 20, PRIMARY_COLOR)
            icon_draw = ImageDraw.Draw(icon_image)
            icon_draw.rectangle([20, 30, 44, 34], fill="white")
            icon_draw.rectangle([30, 20, 34, 44], fill="white")

            menu = pystray.Menu(
                pystray.MenuItem('显示', self.show_window, default=True),
                pystray.MenuItem('登录', self.on_login_click_threadsafe),
                pystray.MenuItem('注销', self.on_logout_click_threadsafe),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('退出', self.exit_app)
            )

            self.tray_icon = pystray.Icon(
                "campus_login",
                icon_image,
                "校园网登录器",
                menu
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logging.info("系统托盘图标已创建。")
        except ImportError:
            logging.warning("pystray 模块未找到，无法创建系统托盘图标。")
            self.tray_icon = None
        except Exception as e:
            logging.error(f"创建托盘图标失败: {e}")
            self.tray_icon = None

    def on_login_click_threadsafe(self):
        """线程安全的登录点击处理"""
        self.root.after(0, self.on_login_click)

    def on_logout_click_threadsafe(self):
        """线程安全的注销点击处理"""
        self.root.after(0, self.on_logout_click)

    def setup_window(self):
        """设置主窗口"""
        self.root.title("校园网登录器")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        self.root.configure(bg=BACKGROUND_COLOR)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'img', 'Zklogo.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                logging.warning(f"图标文件未找到: {icon_path}")
        except Exception as e:
            logging.error(f"设置窗口图标失败: {e}")

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.title_frame = tk.Frame(self.main_frame, bg=BACKGROUND_COLOR)
        self.title_frame.pack(pady=(0, 20))
        self.title_label = tk.Label(self.title_frame, text="校园网登录器",
                                    font=("Microsoft YaHei UI", 24, "bold"),
                                    fg=TEXT_COLOR)
        self.title_label.pack()

        self.card_frame = tk.Frame(self.main_frame, bg=CARD_BASE_COLOR)
        self.card_frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.setup_layout()
        self.create_tray_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_logging()

    def create_widgets(self):
        """创建GUI控件"""
        label_font = ("Microsoft YaHei UI", 11)
        entry_font = ("Microsoft YaHei UI", 11)
        widget_fg = TEXT_COLOR

        self.input_area = tk.Frame(self.card_frame)

        self.username_label = tk.Label(self.input_area, text="用户账号:", font=label_font, fg=TEXT_COLOR)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.input_area, textvariable=self.username_var, font=entry_font, width=30)

        self.password_label = tk.Label(self.input_area, text="登录密码:", font=label_font, fg=TEXT_COLOR)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.input_area, textvariable=self.password_var, show="*", font=entry_font,
                                        width=30)

        self.server_label = tk.Label(self.input_area, text="认证服务器:", font=label_font, fg=TEXT_COLOR)
        self.server_var = tk.StringVar()
        self.server_entry = ttk.Entry(self.input_area, textvariable=self.server_var, font=entry_font, width=30)

        self.device_type_label = tk.Label(self.input_area, text="(暂时没用)设备类型:", font=label_font, fg=TEXT_COLOR)
        self.device_var = tk.StringVar(value="PC")
        self.device_combo = ttk.Combobox(self.input_area, textvariable=self.device_var,
                                         values=["PC", "Mobile"], font=entry_font, state="readonly", width=28)

        self.options_frame = tk.Frame(self.input_area)
        s = ttk.Style()
        s.configure("TCheckbutton", font=label_font, foreground=TEXT_COLOR)
        self.auto_login_var = tk.BooleanVar()
        self.auto_login_check = ttk.Checkbutton(self.options_frame, text="自动登录", variable=self.auto_login_var,
                                                style="TCheckbutton")
        self.auto_start_var = tk.BooleanVar()
        self.auto_start_check = ttk.Checkbutton(self.options_frame, text="开机启动", variable=self.auto_start_var,
                                                style="TCheckbutton")

        self.button_frame = tk.Frame(self.input_area)
        btn_width, btn_height = 100, 38
        self.login_button = ModernButton(self.button_frame, text="登 录", command=self.on_login_click,
                                         width=btn_width, height=btn_height, bg_color=ACCENT_COLOR,
                                         hover_color=PRIMARY_COLOR)
        self.logout_button = ModernButton(self.button_frame, text="注 销", command=self.on_logout_click,
                                        width=btn_width, height=btn_height, bg_color="#AAAAAA", hover_color="#888888")
        self.save_button = ModernButton(self.button_frame, text="保存配置", command=self.on_save_config_click,
                                      width=btn_width, height=btn_height, bg_color=PRIMARY_COLOR,
                                      hover_color=ACCENT_COLOR)
        self.load_button = ModernButton(self.button_frame, text="加载配置", command=self.on_load_config_click,
                                      width=btn_width, height=btn_height, bg_color="#6A5ACD",
                                      hover_color="#483D8B")

        self.status_area = tk.Frame(self.card_frame)
        self.status_label_title = tk.Label(self.status_area, text="状态信息:", font=label_font, fg=TEXT_COLOR)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label_content = tk.Label(self.status_area, textvariable=self.status_var,
                                         font=("Microsoft YaHei UI", 10), fg="#005588", wraplength=300,
                                         justify=tk.LEFT)

        self.log_area = tk.Frame(self.card_frame)
        self.log_label_title = tk.Label(self.log_area, text="日志输出:", font=label_font, fg=TEXT_COLOR)
        self.log_text = ScrolledText(self.log_area, wrap=tk.WORD, height=10,
                                 font=("Consolas", 10), fg=TEXT_COLOR, relief=tk.SOLID, bd=1)
        self.log_text.configure(bg="#FFFFFF")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("DEBUG", foreground="gray")

    def setup_layout(self):
        """布局GUI控件"""
        self.card_frame.grid_columnconfigure(0, weight=3)
        self.card_frame.grid_columnconfigure(1, weight=4)
        self.card_frame.grid_rowconfigure(0, weight=1)
        self.card_frame.grid_rowconfigure(1, weight=0)

        self.input_area.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.status_area.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.log_area.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=20, pady=20)

        self.input_area.grid_columnconfigure(1, weight=1)

        self.username_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        self.password_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        self.server_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.server_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)
        self.device_type_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        self.device_combo.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=5)

        self.options_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=tk.W)
        self.auto_login_check.pack(side=tk.LEFT, padx=(0, 15))
        self.auto_start_check.pack(side=tk.LEFT)

        self.button_frame.grid(row=5, column=0, columnspan=2, pady=15)
        self.login_button.pack(side=tk.TOP, pady=5)
        self.logout_button.pack(side=tk.TOP, pady=5)
        self.save_button.pack(side=tk.TOP, pady=5)
        self.load_button.pack(side=tk.TOP, pady=5)

        self.status_label_title.pack(side=tk.LEFT, anchor=tk.NW)
        self.status_label_content.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)

        self.log_label_title.pack(anchor=tk.NW, pady=(0, 5))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.set_login_state(self.is_logged_in)

    def on_login_click(self):
        """登录按钮点击事件处理"""
        username = self.username_var.get()
        password = self.password_var.get()
        server = self.server_var.get()
        device_type = self.device_var.get()

        if not all([username, password, server]):
            messagebox.showerror("输入错误", "用户名、密码和服务器均不能为空！", parent=self.root)
            return

        auto_login = self.auto_login_var.get()
        auto_start = self.auto_start_var.get()

        threading.Thread(target=self.login_callback,
                         args=(username, password, server, auto_login, auto_start, device_type),
                         daemon=True).start()

    def on_logout_click(self):
        """注销按钮点击事件处理"""
        threading.Thread(target=self.logout_callback, daemon=True).start()

    def on_save_config_click(self):
        """保存配置按钮点击事件处理"""
        username = self.username_var.get()
        password = self.password_var.get()
        server = self.server_var.get()
        auto_login = self.auto_login_var.get()
        auto_start = self.auto_start_var.get()
        device_type = self.device_var.get()

        if not all([username, server]):
            messagebox.showerror("输入错误", "用户名和服务器不能为空！", parent=self.root)
            return

        self.save_config_callback(username, password, server, auto_login, auto_start, device_type)
        messagebox.showinfo("配置已保存", "您的设置已成功保存。", parent=self.root)

    def on_load_config_click(self):
        """加载配置按钮点击事件处理"""
        logging.info("正在加载配置...")
        if hasattr(self.config, 'load_config') and self.config.load_config():
             self.load_config()
             logging.info("配置加载成功并已更新到GUI。")
        else:
             logging.error("加载配置失败或配置对象不支持加载。")

    def load_config(self):
        """加载配置到GUI"""
        self.username_var.set(getattr(self.config, 'username', ''))
        self.password_var.set(getattr(self.config, 'password', ''))
        self.server_var.set(getattr(self.config, 'server', ''))
        self.auto_login_var.set(getattr(self.config, 'auto_login', False))
        self.auto_start_var.set(getattr(self.config, 'auto_start', False))
        self.device_var.set(getattr(self.config, 'device_type', 'PC'))
        logging.info("配置已加载到GUI。")

    def append_log(self, message, level="INFO"):
        """向日志框追加信息"""
        if self.log_text and self.log_text.winfo_exists():
            def _update_log():
                if not self.log_text or not self.log_text.winfo_exists(): return
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n", level.upper())
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)

            if threading.current_thread() is not threading.main_thread():
                self.root.after(0, _update_log)
            else:
                _update_log()

    def setup_logging(self):
        """设置日志系统"""
        if not hasattr(self, 'log_text') or self.log_text is None:
            print("错误: Log_text 未初始化，无法设置GUI日志处理器。")
            return

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers[:]:
            if isinstance(handler, GuiLogHandler):
                logger.removeHandler(handler)

        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        self.gui_log_handler = GuiLogHandler(self)
        self.gui_log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.gui_log_handler.setFormatter(formatter)
        logger.addHandler(self.gui_log_handler)

        logging.info("GUI 日志系统初始化完成。")

    def update_status(self, status_message):
        """更新状态信息"""
        def _update():
            self.status_var.set(status_message)

        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, _update)
        else:
            _update()

    def set_login_state(self, is_logged_in):
        """设置登录状态"""
        self.is_logged_in = is_logged_in

        def _update():
            if is_logged_in:
                self.login_button.config(bg_color="#AAAAAA", hover_color="#888888")
                self.login_button.command = None
                self.logout_button.config(bg_color="#4CAF50", hover_color=PRIMARY_COLOR)
                self.logout_button.command = self.on_logout_click
            else:
                self.login_button.config(bg_color="#4CAF50", hover_color=PRIMARY_COLOR)
                self.login_button.command = self.on_login_click
                self.logout_button.config(bg_color="#AAAAAA", hover_color="#888888")
                self.logout_button.command = None

        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, _update)
        else:
            _update()

    def show_window(self):
        """显示窗口"""
        if self.root:
            self.root.after(0, self.root.deiconify)
            self.root.after(10, self.root.lift)
            self.root.after(20, self.root.focus_force)

    def hide_window(self):
        """隐藏窗口"""
        if self.root:
            self.root.after(0, self.root.withdraw)

    def on_close(self):
        """窗口关闭事件处理"""
        if self.tray_icon and self.tray_icon.visible:
            self.hide_window()
            logging.info("窗口已隐藏到系统托盘。")
            messagebox.showinfo("提示", "程序已最小化到托盘区域。", parent=self.root)
        else:
            self.exit_app()

    def exit_app(self):
        """退出应用程序"""
        logging.info("正在退出应用程序...")
        if self.tray_icon:
            self.tray_icon.stop()
        if self.root:
            self.root.destroy()
        sys.exit()


class GuiLogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到GUI的文本框"""
    def __init__(self, gui_instance):
        super().__init__()
        self.gui_instance = gui_instance

    def emit(self, record):
        msg = self.format(record)
        if self.gui_instance and self.gui_instance.root:
            self.gui_instance.root.after(0, self.gui_instance.append_log, msg, record.levelname)


class MockConfig:
    """用于独立测试的模拟配置类"""
    def __init__(self):
        self.username = "testuser"
        self.password = "password"
        self.server = "1.2.3.4"
        self.auto_login = True
        self.auto_start = False
        self.device_type = "PC"

    def get(self, key, default=None):
        return getattr(self, key, default)

    def save(self):
        logging.info(f"MockConfig: Pretending to save config: {self.__dict__}")


def mock_login(username, password, server, auto_login, auto_start, device_type):
    """模拟登录函数"""
    logging.info(
        f"Attempting login for {username} on {server} ({device_type}). Auto: {auto_login}, Start: {auto_start}")
    gui.update_status(f"正在为 {username} 登录...")

    def _task():
        import time
        time.sleep(2)
        if username == "testuser" and password == "password":
            logging.info("登录成功！")
            gui.update_status("登录成功！")
            gui.set_login_state(True)
        else:
            logging.error("登录失败：用户名或密码错误。")
            gui.update_status("登录失败：用户名或密码错误。")
            gui.set_login_state(False)

    threading.Thread(target=_task).start()


def mock_logout():
    """模拟注销函数"""
    logging.info("Attempting logout...")
    gui.update_status("正在注销...")

    def _task():
        import time
        time.sleep(1)
        logging.info("注销成功！")
        gui.update_status("已注销。")
        gui.set_login_state(False)

    threading.Thread(target=_task).start()


def mock_save_config(username, password, server, auto_login, auto_start, device_type):
    """模拟保存配置函数"""
    mock_config.username = username
    mock_config.password = password
    mock_config.server = server
    mock_config.auto_login = auto_login
    mock_config.auto_start = auto_start
    mock_config.device_type = device_type
    mock_config.save()
    logging.info(
        f"配置已保存: User={username}, Server={server}, AutoLogin={auto_login}, AutoStart={auto_start}, Device={device_type}")
    gui.update_status("配置已保存。")


if __name__ == '__main__':
    root = tk.Tk()
    mock_config = MockConfig()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        stream=sys.stdout)

    gui = LoginGUI(root, vars(mock_config), mock_login, mock_logout, mock_save_config)

    if mock_config.auto_login:
        root.after(1000, gui.on_login_click)

    root.mainloop()