import os
import sys
import threading
import requests
import webview
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# 将项目根目录添加到sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config import config
from utils.compress_utils import ImageCompressor

import json
import base64

# --- JWT 文件路径 ---
JWT_FILE = os.path.join(os.path.expanduser('~'), '.py_printer_jwt')

# --- 全局变量 ---


class Api:
    def handle_login(self, username, password):
        """处理登录逻辑"""
        try:
            response = requests.post(
                'https://xlyn-api.ynxsl.top/user/login',
                json={'name': username, 'password': password}
            )
            response.raise_for_status()  # 如果请求失败则引发HTTPError
            
            data = response.json()

            # According to the user, the business logic code should be checked.
            if data.get('code') == 0:
                jwt = data.get('data')
                if jwt:
                    # 登录成功，保存JWT到文件
                    with open(JWT_FILE, 'w') as f:
                        json.dump({'token': jwt}, f)
                    print(f"JWT已保存到 {JWT_FILE}")
                    return {'success': True, 'token': jwt}
            
            # Login failed
            return {'success': False, 'message': data.get('message', '无效的响应')}

        except requests.exceptions.RequestException as e:
            print(f"登录请求失败: {e}")
            return {'success': False, 'message': f'网络错误: {e}'}
        except Exception as e:
            print(f"处理登录时发生未知错误: {e}")
            return {'success': False, 'message': '服务器内部错误'}

    def get_user_info(self):
        """验证存储的JWT并返回用户信息"""
        if not os.path.exists(JWT_FILE):
            return {"code": -1, "message": "JWT file not found"}

        try:
            with open(JWT_FILE, 'r') as f:
                data = json.load(f)
                jwt = data.get('token')

            if not jwt:
                return {"code": -1, "message": "JWT token not found in file"}

            response = requests.get(
                'https://xlyn-api.ynxsl.top/user/info',
                headers={'Authorization': f'Bearer {jwt}'}
            )

            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get('code') == 0:
                        print("JWT验证成功")
                        return res_json
                    else:
                        return res_json
                except json.JSONDecodeError:
                    print("JWT验证失败：无法解析响应JSON")
                    return {"code": -1, "message": "Failed to parse response JSON"}
            else:
                print(f"JWT验证失败. 状态码: {response.status_code}")
                return {"code": response.status_code, "message": "JWT validation failed"}

        except Exception as e:
            print(f"JWT验证时发生错误: {e}")
            return {"code": -1, "message": f"An error occurred during JWT validation: {e}"}

    def handle_logout(self):
        """处理登出逻辑"""
        if os.path.exists(JWT_FILE):
            os.remove(JWT_FILE)
            print("JWT文件已删除")
        
        # 重新加载登录页面 (异步跳转，避免 JS 回调失败)
        def _navigate():
            import time
            time.sleep(0.1)
            login_html_path = os.path.join(os.path.dirname(__file__), 'login.html')
            webview.windows[0].load_url(login_html_path)
        
        threading.Thread(target=_navigate).start()

    def get_waybill_pdf(self, order_number):
        try:
            if not os.path.exists(JWT_FILE):
                return {'success': False, 'message': 'JWT file not found'}
            with open(JWT_FILE, 'r') as f:
                data = json.load(f)
                jwt = data.get('token')
            if not jwt:
                return {'success': False, 'message': 'JWT token not found'}
            params = {'orderNumber': order_number}
            resp = requests.get('https://xlyn-api.ynxsl.top/erp/order/waybillPdf', headers={'Authorization': f'Bearer {jwt}'}, params=params)
            try:
                resp.raise_for_status()
            except Exception:
                pass
            try:
                j = resp.json()
            except Exception:
                j = {}
            pdf_path = j.get('pdfPath') or (j.get('data') or {}).get('pdfPath')
            if not pdf_path:
                return {'success': False, 'message': j.get('msg') or '未获取到 pdfPath'}
            return {'success': True, 'pdfPath': pdf_path}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def select_image(self):
        """打开文件选择框选择图片"""
        file_types = ('Image Files (*.jpg;*.jpeg;*.png)', 'All files (*.*)')
        result = webview.windows[0].create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False, file_types=file_types)
        if result:
            return result[0]
        return None

    def compress_image_api(self, image_path, quality=100):
        """压缩图片并返回原图和压缩图的 base64"""
        try:
            compressor = ImageCompressor()
            # 压缩图片
            res = compressor.compress(image_path, quality=quality)
            if not res['success']:
                return res

            # 读取原图和压缩图并转为 base64
            def get_base64(path):
                with open(path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    ext = os.path.splitext(path)[1].lower().replace('.', '')
                    if ext == 'jpg': ext = 'jpeg'
                    return f"data:image/{ext};base64,{encoded_string}"

            res['original_base64'] = get_base64(image_path)
            res['compressed_base64'] = get_base64(res['output_path'])

            # 清理生成的压缩文件（如果需要的话，或者保留它，用户可能想保存）
            # 这里我们保留它，让用户知道存在哪里了

            return res
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def goto_compress_page(self):
        """跳转到压缩对比页面"""
        def _navigate():
            import time
            time.sleep(0.1)
            html_path = os.path.join(os.path.dirname(__file__), 'compress_compare.html')
            webview.windows[0].load_url(html_path)
        
        threading.Thread(target=_navigate).start()

    def goto_home_page(self):
        """返回主页面"""
        def _navigate():
            import time
            time.sleep(0.1)
            html_path = os.path.join(os.path.dirname(__file__), 'success.html')
            webview.windows[0].load_url(html_path)
            
        threading.Thread(target=_navigate).start()
def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    from modules.app_module import app_bp
    from modules.printer_module import printer_bp
    from modules.printing_module import printing_bp
    
    app.register_blueprint(app_bp, url_prefix='/app')
    app.register_blueprint(printer_bp, url_prefix='/printer')
    app.register_blueprint(printing_bp, url_prefix='/printing')
    
    @app.route('/')
    def index():
        return jsonify({"message": "后台服务正在运行"})
    
    return app

def run_flask_app(app, host, port):
    """在单独线程中运行Flask应用"""
    app.run(host=host, port=port, debug=False, use_reloader=False)

def start_gui_app():
    """启动GUI应用"""
    api = Api()
    
    # 验证JWT (优化：只要本地有 JWT 文件，就直接进入主界面)
    if os.path.exists(JWT_FILE):
        target_html = 'success.html'
        window_title = '打印机服务 - 主界面'
    else:
        target_html = 'login.html'
        window_title = '打印机服务 - 登录'

    # 创建并显示webview窗口
    target_html_path = os.path.join(os.path.dirname(__file__), target_html)
    webview.create_window(
        window_title,
        target_html_path,
        js_api=api,
        width=400,
        height=500,
        resizable=False
    )
    webview.start()

def start_server(output_port=False, config_name='default'):
    """启动服务器（命令行模式）"""
    # 这个函数现在只用于非GUI模式
    app = create_app(config_name)
    port = 6789
    print(f"后台服务已启动，访问 http://127.0.0.1:{port}")
    if output_port:
        print(f"PORT:{port}")
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == "__main__":
    # 同时启动后台服务和GUI
    config_name = 'development' if '--debug' in sys.argv else 'default'
    server_thread = threading.Thread(target=start_server, args=(False, config_name), daemon=True)
    server_thread.start()
    start_gui_app()