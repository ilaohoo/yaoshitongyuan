#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理 - 从环境变量读取（支持 GitHub Secrets 和 .env）
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用）
load_dotenv()


class Settings:
    """配置类 - 所有配置从环境变量读取"""
    
    # ===== DeepSeek API =====
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL = os.getenv(
        "DEEPSEEK_API_URL", 
        "https://api.deepseek.com/v1/chat/completions"
    )
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # ===== PushPlus =====
    PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")
    PUSHPLUS_URL = os.getenv(
        "PUSHPLUS_URL",
        "http://www.pushplus.plus/send"
    )
    
    # ===== 推送时间 =====
    PUSH_TIME = os.getenv("PUSH_TIME", "12:00")
    
    # ===== 存储路径 =====
    BASE_DIR = Path(__file__).parent
    ARTICLES_DIR = BASE_DIR / "generated_articles"
    DATA_FILE = ARTICLES_DIR / "article_data.json"
    
    @classmethod
    def is_configured(cls):
        """检查是否已配置必要的 API Key"""
        return bool(
            cls.DEEPSEEK_API_KEY and 
            cls.DEEPSEEK_API_KEY != "sk-你的API密钥" and
            cls.PUSHPLUS_TOKEN and 
            cls.PUSHPLUS_TOKEN != "你的PushPlus Token"
        )
    
    @classmethod
    def get_config_info(cls):
        """获取配置状态（用于调试，不显示敏感信息）"""
        return {
            "DeepSeek API": "✅ 已配置" if cls.DEEPSEEK_API_KEY else "❌ 未配置",
            "PushPlus": "✅ 已配置" if cls.PUSHPLUS_TOKEN else "❌ 未配置",
            "推送时间": cls.PUSH_TIME,
            "存储目录": str(cls.ARTICLES_DIR),
        }


# 创建全局配置实例
CONFIG = Settings()
