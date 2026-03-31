"""
车载语音助手 - 语音识别与智能对话模块
基于Qwen3-ASR进行语音识别，通过扣子Bot API进行深度对话
"""

import requests
import json
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

class VoiceAssistant:
    """语音助手核心类"""
    
    def __init__(self, coze_bot_token, coze_bot_id=None):
        """
        初始化语音助手
        
        Args:
            coze_bot_token: 扣子Bot API Token
            coze_bot_id: 扣子Bot ID（可选）
        """
        self.coze_bot_token = coze_bot_token
        self.coze_bot_id = coze_bot_id
        self.asr_model = None
        self.processor = None
        
        # 命令类型定义
        self.COMMAND_TYPES = {
            'MUSIC': ['播放', '暂停', '上一首', '下一首', '音乐', '搜索'],
            'AC': ['空调', '温度', '打开', '关闭', '调高', '调低'],
            'CAMERA': ['360', '全景', '摄像头', '视角', '前', '后', '左', '右', '窄道'],
            'NAV': ['导航', '地图', '路线', '高德', '百度', '腾讯'],
            'SYSTEM': ['设置', '默认', '提醒', '音']
        }
        
        print("✓ 语音助手初始化完成")
    
    def load_asr_model(self):
        """加载Qwen3-ASR模型"""
        try:
            model_id = "Qwen/Qwen3-ASR-1.7B"
            
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.asr_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            
            # 模型量化优化（减少内存占用）
            if torch.cuda.is_available():
                self.asr_model = self.asr_model.cuda()
            
            print("✓ Qwen3-ASR模型加载完成")
            return True
        
        except Exception as e:
            print(f"✗ ASR模型加载失败: {e}")
            return False
    
    def speech_to_text(self, audio_data):
        """
        语音转文字
        
        Args:
            audio_data: 音频数据 (16kHz单声道PCM)
        
        Returns:
            识别文本
        """
        if self.asr_model is None:
            print("✗ ASR模型未加载")
            return ""
        
        try:
            # 预处理音频
            inputs = self.processor(
                audio=audio_data,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            # 推理
            with torch.no_grad():
                generated_ids = self.asr_model.generate(**inputs)
            
            # 解码结果
            transcription = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]
            
            print(f"识别结果: {transcription}")
            return transcription
        
        except Exception as e:
            print(f"✗ 语音识别错误: {e}")
            return ""
    
    def parse_command(self, text):
        """
        解析语音指令类型
        
        Args:
            text: 用户语音文本
        
        Returns:
            {
                'type': 指令类型,
                'action': 具体动作,
                'params': 参数
            }
        """
        text = text.lower()
        
        # 优先级判断：音乐 > 空调 > 360 > 导航 > 系统
        for cmd_type, keywords in self.COMMAND_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    return self._extract_command_details(cmd_type, text)
        
        # 未匹配到指令，返回智能对话
        return {
            'type': 'CHAT',
            'action': 'chat',
            'params': {'query': text}
        }
    
    def _extract_command_details(self, cmd_type, text):
        """提取指令详情"""
        if cmd_type == 'MUSIC':
            return self._parse_music_command(text)
        elif cmd_type == 'AC':
            return self._parse_ac_command(text)
        elif cmd_type == 'CAMERA':
            return self._parse_camera_command(text)
        elif cmd_type == 'NAV':
            return self._parse_nav_command(text)
        elif cmd_type == 'SYSTEM':
            return self._parse_system_command(text)
        
        return {'type': 'UNKNOWN', 'action': 'unknown', 'params': {}}
    
    def _parse_music_command(self, text):
        """解析音乐控制指令"""
        if '播放' in text and '搜索' in text:
            # 搜索并播放
            song_name = text.replace('播放', '').replace('搜索', '').replace('音乐', '').strip()
            return {
                'type': 'MUSIC',
                'action': 'search_and_play',
                'params': {'song_name': song_name}
            }
        elif '播放' in text:
            return {
                'type': 'MUSIC',
                'action': 'play',
                'params': {}
            }
        elif '暂停' in text:
            return {
                'type': 'MUSIC',
                'action': 'pause',
                'params': {}
            }
        elif '下一首' in text:
            return {
                'type': 'MUSIC',
                'action': 'next',
                'params': {}
            }
        elif '上一首' in text:
            return {
                'type': 'MUSIC',
                'action': 'previous',
                'params': {}
            }
        
        return {'type': 'MUSIC', 'action': 'unknown', 'params': {}}
    
    def _parse_ac_command(self, text):
        """解析空调控制指令"""
        if '打开' in text or '开启' in text:
            return {
                'type': 'AC',
                'action': 'turn_on',
                'params': {}
            }
        elif '关闭' in text:
            return {
                'type': 'AC',
                'action': 'turn_off',
                'params': {}
            }
        elif '温度' in text:
            # 提取温度数值
            import re
            temp_match = re.search(r'(\d+)度', text)
            if temp_match:
                temp = int(temp_match.group(1))
                return {
                    'type': 'AC',
                    'action': 'set_temperature',
                    'params': {'temperature': temp}
                }
            elif '调高' in text:
                return {
                    'type': 'AC',
                    'action': 'increase_temp',
                    'params': {}
                }
            elif '调低' in text:
                return {
                    'type': 'AC',
                    'action': 'decrease_temp',
                    'params': {}
                }
        
        return {'type': 'AC', 'action': 'unknown', 'params': {}}
    
    def _parse_camera_command(self, text):
        """解析360全景控制指令"""
        if '打开' in text or '开启' in text:
            return {
                'type': 'CAMERA',
                'action': 'turn_on',
                'params': {}
            }
        elif '关闭' in text:
            return {
                'type': 'CAMERA',
                'action': 'turn_off',
                'params': {}
            }
        elif '前' in text:
            return {
                'type': 'CAMERA',
                'action': 'switch_view',
                'params': {'view': 'front'}
            }
        elif '后' in text:
            return {
                'type': 'CAMERA',
                'action': 'switch_view',
                'params': {'view': 'rear'}
            }
        elif '左' in text:
            return {
                'type': 'CAMERA',
                'action': 'switch_view',
                'params': {'view': 'left'}
            }
        elif '右' in text:
            return {
                'type': 'CAMERA',
                'action': 'switch_view',
                'params': {'view': 'right'}
            }
        elif '窄道' in text:
            return {
                'type': 'CAMERA',
                'action': 'narrow_mode',
                'params': {}
            }
        
        return {'type': 'CAMERA', 'action': 'unknown', 'params': {}}
    
    def _parse_nav_command(self, text):
        """解析导航控制指令"""
        if '高德' in text:
            app = 'amap'
        elif '百度' in text:
            app = 'baidu'
        elif '腾讯' in text:
            app = 'tencent'
        else:
            app = 'default'
        
        if '导航到' in text:
            destination = text.split('导航到')[1].strip()
            return {
                'type': 'NAV',
                'action': 'navigate_to',
                'params': {'destination': destination, 'app': app}
            }
        
        return {
            'type': 'NAV',
            'action': 'unknown',
            'params': {'app': app}
        }
    
    def _parse_system_command(self, text):
        """解析系统设置指令"""
        if '默认' in text:
            if '音乐' in text:
                return {
                    'type': 'SYSTEM',
                    'action': 'set_default_music',
                    'params': {}
                }
            elif '导航' in text:
                return {
                    'type': 'SYSTEM',
                    'action': 'set_default_nav',
                    'params': {}
                }
        elif '唤醒' in text and '提示音' in text:
            return {
                'type': 'SYSTEM',
                'action': 'set_wakeup_prompt',
                'params': {}
            }
        elif '免提示' in text:
            if '开启' in text:
                return {
                    'type': 'SYSTEM',
                    'action': 'disable_wakeup_prompt',
                    'params': {'enabled': True}
                }
            elif '关闭' in text:
                return {
                    'type': 'SYSTEM',
                    'action': 'disable_wakeup_prompt',
                    'params': {'enabled': False}
                }
        
        return {'type': 'SYSTEM', 'action': 'unknown', 'params': {}}
    
    def chat_with_coze(self, user_query, context=None):
        """
        与扣子Bot进行智能对话
        
        Args:
            user_query: 用户问题
            context: 上下文信息（车辆状态、位置等）
        
        Returns:
            Bot回复内容
        """
        url = f"https://api.coze.cn/open_api/v2/chat"
        
        headers = {
            "Authorization": f"Bearer {self.coze_bot_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 构建消息内容
        messages = []
        
        # 添加上下文信息
        if context:
            context_msg = f"""
当前车辆信息：
- 车型: 2021款丰田亚洲龙 2.5豪华版
- 车机: 方易通7870
- 当前状态: {context.get('vehicle_status', '未知')}
- 空调温度: {context.get('ac_temp', '未知')}度
- 燃油: {context.get('fuel_level', '未知')}
- 胎压: {context.get('tire_pressure', '未知')}
"""
            messages.append({
                "role": "system",
                "content": context_msg,
                "content_type": "text"
            })
        
        # 添加用户问题
        messages.append({
            "role": "user",
            "content": user_query,
            "content_type": "text"
        })
        
        payload = {
            "bot_id": self.coze_bot_id,
            "user": "car_user_001",
            "query": user_query,
            "stream": False,
            "chat_history": []
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                # 扣子API返回格式可能不同，需要根据实际调整
                if 'messages' in result:
                    for msg in result['messages']:
                        if msg.get('type') == 'answer':
                            return msg.get('content', '')
                return result.get('data', {}).get('answer', '抱歉，我没有理解你的问题。')
            else:
                print(f"✗ 扣子API调用失败: {response.status_code}")
                return "抱歉，对话服务暂时不可用。"
        
        except Exception as e:
            print(f"✗ 对话错误: {e}")
            return "抱歉，对话服务出现异常。"


# 使用示例
if __name__ == "__main__":
    # 初始化语音助手
    assistant = VoiceAssistant(
        coze_bot_token="your_coze_bot_token",
        coze_bot_id="your_coze_bot_id"
    )
    
    # 测试指令解析
    test_commands = [
        "播放周杰伦的七里香",
        "打开空调，温度调到24度",
        "打开360全景，切换到前视图",
        "导航到北京西站，用高德地图",
        "今天天气怎么样",
        "把默认音乐软件设为网易云音乐"
    ]
    
    print("\n=== 指令解析测试 ===\n")
    for cmd in test_commands:
        result = assistant.parse_command(cmd)
        print(f"指令: {cmd}")
        print(f"解析: {result}\n")
