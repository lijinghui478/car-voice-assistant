@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 车载语音助手 - Windows一键打包脚本

echo ==========================================
echo   车载语音助手 - 一键打包工具 (Windows)
echo ==========================================
echo.

REM 检查Python
echo [1/7] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python未安装或未添加到PATH
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo ✓ Python版本: !PYTHON_VER!

REM 检查pip
echo.
echo [2/7] 检查pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ✗ pip未安装
    pause
    exit /b 1
)
echo ✓ pip已安装

REM 创建虚拟环境
echo.
echo [3/7] 创建Python虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo ✓ 虚拟环境创建完成
) else (
    echo ✓ 虚拟环境已存在
)

REM 激活虚拟环境
echo.
echo [4/7] 激活虚拟环境...
call venv\Scripts\activate.bat
echo ✓ 虚拟环境已激活

REM 安装依赖
echo.
echo [5/7] 安装Python依赖...
if exist "requirements.txt" (
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo ✓ 依赖安装完成
) else (
    echo ✗ requirements.txt不存在
    pause
    exit /b 1
)

REM 安装Buildozer
echo.
echo [6/7] 安装Buildozer...
buildozer --version >nul 2>&1
if errorlevel 1 (
    echo 正在安装Buildozer...
    pip install buildozer -q
    echo ✓ Buildozer安装完成
) else (
    for /f "tokens=*" %%i in ('buildozer --version') do set BUILD_VER=%%i
    echo ✓ Buildozer已安装: !BUILD_VER!
)

REM 准备项目文件
echo.
echo ==========================================
echo   准备项目文件
echo ==========================================

REM 创建目录
if not exist "src" mkdir src
if not exist "assets" mkdir assets
if not exist "bin" mkdir bin
if not exist "libs" mkdir libs

REM 复制V2版本的模块
echo.
echo 复制核心模块到src目录...
set V2_FILES=CarVoiceAssistant_KWS_V2.py MusicController_V2.py ACController_V2.py Camera360Controller_V2.py NavigationController_V2.py AudioCaptureHandler.py logger_config.py ConfigManager.py MainApp.py

for %%f in (%V2_FILES%) do (
    if exist "%%f" (
        copy /Y "%%f" "src\" >nul
        echo ✓ 复制: %%f
    ) else (
        echo ✗ 文件不存在: %%f
        pause
        exit /b 1
    )
)

REM 创建main.py
echo.
echo 创建main.py入口文件...
(
echo #!/usr/bin/env python3
echo # -*- coding: utf-8 -*-
echo """
echo 车载语音助手 - 主入口
echo """
echo.
echo import sys
echo import os
echo.
echo # 添加路径
echo sys.path.insert^(0, os.path.dirname^(__file__^)^)
echo.
echo # 导入主应用
echo from MainApp import CarVoiceAssistantApp
echo.
echo def main^(^):
echo     """主函数"""
echo     try:
echo         # 创建应用实例
echo         app = CarVoiceAssistantApp^(^)
echo.
echo         # 启动应用
echo         app.start^(^)
echo.
echo     except KeyboardInterrupt:
echo         print^("\n应用已停止"^)
echo     except Exception as e:
echo         print^(f"应用启动失败: {e}"^)
echo         import traceback
echo         traceback.print_exc^(^)
echo         sys.exit^(1^)
echo.
echo if __name__ == "__main__":
echo     main^(^)
) > src\main.py
echo ✓ main.py创建完成

REM 复制配置文件
echo.
echo 复制配置文件到assets目录...
if exist "config_example.json" (
    copy /Y config_example.json assets\ >nul
    echo ✓ 配置文件已复制
)

REM 创建buildozer.spec
echo.
echo 创建buildozer.spec配置文件...
(
echo [app]
echo.
echo # 应用信息
echo title = 车机智能语音助手
echo package.name = carvoiceassistant
echo package.domain = org.carvoice
echo source.dir = src
echo.
echo # 源文件
echo source.include_exts = py,png,jpg,kv,atlas,json,xml
echo.
echo # 版本
echo version = 1.0.0
echo.
echo # 依赖
echo requirements = python3,kivy,kivymd,pyjnius,android,pyusb,pyserial,funasr,transformers,torch,numpy,scipy,pyaudio,requests,colorlog
echo.
echo # 全屏
echo fullscreen = True
echo orientation = landscape
echo.
echo # 权限
echo android.permissions = RECORD_AUDIO,ACCESS_FINE_LOCATION,BLUETOOTH,BLUETOOTH_CONNECT,BLUETOOTH_ADMIN,WRITE_SETTINGS,SYSTEM_ALERT_WINDOW,CAMERA
echo.
echo # Android配置
echo android.api = 33
echo android.minapi = 21
echo android.ndk = 25b
echo android.sdk = 33
echo android.archs = arm64-v8a,armeabi-v7a
echo android.entrypoint = org.kivy.android.PythonActivity
echo android.logcat_filters = *:S python:D
echo android.copy_libs = 1
echo.
echo # 其他配置
echo wakelock = True
echo android.enable_androidx = True
echo android.jetifier = True
echo.
echo [buildozer]
echo log_level = 2
echo build_dir = bin
echo cache_dir = .buildozer_cache
echo warnings_as_errors = 0
echo profile = 0
) > buildozer.spec
echo ✓ buildozer.spec创建完成

REM 构建APK
echo.
echo ==========================================
echo   [7/7] 构建APK
echo ==========================================
echo.
echo ⚠ 首次构建可能需要15-30分钟（下载依赖、编译等）
echo 请耐心等待...
echo.

REM 初始化Buildozer
echo 初始化Buildozer...
buildozer init debug

REM 开始构建
echo.
echo 开始构建Debug APK...
buildozer android debug

REM 检查构建结果
echo.
echo ==========================================
echo   构建完成
echo ==========================================

if exist "bin" (
    echo ✓ 构建成功！
    echo.
    echo APK文件:
    dir /b bin\*.apk 2>nul | findstr /i ".apk" >nul
    if errorlevel 1 (
        echo 未找到APK文件
    ) else (
        for %%f in (bin\*.apk) do (
            set APK_NAME=%%f
            set APK_PATH=%%~fF
            echo   ✓ %%~nxf
            echo     路径: !APK_PATH!
        )
    )
) else (
    echo ✗ 构建失败
    echo 请检查：
    echo   1. Java是否已安装
    echo   2. 网络连接是否正常
    echo   3. 磁盘空间是否充足（至少5GB）
)

echo.
echo ==========================================
echo   安装说明
echo ==========================================
echo.
echo 1. 将APK文件传输到车机（通过U盘或网络）
echo 2. 在车机上点击APK文件进行安装
echo 3. 授予应用所有权限（特别是录音和定位权限）
echo 4. 复制config_example.json到应用目录
echo 5. 编辑config.json，填写扣子Bot Token
echo 6. 启动应用并测试
echo.

echo ✓ 打包完成！
echo.
pause
