#!/bin/bash

# 车载语音助手 - 一键打包脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  车载语音助手 - 一键打包工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${GREEN}✓${NC} 检测到Linux系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✓${NC} 检测到macOS系统"
else
    echo -e "${RED}✗${NC} 不支持的操作系统: $OSTYPE"
    exit 1
fi

# 检查Python
echo ""
echo "检查Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python版本: $PYTHON_VER"
else
    echo -e "${RED}✗${NC} Python3未安装"
    exit 1
fi

# 检查pip
echo ""
echo "检查pip..."
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3已安装"
else
    echo -e "${YELLOW}⚠${NC} pip3未安装，尝试安装..."
    sudo apt-get install python3-pip -y
fi

# 创建虚拟环境
echo ""
echo "=========================================="
echo "  步骤 1: 创建虚拟环境"
echo "=========================================="

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} 虚拟环境创建完成"
else
    echo -e "${YELLOW}⚠${NC} 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} 虚拟环境已激活"

# 安装依赖
echo ""
echo "=========================================="
echo "  步骤 2: 安装Python依赖"
echo "=========================================="

if [ -f "requirements.txt" ]; then
    echo "安装依赖包..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "${RED}✗${NC} requirements.txt不存在"
    exit 1
fi

# 安装Buildozer
echo ""
echo "=========================================="
echo "  步骤 3: 安装Buildozer"
echo "=========================================="

echo "检查Buildozer..."
if ! command -v buildozer &> /dev/null; then
    echo "安装Buildozer..."
    pip install buildozer -q
    echo -e "${GREEN}✓${NC} Buildozer安装完成"
else
    echo -e "${YELLOW}⚠${NC} Buildozer已安装"
fi

# 检查Java
echo ""
echo "=========================================="
echo "  步骤 4: 检查Java环境"
echo "=========================================="

if command -v java &> /dev/null; then
    JAVA_VER=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
    echo -e "${GREEN}✓${NC} Java版本: $JAVA_VER"
else
    echo -e "${YELLOW}⚠${NC} Java未安装或未添加到PATH"
    echo "  安装Java (OpenJDK 11)..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install openjdk-11-jdk -y
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install openjdk@11
    fi
fi

# 准备项目文件
echo ""
echo "=========================================="
echo "  步骤 5: 准备项目文件"
echo "=========================================="

# 创建必要目录
mkdir -p src assets bin libs

# 复制V2版本的模块
echo "复制核心模块..."
V2_FILES=(
    "CarVoiceAssistant_KWS_V2.py"
    "MusicController_V2.py"
    "ACController_V2.py"
    "Camera360Controller_V2.py"
    "NavigationController_V2.py"
    "AudioCaptureHandler.py"
    "logger_config.py"
    "ConfigManager.py"
    "MainApp.py"
)

for file in "${V2_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "src/"
        echo -e "${GREEN}✓${NC} 复制: $file"
    else
        echo -e "${RED}✗${NC} 文件不存在: $file"
        exit 1
    fi
done

# 创建main.py入口文件
echo "创建main.py..."
cat > src/main.py << 'EOF'
#!/usr/bin/env python3
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
        print("\n应用已停止")
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
echo -e "${GREEN}✓${NC} main.py创建完成"

# 复制配置文件
echo "复制配置文件..."
if [ -f "config_example.json" ]; then
    cp config_example.json assets/
    echo -e "${GREEN}✓${NC} 复制配置文件"
fi

# 创建buildozer.spec
echo ""
echo "=========================================="
echo "  步骤 6: 创建Buildozer配置"
echo "=========================================="

cat > buildozer.spec << 'EOF'
[app]

# 应用信息
title = 车机智能语音助手
package.name = carvoiceassistant
package.domain = org.carvoice
source.dir = src

# 源文件
source.include_exts = py,png,jpg,kv,atlas,json,xml

# 版本
version = 1.0.0

# 依赖
requirements = python3,kivy,kivymd,pyjnius,android,pyusb,pyserial,funasr,transformers,torch,numpy,scipy,pyaudio,requests,colorlog

# 全屏
fullscreen = True
orientation = landscape

# 权限
android.permissions = RECORD_AUDIO,ACCESS_FINE_LOCATION,BLUETOOTH,BLUETOOTH_CONNECT,BLUETOOTH_ADMIN,WRITE_SETTINGS,SYSTEM_ALERT_WINDOW,CAMERA

# Android配置
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a,armeabi-v7a
android.entrypoint = org.kivy.android.PythonActivity
android.logcat_filters = *:S python:D
android.copy_libs = 1

# 其他配置
wakelock = True
android.enable_androidx = True
android.jetifier = True

[buildozer]
log_level = 2
build_dir = bin
cache_dir = .buildozer_cache
warnings_as_errors = 0
profile = 0
EOF

echo -e "${GREEN}✓${NC} buildozer.spec创建完成"

# 构建APK
echo ""
echo "=========================================="
echo "  步骤 7: 构建APK"
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠${NC} 首次构建可能需要15-30分钟（下载依赖、编译等）"
echo "请耐心等待..."
echo ""

# 初始化Buildozer
echo "初始化Buildozer..."
buildozer init debug

# 开始构建
echo ""
echo "开始构建Debug APK..."
buildozer android debug

# 检查构建结果
echo ""
echo "=========================================="
echo "  构建完成"
echo "=========================================="

if [ -d "bin" ]; then
    echo -e "${GREEN}✓${NC} 构建成功！"
    echo ""
    echo "APK文件:"
    find bin -name "*.apk" -type f | while read apk; do
        size=$(du -h "$apk" | cut -f1)
        echo -e "  ${GREEN}✓${NC} $(basename $apk) (${size})"
        echo "    路径: $(realpath $apk)"
    done
else
    echo -e "${RED}✗${NC} 构建失败"
    exit 1
fi

# 安装说明
echo ""
echo "=========================================="
echo "  安装说明"
echo "=========================================="
echo ""
echo "1. 将APK文件传输到车机（通过U盘或网络）"
echo "2. 在车机上点击APK文件进行安装"
echo "3. 授予应用所有权限（特别是录音和定位权限）"
echo "4. 复制config_example.json到应用目录"
echo "5. 编辑config.json，填写扣子Bot Token"
echo "6. 启动应用并测试"
echo ""

echo -e "${GREEN}✓${NC} 打包完成！"
