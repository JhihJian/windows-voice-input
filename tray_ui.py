import sys
import os
from typing import Callable, Optional
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, 
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QTextEdit, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from config_loader import ConfigLoader
from version_info import VersionInfo

class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(VersionInfo.get_version_string())
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息文本
        info_text = QTextEdit()
        info_text.setPlainText(VersionInfo.get_full_info())
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        layout.addWidget(info_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)


class TrayUI(QObject):
    """托盘UI模块 - 实现托盘图标功能和可视化交互"""
    
    # 信号定义
    start_recognition = pyqtSignal()
    stop_recognition = pyqtSignal()
    show_settings = pyqtSignal()
    quit_application = pyqtSignal()
    
    def __init__(self, config_loader: ConfigLoader):
        super().__init__()
        self.config_loader = config_loader
        self.app = None
        self.tray_icon = None
        self.tray_menu = None
        self.settings_dialog = None
        self.status_label = None
        
        # 状态管理
        self.is_recording = False
        self.recognition_status = "就绪"
        
        self._create_tray_icon()
        self._create_menu()
        self._setup_signals()
    
    def _create_tray_icon(self):
        """创建托盘图标"""
        # 创建简单的图标
        icon = self._create_icon()
        self.tray_icon = QSystemTrayIcon(icon)
        self.tray_icon.setToolTip("Windows语音识别工具")
    
    def _create_icon(self, color: str = "blue") -> QIcon:
        """创建图标"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 根据状态设置颜色
        if color == "red":
            painter.setBrush(QColor(255, 0, 0))
        elif color == "green":
            painter.setBrush(QColor(0, 255, 0))
        else:
            painter.setBrush(QColor(0, 0, 255))
        
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_menu(self):
        """创建托盘菜单"""
        self.tray_menu = QMenu()

        self.tray_menu.addSection("作者：正明 V1.0")
        # 关于
        about_action = QAction("关于")
        # about_action.triggered.connect(self._show_about)
        self.tray_menu.addAction(about_action)
        
        self.tray_menu.addSeparator()
        # 状态显示
        self.status_action = QAction(f"状态: {self.recognition_status}")
        self.status_action.setEnabled(False)
        self.tray_menu.addAction(self.status_action)
        
        self.tray_menu.addSeparator()
        
        # 开始/停止识别
        self.toggle_action = QAction("开始识别")
        self.toggle_action.triggered.connect(self._toggle_recognition)
        self.tray_menu.addAction(self.toggle_action)
        
        self.tray_menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置")
        settings_action.triggered.connect(self._show_settings)
        self.tray_menu.addAction(settings_action)
        

        
        # 退出
        quit_action = QAction("退出")
        quit_action.triggered.connect(self._quit_application)
        self.tray_menu.addAction(quit_action)
        
        # 确保设置上下文菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
    
    def _setup_signals(self):
        """设置信号连接"""
        self.tray_icon.activated.connect(self._on_tray_activated)
    
    def _on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_recognition()
    
    def _toggle_recognition(self):
        """切换识别状态"""
        if self.is_recording:
            self.stop_recognition.emit()
        else:
            self.start_recognition.emit()
    
    def _show_settings(self):
        """显示设置对话框"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config_loader)
        
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
    
    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog()
        dialog.exec_()
    
    def _quit_application(self):
        """退出应用程序"""
        self.quit_application.emit()
    
    def show(self):
        """显示托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self):
        """隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def update_status(self, status: str, is_recording: bool = False):
        """更新状态显示"""
        self.recognition_status = status
        self.is_recording = is_recording
        
        # 更新菜单文本
        if self.status_action:
            self.status_action.setText(f"状态: {status}")
        
        if self.toggle_action:
            self.toggle_action.setText("停止识别" if is_recording else "开始识别")
        
        # 更新图标颜色
        if is_recording:
            icon = self._create_icon("red")
        elif status == "就绪":
            icon = self._create_icon("green")
        else:
            icon = self._create_icon("blue")
        
        if self.tray_icon:
            self.tray_icon.setIcon(icon)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """显示托盘消息"""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, 3000)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_loader: ConfigLoader):
        super().__init__()
        self.config_loader = config_loader
        self.setWindowTitle("设置")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self._create_ui()
        self._load_settings()
    
    def _create_ui(self):
        """创建UI界面"""
        layout = QVBoxLayout()
        
        # 模型设置组
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()
        
        self.model_path_edit = QLineEdit()
        model_layout.addRow("模型路径:", self.model_path_edit)
        
        self.vad_path_edit = QLineEdit()
        model_layout.addRow("VAD模型路径:", self.vad_path_edit)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 输入设置组
        input_group = QGroupBox("输入设置")
        input_layout = QFormLayout()
        
        self.long_press_spin = QSpinBox()
        self.long_press_spin.setRange(100, 2000)
        self.long_press_spin.setSuffix(" ms")
        input_layout.addRow("长按时长:", self.long_press_spin)
        
        self.caps_toggle_check = QCheckBox("启用Caps切换")
        input_layout.addRow("", self.caps_toggle_check)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 音频设置组
        audio_group = QGroupBox("音频设置")
        audio_layout = QFormLayout()
        
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(8000, 48000)
        self.sample_rate_spin.setSingleStep(1000)
        audio_layout.addRow("采样率:", self.sample_rate_spin)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _load_settings(self):
        """加载设置"""
        config = self.config_loader.config
        
        # 模型设置
        model_config = config.get("model", {})
        self.model_path_edit.setText(model_config.get("local_path", ""))
        self.vad_path_edit.setText(model_config.get("vad_model_path", ""))
        
        # 输入设置
        input_config = config.get("input", {})
        duration_ms = int(input_config.get("caps_long_press_duration", 0.5) * 1000)
        self.long_press_spin.setValue(duration_ms)
        self.caps_toggle_check.setChecked(input_config.get("enable_caps_toggle", True))
        
        # 音频设置
        audio_config = config.get("audio", {})
        self.sample_rate_spin.setValue(audio_config.get("sample_rate", 16000))
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            self.config_loader.update_config("model.local_path", self.model_path_edit.text())
            self.config_loader.update_config("model.vad_model_path", self.vad_path_edit.text())
            
            duration_sec = self.long_press_spin.value() / 1000.0
            self.config_loader.update_config("input.caps_long_press_duration", duration_sec)
            self.config_loader.update_config("input.enable_caps_toggle", self.caps_toggle_check.isChecked())
            
            self.config_loader.update_config("audio.sample_rate", self.sample_rate_spin.value())
            
            self.accept()
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"保存设置失败: {e}")