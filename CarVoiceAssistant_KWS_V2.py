"""
车载语音助手 - 语音唤醒模块（完整版）
基于FunASR实现本地低功耗唤醒检测
"""

from funasr import AutoModel
import numpy as np
import threading
import time
import logging
from AudioCaptureHandler import AudioCaptureHandler

logger = logging.getLogger(__name__)

class VoiceWakeUp:
    """语音唤醒核心类"""
    
    def __init__(self, wake_word="小云小云", threshold=0.85, use_android=False):
        """
        初始化唤醒模型
        
        Args:
            wake_word: 唤醒词，默认"小云小云"
            threshold: 唤醒置信度阈值，0.85可降低误唤醒
            use_android: 是否使用Android AudioRecord API
        """
        self.wake_word = wake_word
        self.threshold = threshold
        self.is_listening = False
        self.callback = None
        self.model_loaded = False
        
        # 初始化音频采集器
        self.audio_capture = AudioCaptureHandler(sample_rate=16000, channels=1, chunk_size=3200)
        
        # 唤醒统计
        self.wake_count = 0
        self.false_wake_count = 0
        self.last_wake_time = 0
        
        # 加载唤醒模型
        self._load_model()
        
    def _load_model(self):
        """加载FunASR唤醒模型"""
        try:
            logger.info("正在加载唤醒模型...")
            
            # 加载FunASR唤醒模型
            self.model = AutoModel(
                model="iic/speech_sanm_kws_phone-xiaoyun-commands-online",
                device="cpu",  # 车机使用CPU，避免GPU兼容问题
                quantize=True  # INT8量化，减少内存占用
            )
            
            self.model_loaded = True
            logger.info(f"✓ 语音唤醒模块已加载 | 唤醒词: {self.wake_word}")
            
        except Exception as e:
            logger.error(f"✗ 唤醒模型加载失败: {e}")
            logger.warning("将使用模拟唤醒模式（仅用于测试）")
            self.model_loaded = False
    
    def set_callback(self, callback):
        """
        设置唤醒回调函数
        
        Args:
            callback: 回调函数，格式为 callback(wake_word)
        """
        self.callback = callback
        logger.debug("✓ 唤醒回调函数已设置")
    
    def start_listening(self):
        """启动语音监听"""
        if self.is_listening:
            logger.warning("语音监听已在运行")
            return False
        
        self.is_listening = True
        
        # 启动音频采集
        if not self.audio_capture.start_capture():
            logger.error("✗ 音频采集启动失败")
            self.is_listening = False
            return False
        
        logger.info("✓ 语音监听已启动")
        
        # 启动监听线程
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        return True
    
    def stop_listening(self):
        """停止语音监听"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        logger.info("正在停止语音监听...")
        
        # 停止音频采集
        self.audio_capture.stop_capture()
        
        # 等待监听线程结束
        if hasattr(self, 'listen_thread') and self.listen_thread:
            self.listen_thread.join(timeout=2)
        
        logger.info("✓ 语音监听已停止")
    
    def _listen_loop(self):
        """语音监听主循环"""
        logger.info("语音监听循环已启动")
        
        last_detect_time = 0
        debounce_interval = 2.0  # 唤醒间隔，避免连续触发
        
        while self.is_listening:
            try:
                # 获取音频数据
                audio_data = self.audio_capture.get_audio(timeout=0.5)
                
                if audio_data is None:
                    continue
                
                # 唤醒检测
                if self._detect_wake_word(audio_data):
                    current_time = time.time()
                    
                    # 防抖处理，避免连续触发
                    if current_time - last_detect_time >= debounce_interval:
                        self.wake_count += 1
                        last_detect_time = current_time
                        
                        logger.info(f"✓ 检测到唤醒词: {self.wake_word}")
                        logger.info(f"唤醒统计: 总唤醒 {self.wake_count} 次 | 误唤醒 {self.false_wake_count} 次")
                        
                        # 调用回调函数
                        if self.callback:
                            try:
                                self.callback(self.wake_word)
                            except Exception as e:
                                logger.error(f"✗ 唤醒回调执行失败: {e}")
                
            except Exception as e:
                logger.error(f"✗ 语音监听循环错误: {e}")
                time.sleep(0.1)
    
    def _detect_wake_word(self, audio_data):
        """
        检测唤醒词
        
        Args:
            audio_data: 音频数据（numpy数组）
            
        Returns:
            bool: 是否检测到唤醒词
        """
        # 如果模型未加载，使用模拟检测（测试用）
        if not self.model_loaded:
            return self._mock_detect(audio_data)
        
        try:
            # 归一化音频数据
            if len(audio_data.shape) == 1:
                audio_data = audio_data.reshape(1, -1)
            
            # 调用FunASR模型进行检测
            result = self.model.generate(
                input=audio_data,
                batch_size_s=300,
                cache={},
                language="zh",  # 中文
                use_itn=True
            )
            
            # 解析结果
            if result and len(result) > 0:
                text = result[0].get("text", "")
                confidence = result[0].get("confidence", 0.0)
                
                logger.debug(f"识别结果: {text} | 置信度: {confidence:.2f}")
                
                # 检查是否匹配唤醒词
                if self.wake_word in text and confidence >= self.threshold:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 唤醒词检测失败: {e}")
            return False
    
    def _mock_detect(self, audio_data):
        """
        模拟唤醒检测（测试用）
        
        Args:
            audio_data: 音频数据
            
        Returns:
            bool: 是否检测到唤醒词
        """
        # 模拟：每60秒随机触发一次唤醒（仅用于测试）
        import random
        if random.random() < 0.001:  # 0.1%的概率触发
            logger.warning("⚠ 使用模拟唤醒（测试模式）")
            return True
        return False
    
    def test_wake_word(self, audio_file):
        """
        测试唤醒词检测（用于调试）
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            dict: 检测结果
        """
        logger.info(f"正在测试唤醒词检测: {audio_file}")
        
        try:
            import scipy.io.wavfile as wavfile
            
            # 读取音频文件
            sample_rate, audio_data = wavfile.read(audio_file)
            
            # 转换为numpy数组
            if audio_data.dtype == np.float32:
                audio_data = (audio_data * 32768).astype(np.int16)
            
            # 检测唤醒词
            result = self._detect_wake_word(audio_data)
            
            logger.info(f"测试结果: {'✓ 检测到唤醒词' if result else '✗ 未检测到唤醒词'}")
            
            return {
                "success": True,
                "detected": result,
                "audio_file": audio_file,
                "sample_rate": sample_rate
            }
            
        except Exception as e:
            logger.error(f"✗ 测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_threshold(self, threshold):
        """
        设置唤醒阈值
        
        Args:
            threshold: 阈值，范围0.0-1.0
        """
        if 0.0 <= threshold <= 1.0:
            self.threshold = threshold
            logger.info(f"✓ 唤醒阈值已设置为: {threshold:.2f}")
        else:
            logger.warning("⚠ 阈值超出范围，必须在0.0-1.0之间")
    
    def get_stats(self):
        """
        获取唤醒统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "wake_count": self.wake_count,
            "false_wake_count": self.false_wake_count,
            "accuracy": (self.wake_count / max(self.wake_count + self.false_wake_count, 1)) * 100,
            "threshold": self.threshold,
            "model_loaded": self.model_loaded,
            "audio_info": self.audio_capture.get_audio_info()
        }
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop_listening()
