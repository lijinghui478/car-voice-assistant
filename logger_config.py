"""
车载语音助手 - 日志配置模块
提供统一的日志管理功能
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

def setup_logger(config=None):
    """
    配置日志系统
    
    Args:
        config: 日志配置字典，如未提供则使用默认配置
    """
    # 默认配置
    default_config = {
        "level": "INFO",
        "log_file": "logs/voice_assistant.log",
        "max_file_size": 10485760,  # 10MB
        "backup_count": 5,
        "colored_console": True,
        "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S"
    }
    
    # 合并配置
    if config:
        default_config.update(config)
    
    # 创建日志目录
    log_file = default_config.get("log_file", "logs/voice_assistant.log")
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, default_config.get("level", "INFO")))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        default_config.get("format"),
        datefmt=default_config.get("date_format")
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # 如果支持彩色输出，使用彩色格式
    if default_config.get("colored_console", True):
        try:
            import colorlog
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s[%(asctime)s] [%(levelname)s] [%(name)s]%(reset)s %(message)s",
                datefmt=default_config.get("date_format"),
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
        except ImportError:
            pass  # 回退到普通格式
    
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        try:
            # 按大小轮转的文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=default_config.get("max_file_size", 10485760),
                backupCount=default_config.get("backup_count", 5),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            print(f"✓ 日志文件: {log_file}")
            
        except Exception as e:
            print(f"⚠ 无法创建日志文件处理器: {e}")
    
    # 设置第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    print(f"✓ 日志系统已配置 | 级别: {default_config.get('level')}")
    
    return root_logger


def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


# 模块加载时自动配置
setup_logger()
