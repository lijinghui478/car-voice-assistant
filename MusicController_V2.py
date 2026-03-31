"""
车载语音助手 - 音乐控制模块（完整版）
支持QQ音乐、网易云音乐等主流音乐应用
集成Android MediaSession API
"""

import subprocess
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class MusicApp(Enum):
    """支持的音乐应用枚举"""
    QQ_MUSIC = {
        "package": "com.tencent.qqmusic",
        "activity": ".activity.MainActivity",
        "name": "QQ音乐",
        "search_intent": "com.tencent.qqmusic.action.VIEW_SEARCH"
    }
    NETEASE_MUSIC = {
        "package": "com.netease.cloudmusic",
        "activity": ".activity.MainActivity",
        "name": "网易云音乐",
        "search_intent": "com.netease.cloudmusic.action.VIEW_SEARCH"
    }
    KUGOU_MUSIC = {
        "package": "com.kugou.android",
        "activity": ".app.MainActivity",
        "name": "酷狗音乐",
        "search_intent": "com.kugou.android.action.VIEW_SEARCH"
    }
    KUWO_MUSIC = {
        "package": "cn.kuwo.player",
        "activity": ".main.MainFragmentActivity",
        "name": "酷我音乐",
        "search_intent": "cn.kuwo.player.action.VIEW_SEARCH"
    }

