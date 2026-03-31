"""
车载语音助手 - 空调控制模块（完整版）
通过协议盒子控制车辆空调系统
"""

import serial
import time
import logging
import json
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ACMode(Enum):
    """空调模式枚举"""
    AUTO = "auto"
    COOL = "cool"
    HEAT = "heat"
    FAN_ONLY = "fan_only"
    OFF = "off"

class FanSpeed(Enum):
    """风扇速度枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    AUTO = 0  # 自动模式

class ACController:
    """空调控制核心类"""
    
    def __init__(self, serial_port="/dev/ttyUSB0", baud_rate=115200, timeout=1.0):
        """
        初始化空调控制器
        
        Args:
            serial_port: 串口设备路径
            baud_rate: 波特率
            timeout: 串口超时时间（秒）
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn = None
        self.is_connected = False
        
        # 当前状态
        self.current_temp = 22.0  # 当前温度（摄氏度）
        self.target_temp = 22.0   # 目标温度
        self.current_mode = ACMode.OFF
        self.fan_speed = FanSpeed.AUTO
        self.is_ac_on = False
        
        # 车辆状态缓存
        self.vehicle_state = {
            "outside_temp": 25.0,
            "inside_temp": 22.0,
            "engine_temp": 90.0
        }
        
        # 初始化连接
        self._initialize_connection()
        
        logger.info(f"✓ 空调控制模块初始化完成 | 串口: {serial_port}")
    
    def _initialize_connection(self):
        """初始化串口连接"""
        try:
            # 尝试自动检测串口
            detected_port = self._find_serial_port()
            if detected_port:
                self.serial_port = detected_port
                logger.info(f"✓ 自动检测到串口: {detected_port}")
            
            # 打开串口连接
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.is_connected = True
            logger.info(f"✓ 串口连接成功: {self.serial_port} @ {self.baud_rate}")
            
            # 读取当前空调状态
            self._read_current_status()
            
        except serial.SerialException as e:
            logger.error(f"✗ 串口连接失败: {e}")
            logger.warning("将使用模拟模式进行测试")
            self.is_connected = False
        except Exception as e:
            logger.error(f"✗ 初始化失败: {e}")
            self.is_connected = False
    
    def _find_serial_port(self):
        """
        自动检测串口设备
        
        Returns:
            str: 检测到的串口路径，未检测到返回None
        """
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            
            # 优先查找USB串口
            for port in ports:
                if "USB" in port.device or "ttyUSB" in port.device:
                    # 尝试打开测试
                    try:
                        test_conn = serial.Serial(port.device, baudrate=self.baud_rate, timeout=0.5)
                        test_conn.close()
                        logger.info(f"✓ 检测到可用串口: {port.device}")
                        return port.device
                    except:
                        continue
            
            logger.warning("⚠ 未检测到可用串口")
            return None
            
        except ImportError:
            logger.warning("⚠ pyserial未安装，无法自动检测串口")
            return None
        except Exception as e:
            logger.warning(f"⚠ 串口检测失败: {e}")
            return None
    
    def _read_current_status(self):
        """读取当前空调状态"""
        if not self.is_connected:
            # 模拟读取状态
            self.current_temp = 22.0
            self.is_ac_on = False
            return True
        
        try:
            # 发送状态查询命令
            status_command = self._build_command("READ_STATUS")
            self._send_command(status_command)
            
            # 读取响应
            response = self._read_response()
            
            if response:
                self._parse_status(response)
                logger.debug(f"当前状态: {json.dumps(self.get_status(), ensure_ascii=False)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 读取状态失败: {e}")
            return False
    
    def _build_command(self, cmd_type, **kwargs):
        """
        构建空调控制命令
        
        Args:
            cmd_type: 命令类型 (READ_STATUS, SET_TEMP, SET_MODE, SET_FAN, TURN_ON, TURN_OFF)
            **kwargs: 命令参数
            
        Returns:
            bytes: 命令字节流
        """
        # 命令帧结构: [起始字节][命令类型][数据长度][数据][校验和][结束字节]
        # 以下为示例格式，实际格式需根据协议盒子文档调整
        
        START_BYTE = 0xAA
        END_BYTE = 0x55
        
        # 命令类型映射
        CMD_MAP = {
            "READ_STATUS": 0x01,
            "SET_TEMP": 0x10,
            "SET_MODE": 0x11,
            "SET_FAN": 0x12,
            "TURN_ON": 0x13,
            "TURN_OFF": 0x14
        }
        
        cmd_byte = CMD_MAP.get(cmd_type, 0x00)
        
        # 构建数据部分
        data_bytes = []
        
        if cmd_type == "SET_TEMP":
            temp = kwargs.get("temp", 22)
            data_bytes = [int(temp)]
        
        elif cmd_type == "SET_MODE":
            mode = kwargs.get("mode", "AUTO")
            mode_map = {"AUTO": 0x00, "COOL": 0x01, "HEAT": 0x02, "FAN_ONLY": 0x03}
            data_bytes = [mode_map.get(mode, 0x00)]
        
        elif cmd_type == "SET_FAN":
            speed = kwargs.get("speed", 0)
            data_bytes = [int(speed)]
        
        # 构建完整命令
        frame = [START_BYTE, cmd_byte, len(data_bytes)] + data_bytes
        
        # 计算校验和
        checksum = sum(frame[1:]) & 0xFF
        frame.append(checksum)
        frame.append(END_BYTE)
        
        return bytes(frame)
    
    def _send_command(self, command):
        """
        发送命令到协议盒子
        
        Args:
            command: 命令字节流
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected:
            logger.debug("串口未连接，模拟发送命令")
            return True
        
        try:
            self.serial_conn.write(command)
            self.serial_conn.flush()
            logger.debug(f"已发送命令: {command.hex()}")
            return True
        except Exception as e:
            logger.error(f"✗ 发送命令失败: {e}")
            return False
    
    def _read_response(self, timeout=2.0):
        """
        读取协议盒子响应
        
        Args:
            timeout: 读取超时时间（秒）
            
        Returns:
            bytes: 响应数据，失败返回None
        """
        if not self.is_connected:
            # 模拟响应
            return bytes([0xAA, 0x01, 0x00, 0x01, 0x55])
        
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    response = self.serial_conn.read(self.serial_conn.in_waiting)
                    
                    # 验证响应帧格式
                    if len(response) >= 5 and response[0] == 0xAA and response[-1] == 0x55:
                        logger.debug(f"收到响应: {response.hex()}")
                        return response
                    else:
                        logger.warning(f"收到无效响应: {response.hex()}")
                
                time.sleep(0.01)
            
            logger.warning("⚠ 响应超时")
            return None
            
        except Exception as e:
            logger.error(f"✗ 读取响应失败: {e}")
            return None
    
    def _parse_status(self, response):
        """
        解析状态响应
        
        Args:
            response: 响应字节流
        """
        try:
            if len(response) < 5:
                return
            
            # 解析数据部分（根据实际协议调整）
            data_len = response[2]
            
            if data_len >= 1:
                # 状态字节
                status_byte = response[3]
                self.is_ac_on = (status_byte & 0x01) != 0
                
            if data_len >= 2:
                # 温度字节
                self.current_temp = float(response[4])
                
        except Exception as e:
            logger.error(f"✗ 解析状态失败: {e}")
    
    def turn_on(self):
        """开启空调"""
        try:
            command = self._build_command("TURN_ON")
            
            if self._send_command(command):
                response = self._read_response()
                
                if response:
                    self.is_ac_on = True
                    logger.info("✓ 空调已开启")
                    return True
            
            # 模拟模式
            if not self.is_connected:
                self.is_ac_on = True
                logger.info("✓ 空调已开启（模拟）")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 开启空调失败: {e}")
            return False
    
    def turn_off(self):
        """关闭空调"""
        try:
            command = self._build_command("TURN_OFF")
            
            if self._send_command(command):
                response = self._read_response()
                
                if response:
                    self.is_ac_on = False
                    logger.info("✓ 空调已关闭")
                    return True
            
            # 模拟模式
            if not self.is_connected:
                self.is_ac_on = False
                logger.info("✓ 空调已关闭（模拟）")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 关闭空调失败: {e}")
            return False
    
    def set_temperature(self, temperature: float, unit: str = "celsius"):
        """
        设置目标温度
        
        Args:
            temperature: 温度值
            unit: 温度单位 (celsius/fahrenheit)，默认摄氏度
        """
        try:
            # 温度单位转换
            if unit.lower() == "fahrenheit":
                temperature = (temperature - 32) * 5 / 9
            
            # 温度范围限制（16-30摄氏度）
            temperature = max(16.0, min(30.0, temperature))
            
            command = self._build_command("SET_TEMP", temp=temperature)
            
            if self._send_command(command):
                response = self._read_response()
                
                if response:
                    self.target_temp = temperature
                    logger.info(f"✓ 空调温度已设置为: {temperature:.1f}°C")
                    return True
            
            # 模拟模式
            if not self.is_connected:
                self.target_temp = temperature
                logger.info(f"✓ 空调温度已设置为: {temperature:.1f}°C（模拟）")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 设置温度失败: {e}")
            return False
    
    def increase_temperature(self, delta: float = 1.0):
        """
        调高温度
        
        Args:
            delta: 温度增量（摄氏度）
        """
        new_temp = self.target_temp + delta
        return self.set_temperature(new_temp)
    
    def decrease_temperature(self, delta: float = 1.0):
        """
        调低温度
        
        Args:
            delta: 温度减量（摄氏度）
        """
        new_temp = self.target_temp - delta
        return self.set_temperature(new_temp)
    
    def set_mode(self, mode: str):
        """
        设置空调模式
        
        Args:
            mode: 模式名称 (auto/cool/heat/fan_only/off)
        """
        try:
            mode_map = {
                "auto": ACMode.AUTO,
                "cool": ACMode.COOL,
                "heat": ACMode.HEAT,
                "fan_only": ACMode.FAN_ONLY,
                "off": ACMode.OFF
            }
            
            if mode.lower() not in mode_map:
                logger.error(f"✗ 不支持的空调模式: {mode}")
                return False
            
            new_mode = mode_map[mode.lower()]
            
            command = self._build_command("SET_MODE", mode=new_mode.name)
            
            if self._send_command(command):
                response = self._read_response()
                
                if response:
                    self.current_mode = new_mode
                    if mode == "off":
                        self.is_ac_on = False
                    else:
                        self.is_ac_on = True
                    logger.info(f"✓ 空调模式已设置为: {new_mode.name}")
                    return True
            
            # 模拟模式
            if not self.is_connected:
                self.current_mode = new_mode
                if mode == "off":
                    self.is_ac_on = False
                else:
                    self.is_ac_on = True
                logger.info(f"✓ 空调模式已设置为: {new_mode.name}（模拟）")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 设置模式失败: {e}")
            return False
    
    def set_fan_speed(self, speed: int):
        """
        设置风扇速度
        
        Args:
            speed: 风扇速度 (0=自动, 1=低, 2=中, 3=高)
        """
        try:
            speed = max(0, min(3, speed))
            self.fan_speed = FanSpeed(speed)
            
            command = self._build_command("SET_FAN", speed=speed)
            
            if self._send_command(command):
                response = self._read_response()
                
                if response:
                    logger.info(f"✓ 风扇速度已设置为: {self.fan_speed.name}")
                    return True
            
            # 模拟模式
            if not self.is_connected:
                logger.info(f"✓ 风扇速度已设置为: {self.fan_speed.name}（模拟）")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 设置风扇速度失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取空调当前状态
        
        Returns:
            dict: 状态信息
        """
        return {
            "is_ac_on": self.is_ac_on,
            "current_temp": self.current_temp,
            "target_temp": self.target_temp,
            "mode": self.current_mode.name if self.current_mode else "unknown",
            "fan_speed": self.fan_speed.name,
            "is_connected": self.is_connected
        }
    
    def execute_voice_command(self, command: Dict[str, Any]) -> bool:
        """
        执行语音控制指令
        
        Args:
            command: {
                'action': 'turn_on' | 'turn_off' | 'set_temperature' | 'increase_temperature' | 'decrease_temperature' | 'set_mode' | 'set_fan_speed',
                'params': {
                    'temperature': 22.0,
                    'delta': 1.0,
                    'mode': 'cool',
                    'speed': 2
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
        }
        
        if action in action_map:
            return action_map[action]()
        
        elif action == 'set_temperature':
            temp = params.get('temperature', 22.0)
            return self.set_temperature(temp)
        
        elif action == 'increase_temperature':
            delta = params.get('delta', 1.0)
            return self.increase_temperature(delta)
        
        elif action == 'decrease_temperature':
            delta = params.get('delta', 1.0)
            return self.decrease_temperature(delta)
        
        elif action == 'set_mode':
            mode = params.get('mode', 'auto')
            return self.set_mode(mode)
        
        elif action == 'set_fan_speed':
            speed = params.get('speed', 0)
            return self.set_fan_speed(speed)
        
        else:
            logger.error(f"✗ 未知的空调指令: {action}")
            return False
    
    def close(self):
        """关闭串口连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            logger.info("✓ 串口连接已关闭")
    
    def __del__(self):
        """析构函数"""
        self.close()
    
    def __repr__(self):
        return f"ACController(is_ac_on={self.is_ac_on}, target_temp={self.target_temp}°C, mode={self.current_mode.name if self.current_mode else 'unknown'})"


# 使用示例
if __name__ == "__main__":
    # 初始化空调控制器
    ac = ACController(serial_port="/dev/ttyUSB0")
    
    # 测试各种指令
    print("\n=== 空调控制测试 ===\n")
    
    # 开启空调
    ac.turn_on()
    
    # 设置温度
    ac.set_temperature(24.0)
    
    # 调高温度
    ac.increase_temperature(1.0)
    
    # 设置模式
    ac.set_mode("cool")
    
    # 设置风扇速度
    ac.set_fan_speed(2)
    
    # 获取状态
    status = ac.get_status()
    print(f"\n当前状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    # 测试语音指令
    ac.execute_voice_command({
        'action': 'decrease_temperature',
        'params': {'delta': 2.0}
    })
    
    # 关闭空调
    ac.turn_off()
