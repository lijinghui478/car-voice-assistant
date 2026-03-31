#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
支持配置加密存储（P0安全修复）
"""

import json
import os
import hashlib
import base64
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path="config.json"):
        """初始化配置管理器"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # 生成或加载加密密钥（P0安全修复）
        self.key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_encryption_key(self):
        """获取或创建加密密钥"""
        key_file = ".encryption_key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            logger.info("✓ 加密密钥已创建")
            return key
    
    def encrypt_token(self, token: str) -> str:
        """加密Token（P0安全修复）"""
        if not token:
            return ""
        encrypted = self.cipher.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """解密Token（P0安全修复）"""
        if not encrypted_token:
            return ""
        try:
            encrypted = base64.b64decode(encrypted_token.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Token解密失败: {e}")
            return ""
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"✓ 配置文件加载成功: {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"✗ 配置文件加载失败: {e}")
                return self._get_default_config()
        else:
            logger.warning(f"⚠️ 配置文件不存在，使用默认配置: {self.config_path}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "voice": {
                "wake_word": "小云小云",
                "wake_threshold": 0.85,
                "wakeup_prompt_enabled": True
            },
            "coze_bot": {
                "enabled": True,
                "bot_token": "",  # 将自动加密
                "bot_id": "",
                "api_url": "https://api.coze.cn/open_api/v2/chat",
                "timeout": 10,
                "failure_threshold": 3,
                "recovery_timeout": 30
            },
            "apps": {
                "default_music": "qq",
                "default_navigation": "amap"
            },
            "vehicle_settings": {
                "protocol_box": {
                    "enabled": True,
                    "serial_port": "/dev/ttyUSB0",
                    "baud_rate": 115200
                }
            }
        }
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ 配置文件保存成功: {self.config_path}")
        except Exception as e:
            logger.error(f"✗ 配置文件保存失败: {e}")
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def set_coze_config(self, token: str, bot_id: str):
        """设置扣子配置（自动加密Token，P0安全修复）"""
        if not self.config.get("coze_bot"):
            self.config["coze_bot"] = {}
        
        # 自动加密Token
        encrypted_token = self.encrypt_token(token)
        self.config["coze_bot"]["bot_token"] = encrypted_token
        self.config["coze_bot"]["bot_id"] = bot_id
        self.save()
        logger.info("✓ 扣子配置已保存（Token已加密）")
    
    def get_coze_token(self) -> str:
        """获取扣子Token（自动解密，P0安全修复）"""
        encrypted_token = self.config.get("coze_bot", {}).get("bot_token", "")
        if encrypted_token:
            try:
                return self.decrypt_token(encrypted_token)
            except Exception as e:
                logger.error(f"Token解密失败: {e}")
                return ""
        return ""
    
    def get_coze_bot_id(self) -> str:
        """获取扣子Bot ID"""
        return self.config.get("coze_bot", {}).get("bot_id", "")
    
    def is_coze_enabled(self) -> bool:
        """检查扣子是否启用"""
        return self.config.get("coze_bot", {}).get("enabled", False)
    
    def get_wake_word(self) -> str:
        """获取唤醒词"""
        return self.config.get("voice", {}).get("wake_word", "小云小云")
    
    def get_wake_threshold(self) -> float:
        """获取唤醒阈值"""
        return self.config.get("voice", {}).get("wake_threshold", 0.85)
    
    def is_wakeup_prompt_enabled(self) -> bool:
        """是否启用唤醒提示音"""
        return self.config.get("voice", {}).get("wakeup_prompt_enabled", True)
    
    def get_default_music_app(self) -> str:
        """获取默认音乐应用"""
        return self.config.get("apps", {}).get("default_music", "qq")
    
    def get_default_navigation_app(self) -> str:
        """获取默认导航应用"""
        return self.config.get("apps", {}).get("default_navigation", "amap")
    
    def get_protocol_box_config(self) -> dict:
        """获取协议盒子配置"""
        return self.config.get("vehicle_settings", {}).get("protocol_box", {})
    
    def __repr__(self):
        return f"ConfigManager(config_path='{self.config_path}')"
