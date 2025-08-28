import time
import threading
from typing import Callable, Optional
import keyboard
from config_loader import ConfigLoader

class InputController:
    """输入控制器 - 监测Caps键长按事件和管理麦克风输入启停"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.is_monitoring = False
        self.caps_pressed = False
        self.caps_press_time = 0
        self.long_press_triggered = False
        self.long_press_timer = None
        
        # 回调函数
        self.on_long_press_start: Optional[Callable] = None
        self.on_long_press_end: Optional[Callable] = None
        
        # 配置参数
        input_config = config_loader.get_input_config()
        self.long_press_duration = input_config.get("caps_long_press_duration", 0.5)
        self.enable_caps_toggle = input_config.get("enable_caps_toggle", True)
    
    def set_callbacks(self, on_start: Callable, on_end: Callable):
        """设置长按开始和结束的回调函数"""
        self.on_long_press_start = on_start
        self.on_long_press_end = on_end
    
    def start_monitoring(self) -> bool:
        """启动键盘监控"""
        try:
            if self.is_monitoring:
                return True
            
            # 注册Caps键事件监听
            keyboard.on_press_key('caps lock', self._on_caps_press)
            keyboard.on_release_key('caps lock', self._on_caps_release)
            
            self.is_monitoring = True
            print("开始监控Caps键")
            return True
            
        except Exception as e:
            print(f"启动键盘监控失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止键盘监控"""
        try:
            if not self.is_monitoring:
                return
            
            # 取消事件监听
            keyboard.unhook_all()
            
            # 取消长按计时器
            if self.long_press_timer:
                self.long_press_timer.cancel()
                self.long_press_timer = None
            
            self.is_monitoring = False
            self.caps_pressed = False
            self.long_press_triggered = False
            print("停止监控Caps键")
            
        except Exception as e:
            print(f"停止键盘监控失败: {e}")
    
    def _on_caps_press(self, event):
        """Caps键按下事件处理"""
        if self.caps_pressed:
            return  # 避免重复触发
        
        self.caps_pressed = True
        self.caps_press_time = time.time()
        self.long_press_triggered = False
        
        # 启动长按检测计时器
        self.long_press_timer = threading.Timer(
            self.long_press_duration, 
            self._trigger_long_press
        )
        self.long_press_timer.start()
    
    def _on_caps_release(self, event):
        """Caps键释放事件处理"""
        if not self.caps_pressed:
            return
        
        # 取消长按计时器
        if self.long_press_timer:
            self.long_press_timer.cancel()
            self.long_press_timer = None
        
        press_duration = time.time() - self.caps_press_time
        
        if self.long_press_triggered:
            # 长按结束
            if self.on_long_press_end:
                self.on_long_press_end()
                # 切换大小写锁定
                # self._toggle_caps_lock()
        else:
            # 短按 - 不做任何操作，让系统处理Caps Lock
            # 移除手动切换逻辑，避免与系统冲突
            pass
        
        self.caps_pressed = False
        self.long_press_triggered = False
    
    def _trigger_long_press(self):
        """触发长按事件"""
        # 切换大小写锁定
        self._toggle_caps_lock()
        if self.caps_pressed and not self.long_press_triggered:
            self.long_press_triggered = True
            if self.on_long_press_start:
                self.on_long_press_start()
    
    def _toggle_caps_lock(self):
        """切换大小写锁定状态"""
        try:
            # 使用keyboard库切换Caps Lock状态
            keyboard.press_and_release('caps lock')
        except Exception as e:
            print(f"切换Caps Lock失败: {e}")
    
    def is_long_press_active(self) -> bool:
        """检查是否正在长按"""
        return self.long_press_triggered
    
    def update_config(self, long_press_duration: float = None, enable_caps_toggle: bool = None):
        """更新配置参数"""
        if long_press_duration is not None:
            self.long_press_duration = long_press_duration
            self.config_loader.update_config("input.caps_long_press_duration", long_press_duration)
        
        if enable_caps_toggle is not None:
            self.enable_caps_toggle = enable_caps_toggle
            self.config_loader.update_config("input.enable_caps_toggle", enable_caps_toggle)
            