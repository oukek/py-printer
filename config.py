#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用配置文件
"""

import os


class Config:
    """基础配置类"""
    
    # 服务器配置
    HOST = os.environ.get('HOST', 'localhost')
    PORT = int(os.environ.get('PORT', 6789))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # API配置
    JSON_AS_ASCII = False  # 支持中文JSON响应
    JSON_SORT_KEYS = False
    
    # CORS配置
    CORS_ORIGINS = "*"
    
    # 应用信息
    APP_NAME = "打印机服务API"
    APP_VERSION = "2.0.0"


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}