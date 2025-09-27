#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用模块
提供应用控制相关的API接口
"""

import os
import threading
import time
from flask import Blueprint, jsonify, current_app


# 创建蓝图
app_bp = Blueprint('app', __name__)


@app_bp.route('/info')
def get_app_info():
    """获取应用信息"""
    try:
        return jsonify({
            "name": current_app.config.get('APP_NAME', '打印机服务API'),
            "version": current_app.config.get('APP_VERSION', '2.0.0'),
            "status": "running",
            "host": current_app.config.get('HOST', 'localhost'),
            "port": current_app.config.get('PORT', 6789),
            "debug": current_app.config.get('DEBUG', False),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": "获取应用信息失败",
            "message": str(e),
            "success": False
        }), 500


@app_bp.route('/shutdown')
def shutdown_server():
    """关闭服务器"""
    try:
        def shutdown_task():
            """在单独线程中执行关闭任务"""
            time.sleep(0.1)  # 给响应一点时间发送
            os._exit(0)  # 强制退出应用
        
        # 在单独的线程中关闭服务器，避免阻塞当前请求
        threading.Thread(target=shutdown_task, daemon=True).start()
        
        return jsonify({
            "message": "服务器正在关闭...",
            "success": True
        })
        
    except Exception as e:
        return jsonify({
            "error": "关闭服务器失败",
            "message": str(e),
            "success": False
        }), 500


@app_bp.route('/health')
def health_check():
    """健康检查接口"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": "健康检查失败",
            "message": str(e),
            "success": False
        }), 500


@app_bp.route('/status')
def get_server_status():
    """获取服务器状态"""
    try:
        import psutil
        import platform
        
        # 获取系统信息
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        
        # 获取进程信息
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_usage": process.memory_info().rss / 1024 / 1024,  # MB
            "cpu_percent": process.cpu_percent(),
            "create_time": process.create_time()
        }
        
        return jsonify({
            "system": system_info,
            "process": process_info,
            "success": True
        })
        
    except ImportError:
        # 如果没有安装psutil，返回基本信息
        return jsonify({
            "message": "服务器运行正常",
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": "获取服务器状态失败",
            "message": str(e),
            "success": False
        }), 500