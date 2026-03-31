"""
车载语音助手 - 360全景影像控制模块（完整版）
控制方易通7870车机的360全景系统
增加车辆安全检查和Android API集成
"""

import subprocess
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CameraView(Enum):
    """摄像头视角"""
    FRONT = "front"      # 前视图
    REAR = "rear"        # 后视图
    LEFT = "left"        # 左视图
    RIGHT = "right"      # 右视图
    BIRD = "bird"        # 鸟瞰图
    PANORAMA = "panorama" # 全景图
    TOP = "top"          # 顶视图

class Camera360Controller:
    """360全景控制核心类"""
    
    def __init__(self, camera_package="com.camera360.app", max_safe_speed=15):
        """
        初始化360控制器
        
        Args:
            camera_package: 360全景应用包名
            max_safe_speed: 最大安全车速（km/h），超过此速度禁止操作
        """
        self.camera_package = camera_package
        self.max_safe_speed = max_safe_speed
        self.is_on = False
        self.current_view = CameraView.BIRD
        self.narrow_mode = False
        self.android_available = self._check_android()
        
        # 车辆状态
        self.vehicle_state = {
            "speed": 0.0,
            "gear": "P",
            "parking_brake": True
        }
        
        # 车机360控制相关Intent
        self.INTENT_OPEN_CAMERA = "com.camera360.action.OPEN"
        self.INTENT_CLOSE_CAMERA = "com.camera360.action.CLOSE"
        self.INTENT_SWITCH_VIEW = "com.camera360.action.SWITCH_VIEW"
        self.INTENT_NARROW_MODE = "com.camera360.action.NARROW_MODE"
        
        # 视图切换命令映射（根据实际车机系统调整）
        self.VIEW_COMMANDS = {
            CameraView.FRONT: "view_front",
            CameraView.REAR: "view_rear",
            CameraView.LEFT: "view_left",
            CameraView.RIGHT: "view_right",
            CameraView.BIRD: "view_bird",
            CameraView.PANORAMA: "view_panorama",
            CameraView.TOP: "view_top"
        }
        
        logger.info(f"✓ 360全景控制模块初始化完成 | 最大安全车速: {max_safe_speed}km/h")
    
    def _check_android(self):
        """检测是否运行在Android环境"""
        try:
            import platform
            return "android" in platform.platform().lower()
        except:
            return False
    
    def update_vehicle_state(self, state: Dict[str, Any]):
        """
        更新车辆状态
        
        Args:
            state: {
                'speed': 车速(km/h),
                'gear': 档位(P/R/N/D),
                'parking_brake': 手刹状态
            }
        """
        if state:
            self.vehicle_state.update(state)
            logger.debug(f"车辆状态更新: {state}")
    
    def _check_safety(self, check_speed=True) -> bool:
        """
        检查车辆是否处于安全状态
        
        Args:
            check_speed: 是否检查车速
            
        Returns:
            bool: 是否安全
        """
        # 检查手刹
        if not self.vehicle_state.get("parking_brake", True):
            gear = self.vehicle_state.get("gear", "")
            if gear not in ["P", "N"]:
                logger.warning("⚠ 车辆未挂P档或手刹未拉，存在安全风险")
                return False
        
        # 检查车速
        if check_speed:
            speed = self.vehicle_state.get("speed", 0.0)
            if speed > self.max_safe_speed:
                logger.warning(f"⚠ 车速过高（{speed}km/h），无法切换视角")
                return False
        
        return True
    
    def _send_intent(self, action: str, extras: Optional[Dict[str, str]] = None) -> bool:
        """
        发送Intent到车机
        
        Args:
            action: Intent action
            extras: 额外参数
            
        Returns:
            bool: 发送是否成功
        """
        try:
            if self.android_available:
                # 使用Android API发送Intent
                import android
                droid = android.Android()
                
                # 构建Intent
                intent_data = {"action": action}
                if extras:
                    intent_data["extras"] = extras
                
                droid.broadcastIntent(**intent_data)
                
            else:
                # 使用ADB命令发送Intent
                intent_cmd = f"adb shell am broadcast -a {action}"
                
                if extras:
                    for key, value in extras.items():
                        intent_cmd += f' -e {key} "{value}"'
                
                subprocess.run(intent_cmd, shell=True, capture_output=True, text=True)
            
            logger.debug(f"已发送Intent: {action}")
            return True
            
        except Exception as e:
            logger.error(f"✗ 发送Intent失败: {e}")
            return False
    
    def turn_on(self) -> bool:
        """
        打开360全景
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 启动360应用
            if not self._launch_app():
                logger.error("✗ 启动360应用失败")
                return False
            
            # 等待应用启动
            time.sleep(1.0)
            
            # 发送打开指令
            if self._send_intent(self.INTENT_OPEN_CAMERA):
                self.is_on = True
                logger.info("✓ 360全景已打开")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 打开360全景失败: {e}")
            return False
    
    def _launch_app(self) -> bool:
        """
        启动360应用
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.android_available:
                # 使用Android API启动应用
                import android
                droid = android.Android()
                droid.startActivity(f"{self.camera_package}/.MainActivity")
            else:
                # 使用ADB命令启动应用
                command = f"adb shell am start -n {self.camera_package}/.MainActivity"
                subprocess.run(command, shell=True, capture_output=True, text=True)
            
            logger.debug("360应用已启动")
            return True
            
        except Exception as e:
            logger.error(f"✗ 启动360应用失败: {e}")
            return False
    
    def turn_off(self) -> bool:
        """
        关闭360全景
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 发送关闭指令
            if self._send_intent(self.INTENT_CLOSE_CAMERA):
                self.is_on = False
                logger.info("✓ 360全景已关闭")
                
                # 关闭应用
                self._close_app()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 关闭360全景失败: {e}")
            return False
    
    def _close_app(self) -> bool:
        """
        关闭360应用
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.android_available:
                # 使用Android API关闭应用
                import android
                droid = android.Android()
                droid.forceStopPackage(self.camera_package)
            else:
                # 使用ADB命令关闭应用
                command = f"adb shell am force-stop {self.camera_package}"
                subprocess.run(command, shell=True, capture_output=True, text=True)
            
            logger.debug("360应用已关闭")
            return True
            
        except Exception as e:
            logger.error(f"✗ 关闭360应用失败: {e}")
            return False
    
    def switch_view(self, view: CameraView) -> bool:
        """
        切换360影像视角
        
        Args:
            view: 目标视角
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 安全检查
            if not self._check_safety(check_speed=False):  # 允许低速时切换
                return False
            
            # 检查360是否已打开
            if not self.is_on:
                logger.warning("⚠ 360全景未打开")
                return False
            
            # 获取视角命令
            view_command = self.VIEW_COMMANDS.get(view)
            if not view_command:
                logger.error(f"✗ 不支持的视角: {view}")
                return False
            
            # 发送视角切换指令
            if self._send_intent(self.INTENT_SWITCH_VIEW, {"view": view_command}):
                self.current_view = view
                logger.info(f"✓ 已切换到: {view.name} 视角")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 切换视角失败: {e}")
            return False
    
    def toggle_narrow_mode(self) -> bool:
        """
        切换窄道模式
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 安全检查
            if not self._check_safety():
                return False
            
            # 检查360是否已打开
            if not self.is_on:
                logger.warning("⚠ 360全景未打开")
                return False
            
            # 发送窄道模式切换指令
            if self._send_intent(self.INTENT_NARROW_MODE, {"enable": str(not self.narrow_mode)}):
                self.narrow_mode = not self.narrow_mode
                status = "开启" if self.narrow_mode else "关闭"
                logger.info(f"✓ 窄道模式已{status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 切换窄道模式失败: {e}")
            return False
    
    def open_narrow_mode(self) -> bool:
        """
        开启窄道模式
        
        Returns:
            bool: 操作是否成功
        """
        if not self.narrow_mode:
            return self.toggle_narrow_mode()
        logger.info("窄道模式已开启")
        return True
    
    def close_narrow_mode(self) -> bool:
        """
        关闭窄道模式
        
        Returns:
            bool: 操作是否成功
        """
        if self.narrow_mode:
            return self.toggle_narrow_mode()
        logger.info("窄道模式已关闭")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取360系统状态
        
        Returns:
            dict: 状态信息
        """
        return {
            "is_on": self.is_on,
            "current_view": self.current_view.name,
            "narrow_mode": self.narrow_mode,
            "vehicle_speed": self.vehicle_state.get("speed", 0.0),
            "safe_to_operate": self._check_safety(check_speed=False)
        }
    
    def execute_voice_command(self, command: Dict[str, Any]) -> bool:
        """
        执行语音控制指令
        
        Args:
            command: {
                'action': 'turn_on' | 'turn_off' | 'switch_view' | 'toggle_narrow_mode' | 'open_narrow_mode' | 'close_narrow_mode',
                'params': {
                    'view': 'front' | 'rear' | 'left' | 'right' | 'bird' | 'panorama' | 'top'
                }
            }
            
        Returns:
            bool: 执行是否成功
        """
        action = command.get('action')
        params = command.get('params', {})
        
        action_map = {
            'turn_on': lambda: self.turn_on(),
            'turn_off': lambda: self.turn_off(),
            'toggle_narrow_mode': lambda: self.toggle_narrow_mode(),
            'open_narrow_mode': lambda: self.open_narrow_mode(),
            'close_narrow_mode': lambda: self.close_narrow_mode(),
        }
        
        if action in action_map:
            return action_map[action]()
        
        elif action == 'switch_view':
            view_name = params.get('view', 'bird')
            view_map = {
                'front': CameraView.FRONT,
                'rear': CameraView.REAR,
                'left': CameraView.LEFT,
                'right': CameraView.RIGHT,
                'bird': CameraView.BIRD,
                'panorama': CameraView.PANORAMA,
                'top': CameraView.TOP
            }
            
            if view_name.lower() in view_map:
                return self.switch_view(view_map[view_name.lower()])
            else:
                logger.error(f"✗ 不支持的视角: {view_name}")
                return False
        
        else:
            logger.error(f"✗ 未知的360指令: {action}")
            return False
    
    def __repr__(self):
        return f"Camera360Controller(is_on={self.is_on}, current_view={self.current_view.name}, narrow_mode={self.narrow_mode})"


# 使用示例
if __name__ == "__main__":
    # 初始化360控制器
    camera = Camera360Controller(max_safe_speed=15)
    
    # 测试各种指令
    print("\n=== 360全景控制测试 ===\n")
    
    # 打开360
    camera.turn_on()
    
    # 切换视角
    camera.switch_view(CameraView.FRONT)
    camera.switch_view(CameraView.BIRD)
    
    # 开启窄道模式
    camera.open_narrow_mode()
    
    # 获取状态
    status = camera.get_status()
    print(f"\n当前状态: {status}")
    
    # 测试语音指令
    camera.execute_voice_command({
        'action': 'switch_view',
        'params': {'view': 'rear'}
    })
    
    # 关闭360
    camera.turn_off()
