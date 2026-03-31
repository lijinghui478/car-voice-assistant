"""
车载语音助手 - 主程序入口
整合所有模块，实现完整的语音交互流程
"""

import sys
import time
import threading
from CarVoiceAssistant_KWS import VoiceWakeUp
from CarVoiceAssistant_ASR import VoiceAssistant
from MusicController import MusicController, MusicApp
from ACController import ACController
from Camera360Controller import Camera360Controller
from NavigationController import NavigationController, NavApp
from ConfigManager import ConfigManager

class CarVoiceAssistantApp:
    """车载语音助手主程序"""
    
    def __init__(self):
        """初始化应用"""
        print("\n" + "="*60)
        print("     🚗 车机智能语音助手 - 启动中...")
        print("="*60 + "\n")
        
        # 加载配置
        self.config = ConfigManager()
        
        # 初始化各模块
        self._init_modules()
        
        # 车辆状态
        self.vehicle_state = {
            'speed': 0,
            'engine_on': False,
            'door_open': False
        }
        
        # 运行标志
        self.is_running = False
        
        print("\n✓ 所有模块初始化完成\n")
        print("="*60)
        print("     🎉 车机智能语音助手已就绪")
        print("="*60 + "\n")
    
    def _init_modules(self):
        """初始化所有模块"""
        # 1. 初始化语音唤醒
        wake_word = self.config.get("voice.wake_word", "小云小云")
        threshold = self.config.get("voice.wakeup_threshold", 0.85)
        self.kws = VoiceWakeUp(wake_word=wake_word, threshold=threshold)
        self.kws.set_callback(self.on_wake_up)
        
        # 2. 初始化语音识别和对话
        coze_token = self.config.get("coze.bot_token", "")
        coze_bot_id = self.config.get("coze.bot_id", "")
        self.voice_assistant = VoiceAssistant(coze_token, coze_bot_id)
        
        # 可选：加载ASR模型（如果需要）
        # self.voice_assistant.load_asr_model()
        
        # 3. 初始化音乐控制器
        default_music = self.config.get("apps.default_music", "qq")
        music_app_map = {
            'qq': MusicApp.QQ_MUSIC,
            'netease': MusicApp.NETEASE_MUSIC,
            'kugou': MusicApp.KUGOU_MUSIC,
            'kuwo': MusicApp.KUWO_MUSIC
        }
        self.music = MusicController(default_app=music_app_map.get(default_music, MusicApp.QQ_MUSIC))
        
        # 4. 初始化空调控制器
        self.ac = ACController()
        
        # 5. 初始化360控制器
        self.camera = Camera360Controller()
        
        # 6. 初始化导航控制器
        default_nav = self.config.get("apps.default_navigation", "amap")
        nav_app_map = {
            'amap': NavApp.AMAP,
            'baidu': NavApp.BAIDU,
            'tencent': NavApp.TENCENT
        }
        self.nav = NavigationController(default_app=nav_app_map.get(default_nav, NavApp.AMAP))
    
    def on_wake_up(self, word, confidence):
        """唤醒回调函数"""
        print(f"\n{'='*60}")
        print(f"  ✓ 唤醒成功! | 唤醒词: {word} | 置信度: {confidence:.2f}")
        print(f"{'='*60}\n")
        
        # 播放唤醒提示音（如果开启）
        if self.config.get("voice.wakeup_prompt_enabled", True):
            self._play_wakeup_sound()
        
        # 进入语音识别模式
        self._start_voice_recognition()
    
    def _play_wakeup_sound(self):
        """播放唤醒提示音"""
        sound_file = self.config.get("voice.wakeup_prompt_sound", "default")
        print(f"♪ 播放唤醒提示音: {sound_file}")
        # TODO: 实现实际音频播放
        # 可以使用Android MediaPlayer播放本地音频文件
    
    def _start_voice_recognition(self):
        """启动语音识别"""
        print("🎤 正在听... (请说出您的指令)")
        
        # TODO: 实际音频采集
        # 这里模拟用户输入
        user_input = input("👉 请输入指令 (或直接回车跳过): ").strip()
        
        if not user_input:
            print("✗ 未检测到语音输入")
            return
        
        # 解析指令
        command = self.voice_assistant.parse_command(user_input)
        print(f"\n📋 指令解析: {command}\n")
        
        # 执行指令
        self._execute_command(command)
    
    def _execute_command(self, command):
        """执行语音指令"""
        cmd_type = command.get('type')
        action = command.get('action')
        params = command.get('params', {})
        
        if cmd_type == 'MUSIC':
            print("🎵 执行音乐控制指令...")
            self.music.execute_voice_command(command)
        
        elif cmd_type == 'AC':
            print("❄️  执行空调控制指令...")
            self.ac.execute_voice_command(command)
        
        elif cmd_type == 'CAMERA':
            print("📷 执行360全景控制指令...")
            self.camera.execute_voice_command(command)
        
        elif cmd_type == 'NAV':
            print("🧭 执行导航控制指令...")
            self.nav.execute_voice_command(command)
        
        elif cmd_type == 'SYSTEM':
            print("⚙️  执行系统设置指令...")
            self._handle_system_command(action, params)
        
        elif cmd_type == 'CHAT':
            print("💬 进入智能对话模式...")
            self._handle_chat(params)
        
        else:
            print("✗ 未识别的指令类型")
    
    def _handle_system_command(self, action, params):
        """处理系统设置指令"""
        if action == 'set_default_music':
            # 通过语音让用户选择
            print("请选择默认音乐应用：")
            print("1. QQ音乐")
            print("2. 网易云音乐")
            print("3. 酷狗音乐")
            print("4. 酷我音乐")
            choice = input("请输入编号 (1-4): ").strip()
            
            music_map = {
                '1': 'qq',
                '2': 'netease',
                '3': 'kugou',
                '4': 'kuwo'
            }
            
            if choice in music_map:
                self.config.set_default_music_app(music_map[choice])
                self.music.set_default_app(music_map[choice])
        
        elif action == 'set_default_nav':
            # 通过语音让用户选择
            print("请选择默认导航应用：")
            print("1. 高德地图")
            print("2. 百度地图")
            print("3. 腾讯地图")
            choice = input("请输入编号 (1-3): ").strip()
            
            nav_map = {
                '1': 'amap',
                '2': 'baidu',
                '3': 'tencent'
            }
            
            if choice in nav_map:
                self.config.set_default_nav_app(nav_map[choice])
                self.nav.set_default_app(nav_map[choice])
        
        elif action == 'set_wakeup_prompt':
            print("✓ 唤醒提示音设置已更新")
        
        elif action == 'disable_wakeup_prompt':
            enabled = params.get('enabled', False)
            self.config.toggle_wakeup_prompt(enabled)
        
        else:
            print(f"✗ 未知的系统指令: {action}")
    
    def _handle_chat(self, params):
        """处理智能对话"""
        query = params.get('query', '')
        
        if not query:
            print("✗ 对话内容为空")
            return
        
        # 构建上下文信息
        context = {
            'vehicle_status': '行驶中' if self.vehicle_state.get('speed', 0) > 0 else '停车',
            'ac_temp': self.ac.temperature,
            'fuel_level': '未知',
            'tire_pressure': '未知'
        }
        
        # 调用扣子Bot进行对话
        response = self.voice_assistant.chat_with_coze(query, context)
        
        print(f"\n🤖 智能回复:\n{response}\n")
        
        # TODO: 使用TTS播放回复
        # self._speak(response)
    
    def _speak(self, text):
        """语音播报"""
        print(f"🔊 语音播报: {text}")
        # TODO: 实现TTS语音合成
        # 可以使用扣子TTS或系统TTS
    
    def start(self):
        """启动应用"""
        print("🚀 启动语音监听服务...\n")
        
        self.is_running = True
        
        # 启动语音唤醒
        self.kws.start_listening()
        
        # 主循环
        try:
            while self.is_running:
                # 定期更新车辆状态
                self._update_vehicle_status()
                
                # 避免CPU占用过高
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  收到中断信号，正在关闭...")
            self.stop()
    
    def stop(self):
        """停止应用"""
        print("\n正在关闭应用...")
        
        self.is_running = False
        
        # 停止语音监听
        if hasattr(self, 'kws'):
            self.kws.stop_listening()
        
        # 断开硬件连接
        if hasattr(self, 'ac'):
            self.ac.disconnect()
        
        print("✓ 应用已关闭")
    
    def _update_vehicle_status(self):
        """更新车辆状态"""
        # TODO: 通过协议盒子读取车辆状态
        # 这里模拟更新
        pass
    
    def show_menu(self):
        """显示交互菜单"""
        print("\n" + "="*60)
        print("         📱 车机智能语音助手 - 交互菜单")
        print("="*60)
        print("1. 🎵 音乐控制")
        print("2. ❄️  空调控制")
        print("3. 📷 360全景")
        print("4. 🧭 导航控制")
        print("5. ⚙️  系统设置")
        print("6. 💬 智能对话")
        print("7. 📊 查看状态")
        print("0. 🚪 退出程序")
        print("="*60)
    
    def run_interactive_mode(self):
        """交互模式（用于测试）"""
        self.is_running = True
        
        while self.is_running:
            self.show_menu()
            
            choice = input("\n请选择功能 (0-7): ").strip()
            
            if choice == '0':
                self.stop()
                break
            
            elif choice == '1':
                self._interactive_music()
            elif choice == '2':
                self._interactive_ac()
            elif choice == '3':
                self._interactive_camera()
            elif choice == '4':
                self._interactive_nav()
            elif choice == '5':
                self._interactive_settings()
            elif choice == '6':
                self._interactive_chat()
            elif choice == '7':
                self._show_status()
            else:
                print("✗ 无效的选择")
    
    def _interactive_music(self):
        """音乐控制交互"""
        print("\n🎵 音乐控制")
        print("1. 播放  2. 暂停  3. 下一首  4. 上一首  5. 搜索播放  0. 返回")
        choice = input("请选择: ").strip()
        
        if choice == '1':
            self.music.play()
        elif choice == '2':
            self.music.pause()
        elif choice == '3':
            self.music.next_track()
        elif choice == '4':
            self.music.previous_track()
        elif choice == '5':
            song = input("请输入歌曲名称: ").strip()
            if song:
                self.music.search_and_play(song)
    
    def _interactive_ac(self):
        """空调控制交互"""
        print("\n❄️ 空调控制")
        print("1. 开启  2. 关闭  3. 设置温度  4. 升温  5. 降温  0. 返回")
        choice = input("请选择: ").strip()
        
        if choice == '1':
            self.ac.turn_on()
        elif choice == '2':
            self.ac.turn_off()
        elif choice == '3':
            temp = input("请输入温度 (16-30): ").strip()
            if temp.isdigit():
                self.ac.set_temperature(int(temp))
        elif choice == '4':
            self.ac.increase_temperature()
        elif choice == '5':
            self.ac.decrease_temperature()
    
    def _interactive_camera(self):
        """360控制交互"""
        print("\n📷 360全景")
        print("1. 打开  2. 关闭  3. 前视  4. 后视  5. 左视  6. 右视  7. 鸟瞰  8. 窄道  0. 返回")
        choice = input("请选择: ").strip()
        
        if choice == '1':
            self.camera.turn_on()
        elif choice == '2':
            self.camera.turn_off()
        elif choice == '3':
            self.camera.switch_to_front()
        elif choice == '4':
            self.camera.switch_to_rear()
        elif choice == '5':
            self.camera.switch_to_left()
        elif choice == '6':
            self.camera.switch_to_right()
        elif choice == '7':
            self.camera.switch_to_bird()
        elif choice == '8':
            self.camera.enable_narrow_mode()
    
    def _interactive_nav(self):
        """导航控制交互"""
        print("\n🧭 导航控制")
        print("1. 导航到  2. 搜索附近  3. 停止导航  0. 返回")
        choice = input("请选择: ").strip()
        
        if choice == '1':
            dest = input("请输入目的地: ").strip()
            if dest:
                self.nav.navigate_to(dest)
        elif choice == '2':
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                self.nav.search_nearby(keyword)
        elif choice == '3':
            self.nav.stop_navigation()
    
    def _interactive_settings(self):
        """设置交互"""
        print("\n⚙️ 系统设置")
        print("1. 设置默认音乐  2. 设置默认导航  3. 切换唤醒提示音  4. 设置扣子Bot  0. 返回")
        choice = input("请选择: ").strip()
        
        if choice == '1':
            self._handle_system_command('set_default_music', {})
        elif choice == '2':
            self._handle_system_command('set_default_nav', {})
        elif choice == '3':
            enabled = input("是否开启唤醒提示音 (y/n): ").strip().lower() == 'y'
            self.config.toggle_wakeup_prompt(enabled)
        elif choice == '4':
            token = input("请输入扣子Bot Token: ").strip()
            bot_id = input("请输入扣子Bot ID (可选): ").strip()
            self.config.set_coze_config(token, bot_id)
    
    def _interactive_chat(self):
        """对话交互"""
        print("\n💬 智能对话")
        query = input("请输入您的问题 (或输入 'exit' 退出): ").strip()
        
        if query.lower() != 'exit':
            self._handle_chat({'query': query})
    
    def _show_status(self):
        """显示系统状态"""
        print("\n📊 系统状态")
        print("-" * 60)
        
        # 配置信息
        print("\n⚙️ 配置:")
        print(f"  唤醒词: {self.config.get('voice.wake_word')}")
        print(f"  默认音乐: {self.config.get('apps.default_music')}")
        print(f"  默认导航: {self.config.get('apps.default_navigation')}")
        print(f"  唤醒提示音: {'开启' if self.config.get('voice.wakeup_prompt_enabled') else '关闭'}")
        
        # 模块状态
        print("\n📦 模块状态:")
        print(f"  音乐播放: {'播放中' if self.music.is_playing else '已暂停'}")
        print(f"  空调状态: {'开启' if self.ac.is_on else '关闭'} | 温度: {self.ac.temperature}°C")
        print(f"  360全景: {'开启' if self.camera.is_on else '关闭'}")
        print(f"  导航状态: {'导航中' if self.nav.is_navigating else '未导航'}")
        if self.nav.current_destination:
            print(f"  当前目的地: {self.nav.current_destination}")
        
        print("\n" + "-" * 60)


def main():
    """主函数"""
    # 创建应用实例
    app = CarVoiceAssistantApp()
    
    # 显示启动信息
    print("\n启动模式选择:")
    print("1. 语音监听模式 (自动监听语音指令)")
    print("2. 交互测试模式 (通过菜单操作)")
    
    mode = input("\n请选择启动模式 (1-2，默认2): ").strip()
    
    if mode == '1':
        # 语音监听模式
        app.start()
    else:
        # 交互测试模式
        app.run_interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 程序异常: {e}")
        import traceback
        traceback.print_exc()
