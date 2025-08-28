import numpy as np
import sounddevice as sd
import threading
import queue
import time
import os
from typing import Callable, Optional, Dict, Any
from funasr import AutoModel
from config_loader import ConfigLoader

class VoiceRecognizer:
    """语音识别器 - 封装语音识别模型调用和音频流处理逻辑"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.model = None
        self.vad_model = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recognition_thread = None
        self.callback_func: Optional[Callable[[str], None]] = None
        
        # 音频参数
        audio_config = config_loader.get_audio_config()
        self.sample_rate = audio_config.get("sample_rate", 16000)
        self.chunk_size = audio_config.get("chunk_size", [0, 10, 5])
        self.encoder_chunk_look_back = audio_config.get("encoder_chunk_look_back", 4)
        self.decoder_chunk_look_back = audio_config.get("decoder_chunk_look_back", 1)
        
        # 初始化模型
        self._load_models()
    
    def _load_models(self) -> bool:
        """加载语音识别模型"""
        try:
            model_path = self.config_loader.get_model_path(prefer_local=True)
            print(f"正在加载语音识别模型: {model_path}")
            
            # 加载主识别模型
            self.model = AutoModel(model=model_path)
            
            # 尝试加载VAD模型
            model_config = self.config_loader.get_model_config()
            vad_path = model_config.get("vad_model_path")
            if vad_path and os.path.exists(vad_path):
                try:
                    self.vad_model = AutoModel(model=vad_path)
                    print(f"VAD模型加载成功: {vad_path}")
                except Exception as e:
                    print(f"VAD模型加载失败: {e}")
            
            print("语音识别模型加载完成")
            return True
            
        except Exception as e:
            print(f"模型加载失败: {e}")
            return False
    
    def set_callback(self, callback: Callable[[str], None]):
        """设置识别结果回调函数"""
        self.callback_func = callback
    
    def start_recording(self) -> bool:
        """开始录音和识别"""
        if self.is_recording or not self.model:
            return False
        
        try:
            self.is_recording = True
            self.audio_queue = queue.Queue()
            
            # 启动音频录制线程
            self.audio_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback
            )
            self.audio_stream.start()
            
            # 启动识别处理线程
            self.recognition_thread = threading.Thread(
                target=self._recognition_worker,
                daemon=True
            )
            self.recognition_thread.start()
            
            print("开始语音识别")
            return True
            
        except Exception as e:
            print(f"启动录音失败: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self):
        """停止录音和识别"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        try:
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop()
                self.audio_stream.close()
            
            # 等待识别线程结束
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.recognition_thread.join(timeout=2.0)
            
            print("语音识别已停止")
            
        except Exception as e:
            print(f"停止录音时出错: {e}")
    
    def _audio_callback(self, indata, frames, time, status):
        """音频数据回调函数"""
        if status:
            print(f"音频录制状态: {status}")
        
        if self.is_recording:
            # 将音频数据放入队列
            audio_data = indata.copy().flatten()
            self.audio_queue.put(audio_data)
    
    def _recognition_worker(self):
        """识别工作线程"""
        cache = {}
        chunk_stride = self.chunk_size[1] * 960  # 计算步长
        audio_buffer = np.array([], dtype=np.float32)
        
        while self.is_recording:
            try:
                # 获取音频数据
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                except queue.Empty:
                    continue
                
                # 当缓冲区有足够数据时进行识别
                while len(audio_buffer) >= chunk_stride:
                    # 提取一个chunk进行识别
                    speech_chunk = audio_buffer[:chunk_stride]
                    audio_buffer = audio_buffer[chunk_stride:]
                    
                    # 执行识别
                    try:
                        result = self.model.generate(
                            input=speech_chunk,
                            cache=cache,
                            is_final=False,
                            chunk_size=self.chunk_size,
                            encoder_chunk_look_back=self.encoder_chunk_look_back,
                            decoder_chunk_look_back=self.decoder_chunk_look_back
                        )
                        
                        # 处理识别结果
                        if result and len(result) > 0:
                            text = self._extract_text_from_result(result)
                            if text and text.strip():
                                if self.callback_func:
                                    self.callback_func(text.strip())
                    
                    except Exception as e:
                        print(f"识别过程出错: {e}")
                        continue
                
            except Exception as e:
                print(f"识别工作线程出错: {e}")
                time.sleep(0.1)
        
        # 处理剩余的音频数据
        if len(audio_buffer) > 0:
            try:
                result = self.model.generate(
                    input=audio_buffer,
                    cache=cache,
                    is_final=True,
                    chunk_size=self.chunk_size,
                    encoder_chunk_look_back=self.encoder_chunk_look_back,
                    decoder_chunk_look_back=self.decoder_chunk_look_back
                )
                
                if result and len(result) > 0:
                    text = self._extract_text_from_result(result)
                    if text and text.strip():
                        if self.callback_func:
                            self.callback_func(text.strip())
            except Exception as e:
                print(f"最终识别处理出错: {e}")
    
    def _extract_text_from_result(self, result) -> str:
        """从识别结果中提取文本"""
        try:
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    return result[0].get('text', '')
                elif isinstance(result[0], str):
                    return result[0]
            elif isinstance(result, dict):
                return result.get('text', '')
            elif isinstance(result, str):
                return result
            return ''
        except Exception as e:
            print(f"提取文本时出错: {e}")
            return ''
    
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model is not None
    
    def reload_models(self) -> bool:
        """重新加载模型"""
        self.stop_recording()
        return self._load_models()