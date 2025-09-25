#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机HTTP服务器
提供HTTP API接口来调用打印机功能
"""

import json
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from printer import PrinterInfo


class PrinterHTTPHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        self.printer_info = PrinterInfo()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/printers':
                # 获取打印机列表
                result = self.printer_info.get_printers()
                response = {"result": result, "success": True}
            elif path == '/':
                # 根路径返回API说明
                response = {
                    "message": "打印机服务API",
                    "endpoints": {
                        "/printers": "获取打印机列表 (GET)",
                        "/print/file": "打印文件 (POST) - 参数: file_path, printer_name(可选), paper_size(可选)",
                        "/print/data": "打印数据 (POST) - 参数: data, file_type, printer_name(可选), paper_size(可选)"
                    }
                }
            else:
                response = {"error": "未找到请求的路径", "success": False}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_response = {
                "error": "服务器内部错误",
                "message": str(e),
                "success": False
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if path == '/print/file':
                # 打印文件
                file_path = data.get('file_path')
                printer_name = data.get('printer_name')
                paper_size = data.get('paper_size')
                
                if not file_path:
                    response = {"error": "缺少file_path参数", "success": False}
                else:
                    result = self.printer_info.print_file(file_path, printer_name, paper_size)
                    response = {"result": result, "success": result}
                    
            elif path == '/print/data':
                # 打印数据
                data_content = data.get('data')
                file_type = data.get('file_type')
                printer_name = data.get('printer_name')
                paper_size = data.get('paper_size')
                
                if not data_content or not file_type:
                    response = {"error": "缺少data或file_type参数", "success": False}
                else:
                    result = self.printer_info.print_data(data_content, file_type, printer_name, paper_size)
                    response = {"result": result, "success": result}
            else:
                response = {"error": "未找到请求的路径", "success": False}
                
            self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_response = {
                "error": "服务器内部错误",
                "message": str(e),
                "success": False
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


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


def start_server_for_electron(host='localhost', port=None):
    """为Electron应用启动HTTP服务器，返回实际端口号"""
    try:
        # 如果没有指定端口，自动查找可用端口
        if port is None:
            port = find_available_port()
        
        server = HTTPServer((host, port), PrinterHTTPHandler)
        actual_port = server.server_address[1]
        
        print("打印机HTTP服务已启动")
        print(f"服务地址: http://{host}:{actual_port}")
        print("API端点:")
        print("  GET  /           - API说明")
        print("  GET  /printers   - 获取打印机列表")
        print("  POST /print/file - 打印文件")
        print("  POST /print/data - 打印数据")
        
        # 返回服务器实例和端口号，供Electron使用
        return server, actual_port
        
    except Exception as e:
        print(f"启动服务器失败: {e}")
        raise


def start_server(host='localhost', port=None, output_port=False):
    """启动HTTP服务器（命令行模式）"""
    try:
        server, actual_port = start_server_for_electron(host, port)
        
        if output_port:
            # 输出端口信息到标准输出，供外部程序读取
            print(f"PORT:{actual_port}")
            sys.stdout.flush()
        else:
            print("\n按 Ctrl+C 停止服务")
            
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        server.shutdown()
        print("服务已停止")
    except Exception as e:
        print(f"启动服务器失败: {e}")
        raise


if __name__ == "__main__":
    # 检查命令行参数
    output_port = "--output-port" in sys.argv
    start_server(output_port=output_port)