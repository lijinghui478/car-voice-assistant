"""
车载语音助手 - 音频采集模块
支持PyAudio和Android AudioRecord两种方式
"""

import numpy as np
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class AudioCaptureHandler:
    """音频采集处理器"""
    
    def __init__(self, sample_rate=16000, channels=1, chunk_size=3200):
        """
        初始化音频采集器
        
        Args:
            sample_rate: 采样率，默认16000Hz（车机语音标准）
            channels: 声道数，默认1（单声道）
            chunk_size: 每次采集的帧数，默认3200（200ms）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_capturing = False
        self.audio_queue = queue.Queue(maxsize=100)
        self.audio_stream = None
        
        # 尝试导入PyAudio
        self.pyaudio_available = False
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.pyaudio_available = True
            logger.info("✓ PyAudio已导入")
        except ImportError:
            logger.warning("⚠ PyAudio未安装，将使用模拟音频")
            
        # Android环境检测
        self.android_available = self._check_android()
        if self.android_available:
            logger.info("✓ Android环境检测通过")
        
    def _check_android(self):
        """检测是否运行在Android环境"""
        try:
            import platform
            return "android" in platform.platform().lower()
        except:
            return False
    
    def start_capture(self):
        """启动音频采集"""
        if self.is_capturing:
            logger.warning("音频采集已在运行")
            return False
        
        self.is_capturing = True
        
        if self.android_available:
            # 使用Android AudioRecord API
            success = self._start_android_capture()
        elif self.pyaudio_available:
            # 使用PyAudio
            success = self._start_pyaudio_capture()
        else:
            # 模拟音频采集（测试用）
            success = self._start_mock_capture()
            
        if success:
            logger.info(f"✓ 音频采集已启动 | {self.sample_rate}Hz | {self.channels}ch")
        
        return success
    
    def _start_pyaudio_capture(self):
        """使用PyAudio启动音频采集"""
        try:
            p = self.pyaudio.PyAudio()
            
            # 配置音频流
            self.audio_stream = p.open(
                format=self.pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._pyaudio_callback
            )
            
            # 启动流
            self.audio_stream.start_stream()
            
            # 启动监控线程
            self.capture_thread = threading.Thread(target=self._monitor_capture)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"✗ PyAudio音频采集启动失败: {e}")
            return False
    
    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio音频回调"""
        if status:
            logger.warning(f"音频流状态: {status}")
        
        # 将音频数据转换为numpy数组
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # 放入队列
        try:
            if not self.audio_queue.full():
                self.audio_queue.put(audio_data)
        except queue.Full:
            pass  # 队列满时丢弃旧数据
        
        return (in_data, self.pyaudio.paContinue)
    
    def _start_android_capture(self):
        """使用Android AudioRecord启动音频采集"""
        try:
            # 导入Android桥接库
            import android
            droid = android.Android()
            
            # 使用Android AudioRecord API
            result = droid.audioCapture(
                self.sample_rate,
                self.channels,
                16,  # 16-bit PCM
                self.chunk_size
            )
            
            if result is None or result.error:
                logger.error(f"✗ Android音频采集失败: {result.error if result else 'Unknown'}")
                return False
            
            self.android_droid = droid
            
            # 启动采集线程
            self.capture_thread = threading.Thread(target=self._android_capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            return True
            
        except ImportError:
            logger.warning("⚠ Android桥接库未安装，回退到PyAudio")
            if self.pyaudio_available:
                return self._start_pyaudio_capture()
            else:
                return self._start_mock_capture()
        except Exception as e:
            logger.error(f"✗ Android音频采集启动失败: {e}")
            return False
    
    def _android_capture_loop(self):
        """Android音频采集循环"""
        while self.is_capturing:
            try:
                # 从Android获取音频数据
                result = self.android_droid.audioCaptureData()
                
                if result and result.result:
                    audio_data = np.array(result.result, dtype=np.int16)
                    
                    # 放入队列
                    try:
                        if not self.audio_queue.full():
                            self.audio_queue.put(audio_data)
                    except queue.Full:
                        pass
                        
                time.sleep(0.01)  # 10ms间隔
                
            except Exception as e:
                logger.error(f"Android音频采集错误: {e}")
                time.sleep(0.1)
    
    def _start_mock_capture(self):
        """启动模拟音频采集（测试用）"""
        logger.warning("⚠ 使用模拟音频采集，仅用于测试")
        
        def mock_capture_loop():
            while self.is_capturing:
                # 生成模拟音频数据（白噪声）
                mock_audio = np.random.randint(
                    -1000, 1000, 
                    size=self.chunk_size, 
                    dtype=np.int16
                )
                
                try:
                    if not self.audio_queue.full():
                        self.audio_queue.put(mock_audio)
                except queue.Full:
                    pass
                
                time.sleep(0.2)  # 200ms
        
        self.capture_thread = threading.Thread(target=mock_capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        return True
    
    def _monitor_capture(self):
        """监控音频采集状态"""
        while self.is_capturing:
            time.sleep(1)
            if self.audio_stream and not self.audio_stream.is_active():
                logger.warning("⚠ 音频流已停止，尝试重新启动")
                self._start_pyaudio_capture()
    
    def get_audio(self, timeout=0.1):
        """
        获取音频数据
        
        Args:
            timeout: 获取超时时间（秒）
            
        Returns:
            numpy数组格式的音频数据，超时返回None
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop_capture(self):
        """停止音频采集"""
        self.is_capturing = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
        
        # 等待采集线程结束
        if hasattr(self, 'capture_thread') and self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        logger.info("✓ 音频采集已停止")
    
    def get_audio_info(self):
        """获取音频信息"""
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "format": "PCM16",
            "backend": "Android" if self.android_available else ("PyAudio" if self.pyaudio_available else "Mock")
        }
