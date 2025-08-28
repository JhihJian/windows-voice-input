import sys
import os
import ctypes
import threading
import time
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

# 导入自定义模块
from config_loader import ConfigLoader
from voice_recognizer import VoiceRecognizer
from input_controller import InputController
from tray_ui import TrayUI
from version_info import VersionInfo
from logger import app_logger
class TextOutputManager:
    """文本输出管理器 - 处理跨应用文本输入"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
    
    def send_text(self, text: str):
        """发送文本到当前活动窗口"""
        try:
            # 获取当前活动窗口
            hwnd = self.user32.GetForegroundWindow()
            if not hwnd:
                return False
            
            # 模拟文本输入
            for char in text:
                if char == ' ':
                    # 发送空格键
                    self.user32.keybd_event(0x20, 0, 0, 0)  # 按下
                    self.user32.keybd_event(0x20, 0, 2, 0)  # 释放
                else:
                    # 发送Unicode字符
                    self.user32.SendMessageW(hwnd, 0x0102, ord(char), 0)  # WM_CHAR
            
            return True
            
        except Exception as e:
            app_logger.info(f"文本输出失败: {e}")
            return False

class VoiceInputApp(QObject):
    """主应用程序类 - 整合各模块功能和协调业务流程"""
    
    def __init__(self):
        super().__init__()
        # 显示启动信息
        VersionInfo.print_startup_info()
        # 初始化组件
        self.config_loader = ConfigLoader()
        self.voice_recognizer = VoiceRecognizer(self.config_loader)
        self.input_controller = InputController(self.config_loader)
        self.tray_ui = TrayUI(self.config_loader)
        self.text_output = TextOutputManager()
        
        # 状态管理
        self.is_running = False
        self.is_recognizing = False
        
        self._setup_connections()
        self._initialize_components()
    
    def _setup_connections(self):
        """设置组件间的连接"""
        # 语音识别回调
        self.voice_recognizer.set_callback(self._on_recognition_result)
        
        # 输入控制回调
        self.input_controller.set_callbacks(
            on_start=self._on_long_press_start,
            on_end=self._on_long_press_end
        )
        
        # UI信号连接
        self.tray_ui.start_recognition.connect(self._start_manual_recognition)
        self.tray_ui.stop_recognition.connect(self._stop_manual_recognition)
        self.tray_ui.quit_application.connect(self._quit_application)
    
    def _initialize_components(self):
        """初始化各组件"""
        # 检查模型是否加载成功
        if not self.voice_recognizer.is_model_loaded():
            self.tray_ui.show_message(
                "错误", 
                "语音识别模型加载失败，请检查配置",
                self.tray_ui.tray_icon.Critical
            )
            self.tray_ui.update_status("模型加载失败")
        else:
            self.tray_ui.update_status("就绪")
    
    def start(self) -> bool:
        """启动应用程序"""
        try:
            # 启动输入监控
            if not self.input_controller.start_monitoring():
                app_logger.info("启动输入监控失败")
                return False
            
            # 显示托盘图标
            self.tray_ui.show()
            
            self.is_running = True
            app_logger.info("语音识别工具已启动")
            
            # 显示启动消息
            self.tray_ui.show_message(
                "语音识别工具",
                "已启动，长按Caps键开始语音输入"
            )
            
            return True
            
        except Exception as e:
            app_logger.info(f"启动失败: {e}")
            return False
    
    def stop(self):
        """停止应用程序"""
        if not self.is_running:
            return
        
        try:
            # 停止识别
            self._stop_recognition()
            
            # 停止输入监控
            self.input_controller.stop_monitoring()
            
            # 隐藏托盘图标
            self.tray_ui.hide()
            
            self.is_running = False
            app_logger.info("语音识别工具已停止")
            
        except Exception as e:
            app_logger.info(f"停止时出错: {e}")
    
    def _on_long_press_start(self):
        """长按开始事件处理"""
        app_logger.info("检测到Caps长按，开始语音识别")
        self._start_recognition()
    
    def _on_long_press_end(self):
        """长按结束事件处理"""
        app_logger.info("Caps长按结束，停止语音识别")
        self._stop_recognition()
    
    def _start_recognition(self):
        """开始语音识别"""
        if self.is_recognizing:
            return
        
        if not self.voice_recognizer.is_model_loaded():
            self.tray_ui.show_message(
                "错误",
                "语音识别模型未加载",
                self.tray_ui.tray_icon.Critical
            )
            return
        
        if self.voice_recognizer.start_recording():
            self.is_recognizing = True
            self.tray_ui.update_status("正在识别", True)
            app_logger.info("语音识别已开始")
        else:
            self.tray_ui.show_message(
                "错误",
                "启动语音识别失败",
                self.tray_ui.tray_icon.Critical
            )
    
    def _stop_recognition(self):
        """停止语音识别"""
        if not self.is_recognizing:
            return
        
        self.voice_recognizer.stop_recording()
        self.is_recognizing = False
        self.tray_ui.update_status("就绪", False)
        app_logger.info("语音识别已停止")
    
    def _start_manual_recognition(self):
        """手动开始识别（通过托盘菜单）"""
        self._start_recognition()
    
    def _stop_manual_recognition(self):
        """手动停止识别（通过托盘菜单）"""
        self._stop_recognition()
    
    def _on_recognition_result(self, text: str):
        """处理识别结果"""
        if text and text.strip():
            app_logger.info(f"识别结果: {text}")
            
            # 输出文本到当前活动窗口
            if self.text_output.send_text(text):
                app_logger.info(f"文本已输出: {text}")
            else:
                app_logger.info(f"文本输出失败: {text}")
    
    def _quit_application(self):
        """退出应用程序"""
        self.stop()
        QApplication.quit()

def main():
    """主函数"""
    # 检查是否已有实例运行
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 检查系统托盘支持
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "系统托盘",
            "系统不支持托盘功能"
        )
        sys.exit(1)
    
    # 创建应用程序实例
    voice_app = VoiceInputApp()
    
    # 启动应用程序
    if not voice_app.start():
        QMessageBox.critical(
            None,
            "启动失败",
            "语音识别工具启动失败"
        )
        sys.exit(1)
    
    # 运行应用程序
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        app_logger.info("\n收到中断信号，正在退出...")
        voice_app.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()