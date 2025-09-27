#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机模块
提供打印机相关的API接口
"""

from flask import Blueprint, jsonify, request
from utils.printer import PrinterInfo


# 创建蓝图
printer_bp = Blueprint('printer', __name__)

# 创建打印机信息实例
printer_info = PrinterInfo()


@printer_bp.route('/list')
def get_printers():
    """获取打印机列表"""
    try:
        result = printer_info.get_printers()
        return jsonify({
            "result": result,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": "获取打印机列表失败",
            "message": str(e),
            "success": False
        }), 500


@printer_bp.route('/print/file', methods=['POST'])
def print_file():
    """打印文件"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        file_path = data.get('file_path')
        printer_name = data.get('printer_name')
        paper_size = data.get('paper_size')
        
        if not file_path:
            return jsonify({
                "error": "缺少file_path参数",
                "success": False
            }), 400
        
        result = printer_info.print_file(file_path, printer_name, paper_size)
        
        return jsonify({
            "result": result,
            "success": result,
            "message": "打印任务已提交" if result else "打印任务提交失败"
        })
        
    except Exception as e:
        return jsonify({
            "error": "打印文件失败",
            "message": str(e),
            "success": False
        }), 500


@printer_bp.route('/print/data', methods=['POST'])
def print_data():
    """打印数据"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        data_content = data.get('data')
        file_type = data.get('file_type')
        printer_name = data.get('printer_name')
        paper_size = data.get('paper_size')
        
        if not data_content or not file_type:
            return jsonify({
                "error": "缺少data或file_type参数",
                "success": False
            }), 400
        
        result = printer_info.print_data(data_content, file_type, printer_name, paper_size)
        
        return jsonify({
            "result": result,
            "success": result,
            "message": "打印任务已提交" if result else "打印任务提交失败"
        })
        
    except Exception as e:
        return jsonify({
            "error": "打印数据失败",
            "message": str(e),
            "success": False
        }), 500


@printer_bp.route('/default')
def get_default_printer():
    """获取默认打印机"""
    try:
        # 这里可以扩展PrinterInfo类来获取默认打印机
        printers = printer_info.get_printers()
        
        # 简单实现：返回第一个打印机作为默认打印机
        default_printer = printers[0] if printers else None
        
        return jsonify({
            "result": default_printer,
            "success": True,
            "message": "获取默认打印机成功" if default_printer else "未找到可用打印机"
        })
        
    except Exception as e:
        return jsonify({
            "error": "获取默认打印机失败",
            "message": str(e),
            "success": False
        }), 500


@printer_bp.route('/status/<printer_name>')
def get_printer_status(printer_name):
    """获取指定打印机状态"""
    try:
        # 这里可以扩展PrinterInfo类来获取打印机状态
        printers = printer_info.get_printers()
        
        # 查找指定打印机
        target_printer = None
        for printer in printers:
            if printer.get('name') == printer_name:
                target_printer = printer
                break
        
        if not target_printer:
            return jsonify({
                "error": f"未找到打印机: {printer_name}",
                "success": False
            }), 404
        
        return jsonify({
            "result": target_printer,
            "success": True,
            "message": f"获取打印机 {printer_name} 状态成功"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"获取打印机 {printer_name} 状态失败",
            "message": str(e),
            "success": False
        }), 500


@printer_bp.route('/test', methods=['POST'])
def test_printer():
    """测试打印机连接"""
    try:
        data = request.get_json()
        printer_name = data.get('printer_name') if data else None
        
        # 获取打印机列表来验证连接
        printers = printer_info.get_printers()
        
        if printer_name:
            # 测试指定打印机
            target_printer = None
            for printer in printers:
                if printer.get('name') == printer_name:
                    target_printer = printer
                    break
            
            if not target_printer:
                return jsonify({
                    "error": f"未找到打印机: {printer_name}",
                    "success": False
                }), 404
            
            return jsonify({
                "result": f"打印机 {printer_name} 连接正常",
                "printer_info": target_printer,
                "success": True
            })
        else:
            # 测试所有打印机
            return jsonify({
                "result": f"找到 {len(printers)} 台可用打印机",
                "printers": printers,
                "success": True
            })
        
    except Exception as e:
        return jsonify({
            "error": "测试打印机连接失败",
            "message": str(e),
            "success": False
        }), 500