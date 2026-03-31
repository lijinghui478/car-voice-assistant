"""
车载语音助手 - 导航控制模块（完整版）
支持高德地图、百度地图、腾讯地图
集成Android Intent和地理编码
"""

import subprocess
import urllib.parse
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class NavigationApp(Enum):
    """支持的导航应用枚举"""
    AMAP = {
        "package": "com.autonavi.minimap",
        "activity": ".activity.MapActivity",
        "name": "高德地图",
        "search_intent": "android.intent.action.VIEW",
        "uri_scheme": "amapuri://route/plan/"
    }
    BAIDU_MAP = {
        "package": "com.baidu.BaiduMap",
        "activity": ".BaiduMapMainActivity",
        "name": "百度地图",
        "search_intent": "android.intent.action.VIEW",
        "uri_scheme": "baidumap://map/direction"
    }
    TENCENT_MAP = {
        "package": "com.tencent.map",
        "activity": ".map.MapActivity",
        "name": "腾讯地图",
        "search_intent": "android.intent.action.VIEW",
        "uri_scheme": "qqmap://map/routeplan"
    }

class NavigationController:
    """导航控制核心类"""
    
    def __init__(self, default_app=NavigationApp.AMAP, use_android_api=True):
        """
        初始化导航控制器
        
        Args:
            default_app: 默认导航应用
            use_android_api: 是否使用Android API（生产环境建议True）
        """
        self.default_app = default_app
        self.current_app = default_app
        self.use_android_api = use_android_api
        self.android_available = self._check_android()
        
        # 导航状态
        self.is_navigating = False
        self.current_destination = None
        self.current_route = None
        
        logger.info(f"✓ 导航控制模块初始化完成 | 默认应用: {default_app.value['name']} | Android API: {use_android_api}")
    
    def _check_android(self) -> bool:
        """检测是否运行在Android环境"""
        try:
            import platform
            return "android" in platform.platform().lower()
        except:
            return False
    
    def _is_app_installed(self, package: str) -> bool:
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
    
    def set_default_app(self, app_name: str) -> bool:
        """
        设置默认导航应用
        
        Args:
            app_name: 应用名称 ('amap', 'baidu', 'tencent', 'gaode')
        """
        app_map = {
            'amap': NavigationApp.AMAP,
            'gaode': NavigationApp.AMAP,
            'baidu': NavigationApp.BAIDU_MAP,
            'tencent': NavigationApp.TENCENT_MAP,
            'tx': NavigationApp.TENCENT_MAP
        }
        
        if app_name.lower() in app_map:
            self.default_app = app_map[app_name.lower()]
            self.current_app = self.default_app
            logger.info(f"✓ 默认导航应用已设置为: {self.default_app.value['name']}")
            return True
        else:
            logger.error(f"✗ 不支持的导航应用: {app_name}")
            return False
    
    def _build_navigation_uri(self, app: NavigationApp, destination: str, 
                              origin: Optional[str] = None, 
                              mode: str = "driving") -> str:
        """
        构建导航URI
        
        Args:
            app: 导航应用
            destination: 目的地
            origin: 起点（可选）
            mode: 导航模式 (driving/walking/transit/riding)
            
        Returns:
            str: 导航URI
        """
        app_info = app.value
        base_uri = app_info.get("uri_scheme", "")
        
        # 根据不同应用构建URI
        if app == NavigationApp.AMAP:
            # 高德地图URI: amapuri://route/plan/?sid=起点坐标&did=终点坐标&dname=终点名称&dev=0&t=0
            encoded_dest = urllib.parse.quote(destination)
            uri = f"{base_uri}?dname={encoded_dest}&dev=0&t=0"
            
            if origin:
                encoded_origin = urllib.parse.quote(origin)
                uri += f"&sname={encoded_origin}"
                
        elif app == NavigationApp.BAIDU_MAP:
            # 百度地图URI: baidumap://map/direction?destination=name:终点|latlng:经度,纬度&mode=driving
            encoded_dest = urllib.parse.quote(destination)
            uri = f"{base_uri}?destination=name:{encoded_dest}&mode={mode}"
            
            if origin:
                encoded_origin = urllib.parse.quote(origin)
                uri += f"&origin=name:{encoded_origin}"
                
        elif app == NavigationApp.TENCENT_MAP:
            # 腾讯地图URI: qqmap://map/routeplan?type=drive&to=终点&from=起点
            encoded_dest = urllib.parse.quote(destination)
            uri = f"{base_uri}?type={mode}&to={encoded_dest}"
            
            if origin:
                encoded_origin = urllib.parse.quote(origin)
                uri += f"&from={encoded_origin}"
        else:
            # 通用geo URI
            uri = f"geo:0,0?q={urllib.parse.quote(destination)}"
        
        return uri
    
    def _build_search_uri(self, app: NavigationApp, keyword: str) -> str:
        """
        构建搜索URI
        
        Args:
            app: 导航应用
            keyword: 搜索关键词
            
        Returns:
            str: 搜索URI
        """
        app_info = app.value
        
        # 根据不同应用构建搜索URI
        if app == NavigationApp.AMAP:
            # 高德地图搜索
            encoded_keyword = urllib.parse.quote(keyword)
            uri = f"androidamap://arroundpoi?src_application={app_info['package']}&keywords={encoded_keyword}"
        elif app == NavigationApp.BAIDU_MAP:
            # 百度地图搜索
            encoded_keyword = urllib.parse.quote(keyword)
            uri = f"baidumap://map/search?query={encoded_keyword}"
        elif app == NavigationApp.TENCENT_MAP:
            # 腾讯地图搜索
            encoded_keyword = urllib.parse.quote(keyword)
            uri = f"qqmap://map/search?keyword={encoded_keyword}"
        else:
            # 通用geo URI
            uri = f"geo:0,0?q={urllib.parse.quote(keyword)}"
        
        return uri
    
    def _start_navigation(self, app: NavigationApp, uri: str) -> bool:
        """
        启动导航
        
        Args:
            app: 导航应用
            uri: 导航URI
            
        Returns:
            bool: 启动是否成功
        """
        try:
            if self.android_available and self.use_android_api:
                # 使用Android API启动导航
                import android
                droid = android.Android()
                
                # 创建Intent
                intent_data = {
                    "action": "android.intent.action.VIEW",
                    "data": uri
                }
                
                # 设置包名
                package = app.value.get("package")
                if package:
                    intent_data["package"] = package
                
                droid.startActivity(**intent_data)
                
            else:
                # 使用ADB命令启动导航
                package = app.value.get("package")
                activity = app.value.get("activity", "")
                
                # 方法1: 使用geo URI
                geo_cmd = f'adb shell am start -a android.intent.action.VIEW -d "{uri}"'
                subprocess.run(geo_cmd, shell=True, capture_output=True, text=True)
                
                # 方法2: 如果失败，尝试直接启动应用
                if package and activity:
                    time.sleep(0.5)
                    app_cmd = f"adb shell am start -n {package}/{activity}"
                    subprocess.run(app_cmd, shell=True, capture_output=True, text=True)
            
            logger.debug(f"导航URI: {uri}")
            return True
            
        except Exception as e:
            logger.error(f"✗ 启动导航失败: {e}")
            return False
    
    def navigate_to(self, destination: str, app: Optional[NavigationApp] = None, 
                     origin: Optional[str] = None, mode: str = "driving") -> bool:
        """
        导航到指定目的地
        
        Args:
            destination: 目的地地址或名称
            app: 指定导航应用（可选）
            origin: 起点（可选）
            mode: 导航模式 (driving/walking/transit/riding)
            
        Returns:
            bool: 导航是否成功启动
        """
        target_app = app or self.current_app
        app_info = target_app.value
        
        # 检查应用是否安装
        if not self._is_app_installed(app_info["package"]):
            logger.error(f"✗ 应用未安装: {app_info['name']}")
            return False
        
        try:
            # 解析目的地
            if not destination:
                logger.error("✗ 目的地为空")
                return False
            
            # 提取目的地名称
            destination_name = self._parse_destination(destination)
            
            # 构建导航URI
            uri = self._build_navigation_uri(target_app, destination_name, origin, mode)
            
            # 启动导航
            if self._start_navigation(target_app, uri):
                self.is_navigating = True
                self.current_destination = destination_name
                self.current_route = {"from": origin, "to": destination_name, "mode": mode}
                logger.info(f"✓ 开始导航到: {destination_name} | 应用: {app_info['name']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 导航失败: {e}")
            return False
    
    def _parse_destination(self, destination: str) -> str:
        """
        解析目的地，提取关键信息
        
        Args:
            destination: 原始目的地字符串
            
        Returns:
            str: 解析后的目的地
        """
        # 去除多余的空格和标点
        import re
        cleaned = re.sub(r'[，。、；;]', '', destination.strip())
        
        # 如果包含"导航到"等关键词，去除
        keywords = ["导航到", "去", "到", "前往", "我想去"]
        for keyword in keywords:
            if cleaned.startswith(keyword):
                cleaned = cleaned[len(keyword):].strip()
                break
        
        return cleaned if cleaned else destination
    
    def search_poi(self, keyword: str, app: Optional[NavigationApp] = None) -> bool:
        """
        搜索POI（兴趣点）
        
        Args:
            keyword: 搜索关键词（如"加油站"、"餐厅"等）
            app: 指定导航应用（可选）
            
        Returns:
            bool: 搜索是否成功
        """
        target_app = app or self.current_app
        app_info = target_app.value
        
        # 检查应用是否安装
        if not self._is_app_installed(app_info["package"]):
            logger.error(f"✗ 应用未安装: {app_info['name']}")
            return False
        
        try:
            # 构建搜索URI
            uri = self._build_search_uri(target_app, keyword)
            
            # 启动搜索
            if self._start_navigation(target_app, uri):
                logger.info(f"✓ 已搜索: {keyword} | 应用: {app_info['name']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"✗ 搜索失败: {e}")
            return False
    
    def navigate_home(self) -> bool:
        """
        导航回家
        
        Returns:
            bool: 导航是否成功
        """
        return self.navigate_to("家")
    
    def navigate_to_company(self) -> bool:
        """
        导航去公司
        
        Returns:
            bool: 导航是否成功
        """
        return self.navigate_to("公司")
    
    def cancel_navigation(self) -> bool:
        """
        取消导航
        
        Returns:
            bool: 取消是否成功
        """
        try:
            # 发送退出导航指令
            if self.android_available and self.use_android_api:
                # 使用Android API
                import android
                droid = android.Android()
                droid.sendKeyEvent("KEYCODE_BACK")
            else:
                # 使用ADB命令
                subprocess.run("adb shell input keyevent KEYCODE_BACK", 
                             shell=True, capture_output=True, text=True)
            
            self.is_navigating = False
            logger.info("✓ 导航已取消")
            return True
            
        except Exception as e:
            logger.error(f"✗ 取消导航失败: {e}")
            return False
    
    def get_navigating_status(self) -> Dict[str, Any]:
        """
        获取当前导航状态
        
        Returns:
            dict: 导航状态信息
        """
        return {
            "is_navigating": self.is_navigating,
            "current_destination": self.current_destination,
            "current_route": self.current_route,
            "current_app": self.current_app.value['name']
        }
    
    def search_nearby(self, poi_type: str, app: Optional[NavigationApp] = None) -> bool:
        """
        搜索附近POI
        
        Args:
            poi_type: POI类型（如"加油站"、"停车场"、"餐厅"等）
            app: 指定导航应用（可选）
            
        Returns:
            bool: 搜索是否成功
        """
        # 添加"附近"关键词
        keyword = f"附近{poi_type}"
        return self.search_poi(keyword, app)
    
    def execute_voice_command(self, command: Dict[str, Any]) -> bool:
        """
        执行语音控制指令
        
        Args:
            command: {
                'action': 'navigate_to' | 'search_poi' | 'navigate_home' | 'navigate_to_company' | 'cancel_navigation' | 'search_nearby',
                'params': {
                    'destination': 'xxx' (navigate_to需要),
                    'keyword': 'xxx' (search_poi需要),
                    'poi_type': 'xxx' (search_nearby需要),
                    'origin': 'xxx' (可选),
                    'mode': 'driving' (可选),
                    'app': 'amap' (可选)
                }
            }
            
        Returns:
            bool: 执行是否成功
        """
        action = command.get('action')
        params = command.get('params', {})
        
        # 解析应用参数
        app_name = params.get('app')
        if app_name:
            app_map = {
                'amap': NavigationApp.AMAP,
                'gaode': NavigationApp.AMAP,
                'baidu': NavigationApp.BAIDU_MAP,
                'tencent': NavigationApp.TENCENT_MAP
            }
            app = app_map.get(app_name.lower())
        else:
            app = None
        
        action_map = {
            'navigate_home': lambda: self.navigate_home(),
            'navigate_to_company': lambda: self.navigate_to_company(),
            'cancel_navigation': lambda: self.cancel_navigation(),
        }
        
        if action in action_map:
            return action_map[action]()
        
        elif action == 'navigate_to':
            destination = params.get('destination', '')
            if destination:
                origin = params.get('origin')
                mode = params.get('mode', 'driving')
                return self.navigate_to(destination, app, origin, mode)
            else:
                logger.error("✗ 缺少目的地")
                return False
        
        elif action == 'search_poi':
            keyword = params.get('keyword', '')
            if keyword:
                return self.search_poi(keyword, app)
            else:
                logger.error("✗ 缺少搜索关键词")
                return False
        
        elif action == 'search_nearby':
            poi_type = params.get('poi_type', '')
            if poi_type:
                return self.search_nearby(poi_type, app)
            else:
                logger.error("✗ 缺少POI类型")
                return False
        
        else:
            logger.error(f"✗ 未知的导航指令: {action}")
            return False
    
    def __repr__(self):
        return f"NavigationController(is_navigating={self.is_navigating}, current_app={self.current_app.value['name']}, destination={self.current_destination})"


# 使用示例
if __name__ == "__main__":
    # 初始化导航控制器
    nav = NavigationController(default_app=NavigationApp.AMAP)
    
    # 测试各种指令
    print("\n=== 导航控制测试 ===\n")
    
    # 导航到指定地点
    nav.navigate_to("北京市朝阳区国贸")
    
    # 搜索POI
    nav.search_poi("加油站")
    
    # 搜索附近POI
    nav.search_nearby("停车场")
    
    # 切换到百度地图
    nav.set_default_app("baidu")
    
    # 导航回家
    nav.navigate_home()
    
    # 获取状态
    status = nav.get_navigating_status()
    print(f"\n当前状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
    
    # 测试语音指令
    nav.execute_voice_command({
        'action': 'navigate_to',
        'params': {
            'destination': '天安门广场',
            'app': 'gaode'
        }
    })
    
    # 取消导航
    nav.cancel_navigation()