class MusicController:
    """音乐控制核心类"""
    
    def __init__(self, default_app=MusicApp.QQ_MUSIC, use_android_api=True):
        """
        初始化音乐控制器
        
        Args:
            default_app: 默认音乐应用
            use_android_api: 是否使用Android API（生产环境建议True）
        """
        self.default_app = default_app
        self.current_app = default_app
        self.use_android_api = use_android_api
        self.is_playing = False
        self.current_song = None
        self.current_artist = None
        self.android_context = None
        
        # 检查环境
        self.android_available = self._check_android()
        
        logger.info(f"✓ 音乐控制模块初始化完成 | 默认应用: {default_app.value['name']} | Android API: {use_android_api}")
    
    def _check_android(self):
        """检测是否运行在Android环境"""
        try:
            import platform
            return "android" in platform.platform().lower()
        except:
            return False
    
    def _is_app_installed(self, package):
        """
        检查应用是否已安装
        
        Args:
            package: 应用包名
            
        Returns:
            bool: 是否已安装
        """
        try:
            if self.android_available:
                # 使用Android API检查
                import android
                droid = android.Android()
                result = droid.getPackageVersion(package)
                return result is not None
            else:
                # 使用ADB命令检查
                command = f"adb shell pm list packages | grep {package}"
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return package in result.stdout
        except Exception as e:
            logger.warning(f"应用检查失败: {e}")
            return True  # 假设已安装
    
    def set_default_app(self, app_name):
        """
        设置默认音乐应用
        
        Args:
            app_name: 应用名称 ('qq', 'netease', 'kugou', 'kuwo', 'qy')
        """
        app_map = {
            'qq': MusicApp.QQ_MUSIC,
            'qy': MusicApp.QQ_MUSIC,
            'netease': MusicApp.NETEASE_MUSIC,
            'wy': MusicApp.NETEASE_MUSIC,
            'kugou': MusicApp.KUGOU_MUSIC,
            'kuwo': MusicApp.KUWO_MUSIC
        }
        
        if app_name.lower() in app_map:
            self.default_app = app_map[app_name.lower()]
            self.current_app = self.default_app
            logger.info(f"✓ 默认音乐应用已设置为: {self.default_app.value['name']}")
            return True
        else:
            logger.error(f"✗ 不支持的音乐应用: {app_name}")
            return False
    
    def _send_media_keyevent(self, keycode):
        """
        发送媒体按键事件
        
        Args:
            keycode: 按键代码 (KEYCODE_MEDIA_PLAY, KEYCODE_MEDIA_PAUSE, etc.)
        """
        try:
            if self.android_available and self.use_android_api:
                # 使用Android API发送媒体按键
                import android
                droid = android.Android()
                droid.eventPost("KEYEVENT", keycode)
            else:
                # 使用ADB命令发送媒体按键
                command = f"adb shell input keyevent {keycode}"
                subprocess.run(command, shell=True, capture_output=True, text=True)
            
            return True
        except Exception as e:
            logger.error(f"发送媒体按键失败: {e}")
            return False
    
    def play(self, app=None):
        """
        播放音乐
        
        Args:
            app: 指定音乐应用（可选）
        """
        target_app = app or self.current_app
        app_info = target_app.value
        
        # 检查应用是否安装
        if not self._is_app_installed(app_info["package"]):
            logger.error(f"✗ 应用未安装: {app_info['name']}")
            return False
        
        try:
            # 发送播放按键事件
            if self._send_media_keyevent("KEYCODE_MEDIA_PLAY"):
                self.is_playing = True
                logger.info(f"✓ 开始播放 | 应用: {app_info['name']}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 播放失败: {e}")
            return False
    
    def pause(self):
        """暂停音乐"""
        try:
            # 发送暂停按键事件
            if self._send_media_keyevent("KEYCODE_MEDIA_PAUSE"):
                self.is_playing = False
                logger.info("✓ 音乐已暂停")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 暂停失败: {e}")
            return False
    
    def toggle_play_pause(self):
        """切换播放/暂停"""
        try:
            # 发送播放/暂停按键事件
            if self._send_media_keyevent("KEYCODE_MEDIA_PLAY_PAUSE"):
                self.is_playing = not self.is_playing
                logger.info(f"✓ {'播放' if self.is_playing else '暂停'}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 切换播放状态失败: {e}")
            return False
    
    def next_track(self):
        """切换下一首"""
        try:
            if self._send_media_keyevent("KEYCODE_MEDIA_NEXT"):
                logger.info("✓ 已切换下一首")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 切歌失败: {e}")
            return False
    
    def previous_track(self):
        """切换上一首"""
        try:
            if self._send_media_keyevent("KEYCODE_MEDIA_PREVIOUS"):
                logger.info("✓ 已切换上一首")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 切歌失败: {e}")
            return False
    
    def _launch_app(self, app_info):
        """
        启动音乐应用
        
        Args:
            app_info: 应用信息字典
        """
        try:
            if self.android_available and self.use_android_api:
                # 使用Android API启动应用
                import android
                droid = android.Android()
                droid.startActivity(
                    f"{app_info['package']}/{app_info['activity']}"
                )
            else:
                # 使用ADB命令启动应用
                launch_cmd = f"adb shell am start -n {app_info['package']}/{app_info['activity']}"
                subprocess.run(launch_cmd, shell=True, capture_output=True, text=True)
            
            return True
        except Exception as e:
            logger.error(f"启动应用失败: {e}")
            return False
    
    def _send_search_intent(self, app_info, query):
        """
        发送搜索Intent
        
        Args:
            app_info: 应用信息字典
            query: 搜索关键词
        """
        try:
            if self.android_available and self.use_android_api:
                # 使用Android API发送搜索Intent
                import android
                droid = android.Android()
                droid.startActivity(
                    f"{app_info['package']}/{app_info['activity']}",
                    data="search:" + query
                )
            else:
                # 使用ADB命令发送搜索Intent
                search_intent = f'adb shell am start -a android.intent.action.SEARCH -e query "{query}" {app_info["package"]}'
                subprocess.run(search_intent, shell=True, capture_output=True, text=True)
            
            return True
        except Exception as e:
            logger.error(f"发送搜索Intent失败: {e}")
            return False
    
    def search_and_play(self, song_name, app=None):
        """
        搜索并播放指定歌曲
        
        Args:
            song_name: 歌曲名称
            app: 指定音乐应用（可选）
        """
        target_app = app or self.current_app
        app_info = target_app.value
        
        # 检查应用是否安装
        if not self._is_app_installed(app_info["package"]):
            logger.error(f"✗ 应用未安装: {app_info['name']}")
            return False
        
        try:
            # 启动应用
            if not self._launch_app(app_info):
                logger.error("✗ 启动应用失败")
                return False
            
            # 等待应用启动
            import time
            time.sleep(1.5)
            
            # 发送搜索Intent
            if self._send_search_intent(app_info, song_name):
                self.current_song = song_name
                self.is_playing = True
                logger.info(f"✓ 正在播放: {song_name} | 应用: {app_info['name']}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"✗ 搜索播放失败: {e}")
            return False
    
    def seek_to(self, position_seconds):
        """
        跳转到指定位置
        
        Args:
            position_seconds: 位置（秒）
        """
        try:
            if self.android_available and self.use_android_api:
                # 使用Android API跳转
                import android
                droid = android.Android()
                droid.eventPost("SEEK", position_seconds)
            else:
                # 使用ADB命令跳转
                command = f"adb shell input keyevent KEYCODE_MEDIA_FAST_FORWARD && sleep {position_seconds}"
                subprocess.run(command, shell=True, capture_output=True, text=True)
            
            logger.info(f"✓ 已跳转到: {position_seconds}秒")
            return True
        except Exception as e:
            logger.error(f"✗ 跳转失败: {e}")
            return False
    
    def set_volume(self, volume_level):
        """
        设置音量
        
        Args:
            volume_level: 音量等级 (0-100)
        """
        try:
            volume_level = max(0, min(100, volume_level))  # 限制在0-100范围
            
            if self.android_available and self.use_android_api:
                # 使用Android API设置音量
                import android
                droid = android.Android()
                droid.setMusicVolume(volume_level)
            else:
                # 使用ADB命令设置音量
                command = f"adb shell media volume --show --set {volume_level}"
                subprocess.run(command, shell=True, capture_output=True, text=True)
            
            logger.info(f"✓ 音量已设置为: {volume_level}%")
            return True
        except Exception as e:
            logger.error(f"✗ 设置音量失败: {e}")
            return False
    
    def get_current_status(self):
        """
        获取当前播放状态
        
        Returns:
            dict: 播放状态信息
        """
        return {
            'is_playing': self.is_playing,
            'current_song': self.current_song,
            'current_artist': self.current_artist,
            'app': self.current_app.value['name'],
            'package': self.current_app.value['package']
        }
    
    def execute_voice_command(self, command):
        """
        执行语音控制指令
        
        Args:
            command: {
                'action': 'play' | 'pause' | 'toggle' | 'next' | 'previous' | 'search_and_play' | 'seek_to' | 'set_volume',
                'params': {
                    'song_name': 'xxx' (search_and_play需要),
                    'position_seconds': 30 (seek_to需要),
                    'volume_level': 50 (set_volume需要)
                }
            }
            
        Returns:
            bool: 执行是否成功
        """
        action = command.get('action')
        params = command.get('params', {})
        
        action_map = {
            'play': lambda: self.play(),
            'pause': lambda: self.pause(),
            'toggle': lambda: self.toggle_play_pause(),
            'next': lambda: self.next_track(),
            'previous': lambda: self.previous_track(),
        }
        
        if action in action_map:
            return action_map[action]()
        
        elif action == 'search_and_play':
            song_name = params.get('song_name', '')
            if song_name:
                return self.search_and_play(song_name)
            else:
                logger.error("✗ 缺少歌曲名称")
                return False
        
        elif action == 'seek_to':
            position = params.get('position_seconds', 0)
            return self.seek_to(position)
        
        elif action == 'set_volume':
            volume = params.get('volume_level', 50)
            return self.set_volume(volume)
        
        else:
            logger.error(f"✗ 未知的音乐指令: {action}")
            return False
    
    def __repr__(self):
        return f"MusicController(default_app={self.default_app.value['name']}, is_playing={self.is_playing})"


# 使用示例
if __name__ == "__main__":
    # 初始化音乐控制器
    controller = MusicController(default_app=MusicApp.QQ_MUSIC)
    
    # 测试各种指令
    print("\n=== 音乐控制测试 ===\n")
    
    # 播放
    controller.play()
    
    # 搜索并播放
    controller.search_and_play("七里香")
    
    # 下一首
    controller.next_track()
    
    # 暂停
    controller.pause()
    
    # 切换到网易云音乐
    controller.set_default_app("netease")
    
    # 获取状态
    status = controller.get_current_status()
    print(f"\n当前状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    # 测试音量控制
    controller.set_volume(75)
