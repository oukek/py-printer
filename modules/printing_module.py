#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印花模块
提供印花相关的API接口
"""

from flask import Blueprint, jsonify, request
from utils.image_utils import ImageProcessor


# 创建蓝图
printing_bp = Blueprint('printing', __name__)

# 创建图像处理器实例
image_processor = ImageProcessor()


@printing_bp.route('/channel/create', methods=['POST'])
def create_channel():
    """
    做通道图
    功能：传过来一张图片，自动对图片的所有非透明区域做选区，对选区收缩1个像素，对选区创建专色通道，命名为W1，文件保存为tif格式
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        # 获取参数
        image_data = data.get('image_data')
        shrink_pixels = data.get('shrink_pixels', 1)  # 默认收缩1个像素
        channel_name = data.get('channel_name', 'W1')  # 默认通道名为W1
        
        if not image_data:
            return jsonify({
                "error": "缺少image_data参数",
                "success": False
            }), 400
        
        # 处理图像
        result = image_processor.create_channel_image(
            image_data=image_data,
            shrink_pixels=shrink_pixels,
            channel_name=channel_name
        )
        
        if result.get('success'):
            return jsonify({
                "result": result,
                "success": True,
                "message": result.get('message', '通道图创建成功')
            })
        else:
            return jsonify({
                "error": result.get('error', '通道图创建失败'),
                "success": False
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "创建通道图失败",
            "message": str(e),
            "success": False
        }), 500


@printing_bp.route('/image/info', methods=['POST'])
def get_image_info():
    """获取图像信息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({
                "error": "缺少image_data参数",
                "success": False
            }), 400
        
        # 获取图像信息
        result = image_processor.get_image_info(image_data)
        
        if result.get('success'):
            return jsonify({
                "result": result,
                "success": True
            })
        else:
            return jsonify({
                "error": result.get('error', '获取图像信息失败'),
                "success": False
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "获取图像信息失败",
            "message": str(e),
            "success": False
        }), 500


@printing_bp.route('/test', methods=['GET'])
def test_printing():
    """测试印花模块"""
    try:
        return jsonify({
            "message": "印花模块运行正常",
            "success": True,
            "endpoints": {
                "/printing/channel/create": "创建通道图 (POST)",
                "/printing/image/info": "获取图像信息 (POST)",
                "/printing/test": "测试印花模块 (GET)"
            }
        })
    except Exception as e:
        return jsonify({
            "error": "印花模块测试失败",
            "message": str(e),
            "success": False
        }), 500