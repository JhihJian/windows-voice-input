import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    """配置加载器 - 处理配置文件读取和本地模型加载逻辑"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # 创建默认配置
                self.config = self._get_default_config()
                self.save_config()
            return self.config
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            self.config = self._get_default_config()
            return self.config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "model": {
                "name": "paraformer-zh-streaming",
                "local_path": "./iic/paraformer-zh-streaming",
                "vad_model_path": "./iic/fsmn-vad",
                "sense_voice_path": "./iic/SenseVoiceSmall"
            },
            "audio": {
                "sample_rate": 16000,
                "chunk_size": [0, 10, 5],
                "encoder_chunk_look_back": 4,
                "decoder_chunk_look_back": 1
            },
            "input": {
                "caps_long_press_duration": 0.5,
                "enable_caps_toggle": True
            },
            "output": {
                "incremental_mode": True,
                "cross_app_input": True
            }
        }
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config.get("model", {})
    
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return self.config.get("audio", {})
    
    def get_input_config(self) -> Dict[str, Any]:
        """获取输入配置"""
        return self.config.get("input", {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """获取输出配置"""
        return self.config.get("output", {})
    
    def validate_model_paths(self) -> bool:
        """验证模型路径是否存在"""
        model_config = self.get_model_config()
        paths_to_check = [
            model_config.get("local_path"),
            model_config.get("vad_model_path"),
            model_config.get("sense_voice_path")
        ]
        
        for path in paths_to_check:
            if path and not os.path.exists(path):
                print(f"模型路径不存在: {path}")
                return False
        return True
    
    def get_model_path(self, prefer_local: bool = True) -> str:
        """获取模型路径 - 实现本地优先策略"""
        model_config = self.get_model_config()
        
        if prefer_local:
            local_path = model_config.get("local_path")
            if local_path and os.path.exists(local_path):
                return local_path
        
        # 回退到默认模型名称
        return model_config.get("name", "paraformer-zh-streaming")
    
    def update_config(self, key: str, value: Any) -> bool:
        """更新配置项"""
        try:
            keys = key.split('.')
            config_ref = self.config
            
            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # 设置值
            config_ref[keys[-1]] = value
            return self.save_config()
        except Exception as e:
            print(f"配置更新失败: {e}")
            return False