import logging
import os
from datetime import datetime

class AppLogger:
    """应用程序日志管理器"""
    
    def __init__(self, log_file="voice_input.log"):
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "VoiceInput")
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = os.path.join(log_dir, self.log_file)
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                # 在调试模式下也输出到控制台
                # logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('VoiceInput')
    
    def info(self, message):
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message):
        """记录错误日志"""
        self.logger.error(message)
    
    def warning(self, message):
        """记录警告日志"""
        self.logger.warning(message)
    
    def debug(self, message):
        """记录调试日志"""
        self.logger.debug(message)

# 全局日志实例
app_logger = AppLogger()