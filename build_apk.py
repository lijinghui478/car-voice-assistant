#!/usr/bin/env python3
"""
车载语音助手 - APK编译脚本
使用Buildozer自动构建Android APK
"""

import os
import sys
import subprocess
import shutil
import json

class APKBuilder:
    """APK构建器"""
    
    def __init__(self, project_dir="."):
        self.project_dir = project_dir
        self.buildozer_spec = "buildozer.spec"
        self.python_files = [
            "CarVoiceAssistant_KWS_V2.py",
            "MusicController_V2.py",
            "ACController_V2.py",
            "Camera360Controller_V2.py",
            "NavigationController_V2.py",
            "AudioCaptureHandler.py",
            "logger_config.py",
            "ConfigManager.py",
            "MainApp.py"
        ]
        self.config_files = [
            "config_example.json",
            "AndroidManifest.xml"
        ]
        self.assets = []
    
    def prepare_project(self):
        """准备项目文件"""
        print("="*80)
        print("准备项目文件")
        print("="*80)
        
        # 创建必要的目录
        dirs_to_create = [
            "assets",
            "libs",
            "res",
            "src",
            "bin"
        ]
        
        for dir_name in dirs_to_create:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"✓ 创建目录: {dir_name}")
        
        # 复制Python文件到src目录
        src_dir = os.path.join(self.project_dir, "src")
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)
        
        for py_file in self.python_files:
            if os.path.exists(py_file):
                shutil.copy(py_file, os.path.join(src_dir, py_file))
                print(f"✓ 复制文件: {py_file}")
            else:
                print(f"✗ 文件不存在: {py_file}")
        
        # 复制配置文件到assets目录
        assets_dir = os.path.join(self.project_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        
        for config_file in self.config_files:
            if os.path.exists(config_file):
                shutil.copy(config_file, os.path.join(assets_dir, config_file))
                print(f"✓ 复制配置: {config_file}")
        
        # 创建main.py（入口文件）
        main_py = os.path.join(src_dir, "main.py")
        self.create_main_py(main_py)
        
        print("\n✓ 项目文件准备完成")
    
    def create_main_py(self, output_path):
        """创建main.py入口文件"""
        content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载语音助手 - 主入口
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入主应用
from MainApp import CarVoiceAssistantApp

def main():
    """主函数"""
    try:
        # 创建应用实例
        app = CarVoiceAssistantApp()
        
        # 启动应用
        app.start()
        
    except KeyboardInterrupt:
        print("\\n应用已停止")
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 创建入口文件: {output_path}")
    
    def create_buildozer_spec(self):
        """创建buildozer.spec配置文件"""
        spec_content = '''[app]

# (str) Title of your application
title = 车机智能语音助手

# (str) Package name
package.name = carvoiceassistant

# (str) Package domain (needed for android/ios packaging)
package.domain = org.carvoice

# (str) Source code where the main.py live
source.dir = src

# (list) Source files to include (let empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,json,xml

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy,kivymd,pyjnius,android,pyusb,pyserial,funasr,transformers,torch,numpy,scipy,pyaudio,requests

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = True

# (list) Permissions
android.permissions = RECORD_AUDIO,ACCESS_FINE_LOCATION,BLUETOOTH,BLUETOOTH_CONNECT,BLUETOOTH_ADMIN,WRITE_SETTINGS,SYSTEM_ALERT_WINDOW,CAMERA

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
android.sdk_path =

# (str) Android entry point (default: "org.kivy.android.PythonActivity")
android.entrypoint = org.kivy.android.PythonActivity

# (list) Android whitelist (regex)
android.whitelist =

# (str) Android logcat filters to use when androidlogcat is enabled
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) Android archs
android.archs = arm64-v8a,armeabi-v7a

# (bool) Indicate whether the screen should stay on
wakelock = True

# (list) List of service to declare
services = CarVoiceAssistantService:src/CarVoiceAssistantService.py

# (list) List of meta
meta =

# (list) List of aars to add
android.add_aars =

# (list) Gradle dependencies to add (can be file or a Maven artifact)
android.gradle_dependencies =

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable Jetifier support
android.jetifier = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build output directory
build_dir = bin

# (str) Path to build cache directory
cache_dir = .buildozer_cache

# (bool) Enable Buildozer warnings as errors
warnings_as_errors = 0

# (str) Enable profiling
profile = 0

# (str) Android compilation archs
android.accepted_android_abis = arm64-v8a,armeabi-v7a

# (str) NDK version
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity
'''
        
        with open(self.buildozer_spec, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✓ 创建Buildozer配置: {self.buildozer_spec}")
    
    def check_dependencies(self):
        """检查依赖环境"""
        print("\n" + "="*80)
        print("检查依赖环境")
        print("="*80)
        
        # 检查Python
        python_version = sys.version_info
        print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version.major < 3 or python_version.minor < 8:
            print("✗ Python版本过低，需要3.8+")
            return False
        
        # 检查Buildozer
        try:
            result = subprocess.run(['buildozer', '--version'], capture_output=True, text=True)
            print(f"✓ Buildozer已安装: {result.stdout.strip()}")
        except:
            print("⚠ Buildozer未安装，正在安装...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'buildozer'], check=True)
            print("✓ Buildozer安装完成")
        
        # 检查Java
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            java_version = result.stderr.splitlines()[0].split('"')[1]
            print(f"✓ Java版本: {java_version}")
        except:
            print("⚠ Java未安装或未添加到PATH")
        
        # 检查Android SDK
        android_sdk = os.environ.get('ANDROID_SDK_ROOT')
        if android_sdk:
            print(f"✓ Android SDK: {android_sdk}")
        else:
            print("⚠ ANDROID_SDK_ROOT未设置，Buildozer将自动下载")
        
        return True
    
    def build_apk(self, mode="debug"):
        """
        构建APK
        
        Args:
            mode: debug/release
        """
        print("\n" + "="*80)
        print(f"构建APK ({mode}模式)")
        print("="*80)
        
        # 准备项目
        self.prepare_project()
        
        # 创建Buildozer配置
        self.create_buildozer_spec()
        
        # 检查依赖
        if not self.check_dependencies():
            print("✗ 依赖检查失败")
            return False
        
        # 构建APK
        print(f"\n开始构建APK (这可能需要几分钟时间)...")
        print("="*80)
        
        try:
            if mode == "debug":
                cmd = ["buildozer", "android", "debug"]
            else:
                cmd = ["buildozer", "android", "release"]
            
            subprocess.run(cmd, check=True)
            
            print("\n" + "="*80)
            print("✓ APK构建完成")
            print("="*80)
            
            # 显示APK文件位置
            apk_dir = os.path.join(self.project_dir, "bin")
            if os.path.exists(apk_dir):
                apk_files = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]
                if apk_files:
                    print(f"\nAPK文件位置:")
                    for apk in apk_files:
                        apk_path = os.path.join(apk_dir, apk)
                        size_mb = os.path.getsize(apk_path) / (1024 * 1024)
                        print(f"  - {apk} ({size_mb:.2f} MB)")
                        print(f"    路径: {apk_path}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ 构建失败: {e}")
            return False
        except KeyboardInterrupt:
            print("\n构建已取消")
            return False
    
    def clean(self):
        """清理构建文件"""
        print("清理构建文件...")
        
        dirs_to_clean = ["bin", ".buildozer_cache", "__pycache__"]
        
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"✓ 清理: {dir_name}")
        
        print("✓ 清理完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='车载语音助手 - APK构建工具')
    parser.add_argument('--mode', choices=['debug', 'release'], default='debug',
                       help='构建模式 (默认: debug)')
    parser.add_argument('--clean', action='store_true',
                       help='清理构建文件')
    
    args = parser.parse_args()
    
    builder = APKBuilder()
    
    if args.clean:
        builder.clean()
        return
    
    # 构建APK
    success = builder.build_apk(mode=args.mode)
    
    if success:
        print("\n" + "="*80)
        print("🎉 构建成功！")
        print("="*80)
        print("\n下一步:")
        print("1. 将APK文件传输到车机")
        print("2. 在车机上安装APK")
        print("3. 授予应用所需权限")
        print("4. 配置扣子Bot Token")
        print("5. 启动应用并测试")
    else:
        print("\n" + "="*80)
        print("❌ 构建失败")
        print("="*80)
        print("\n请检查:")
        print("1. Python版本是否 >= 3.8")
        print("2. Java是否已安装")
        print("3. 网络连接是否正常（需要下载依赖）")
        print("4. 磁盘空间是否充足（至少5GB）")


if __name__ == "__main__":
    main()
