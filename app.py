#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask打印机服务应用
模块化架构的HTTP API服务器
"""

import os
import sys
import socket
import threading
import time
from flask import Flask, jsonify
from flask_cors import CORS
from config import config


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 启用CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # 注册蓝图
    from modules.app_module import app_bp
    from modules.printer_module import printer_bp
    
    app.register_blueprint(app_bp, url_prefix='/app')
    app.register_blueprint(printer_bp, url_prefix='/printer')
    
    # 根路径API说明
    @app.route('/')
    def index():
        return jsonify({
            "message": app.config['APP_NAME'],
            "version": app.config['APP_VERSION'],
            "modules": {
                "app": {
                    "prefix": "/app",
                    "description": "应用控制模块",
                    "endpoints": {
                        "/app/info": "获取应用信息 (GET)",
                        "/app/shutdown": "关闭服务器 (GET)"
                    }
                },
                "printer": {
                    "prefix": "/printer",
                    "description": "打印机模块",
                    "endpoints": {
                        "/printer/list": "获取打印机列表 (GET)",
                        "/printer/print/file": "打印文件 (POST)",
                        "/printer/print/data": "打印数据 (POST)"
                    }
                }
            }
        })
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "未找到请求的路径",
            "success": False
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "服务器内部错误",
            "message": str(error),
            "success": False
        }), 500
    
    return app


def find_available_port(start_port=6789, max_attempts=100):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"无法在 {start_port}-{start_port + max_attempts - 1} 范围内找到可用端口")


# 全局变量保存应用实例
app_instance = None
server_thread = None


def start_server_for_electron(host='localhost', port=None, config_name='default'):
    """为Electron应用启动Flask服务器，返回实际端口号"""
    global app_instance
    
    try:
        # 如果没有指定端口，自动查找可用端口
        if port is None:
            port = find_available_port()
        
        app_instance = create_app(config_name)
        
        print("打印机Flask服务已启动")
        print(f"服务地址: http://{host}:{port}")
        print("API模块:")
        print("  应用模块: /app/*")
        print("  打印模块: /printer/*")
        
        # 返回应用实例和端口号，供Electron使用
        return app_instance, port
        
    except Exception as e:
        print(f"启动服务器失败: {e}")
        raise


def start_server(host='localhost', port=None, output_port=False, config_name='default'):
    """启动Flask服务器（命令行模式）"""
    global app_instance, server_thread
    
    try:
        app_instance, actual_port = start_server_for_electron(host, port, config_name)
        
        if output_port:
            # 输出端口信息到标准输出，供外部程序读取
            print(f"PORT:{actual_port}")
            sys.stdout.flush()
        else:
            print("\n按 Ctrl+C 停止服务")
        
        # 在单独线程中运行Flask应用
        def run_app():
            app_instance.run(host=host, port=actual_port, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_app, daemon=True)
        server_thread.start()
        
        # 主线程等待
        try:
            while server_thread.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n正在停止服务...")
            print("服务已停止")
            
    except Exception as e:
        print(f"启动服务器失败: {e}")
        raise


def shutdown_server():
    """关闭服务器"""
    import os
    os._exit(0)


if __name__ == "__main__":
    # 检查命令行参数
    output_port = "--output-port" in sys.argv
    config_name = 'development' if '--debug' in sys.argv else 'default'
    start_server(output_port=output_port, config_name=config_name)