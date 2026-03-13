#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩模块
提供图像压缩相关的API接口
"""

from flask import Blueprint, jsonify, request
from utils.compress_utils import ImageCompressor


# 创建蓝图
compress_bp = Blueprint('compress', __name__)

# 创建压缩器实例
compressor = ImageCompressor()


@compress_bp.route('/image', methods=['POST'])
def compress_image():
    """
    压缩图像
    参数:
        input_path: 输入文件路径
        output_path: 输出文件路径 (可选)
        quality: JPG 压缩质量 (1-100)，默认 100
        png_quantize: 是否对 PNG 进行颜色量化，默认 True
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        # 获取参数
        input_path = data.get('input_path')
        output_path = data.get('output_path')
        quality = data.get('quality', 100)
        png_quantize = data.get('png_quantize', True)
        
        if not input_path:
            return jsonify({
                "error": "缺少input_path参数",
                "success": False
            }), 400
        
        # 处理压缩
        result = compressor.compress(
            input_path=input_path,
            output_path=output_path,
            quality=quality,
            png_quantize=png_quantize
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({
                "error": result.get('error', '压缩失败'),
                "success": False
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "压缩图像失败",
            "message": str(e),
            "success": False
        }), 500

@compress_bp.route('/test', methods=['GET'])
def test_compress():
    """测试压缩模块"""
    try:
        return jsonify({
            "message": "压缩模块运行正常",
            "success": True,
            "endpoints": {
                "/compress/image": "压缩图像 (POST)",
                "/compress/test": "测试压缩模块 (GET)"
            }
        })
    except Exception as e:
        return jsonify({
            "error": "压缩模块测试失败",
            "message": str(e),
            "success": False
        }), 500

@compress_bp.route('/image/base64', methods=['POST'])
def compress_image_base64():
    """
    压缩Base64编码的图像
    参数:
        image_base64: Base64编码的图像字符串
        quality: JPG 压缩质量 (1-100)，默认 100
        png_quantize: 是否对 PNG 进行颜色量化，默认 True
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        # 获取参数
        image_base64 = data.get('image_base64')
        quality = data.get('quality', 100)
        png_quantize = data.get('png_quantize', True)
        
        if not image_base64:
            return jsonify({
                "error": "缺少image_base64参数",
                "success": False
            }), 400
        
        # 处理压缩
        result = compressor.compress_base64(
            image_base64=image_base64,
            quality=quality,
            png_quantize=png_quantize
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({
                "error": result.get('error', '压缩失败'),
                "success": False
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "压缩Base64图像失败",
            "message": str(e),
            "success": False
        }), 500
