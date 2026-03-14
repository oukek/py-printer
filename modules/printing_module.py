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


@printing_bp.route('/image/concatenate', methods=['POST'])
def concatenate_images():
    """批量垂直拼接图像"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "请求体不能为空",
                "success": False
            }), 400
        
        file_paths = data.get('file_paths')
        output_path = data.get('output_path')
        target_width = data.get('target_width', 6614)
        dpi = data.get('dpi', 300)
        batch_size = data.get('batch_size', 4)
        batch_id = data.get('batch_id')
        
        if not file_paths:
            return jsonify({
                "error": "缺少file_paths参数",
                "success": False
            }), 400
        
        # 批量拼接图像
        result = image_processor.batch_concatenate_images(
            file_paths=file_paths,
            output_path=output_path,
            target_width=target_width,
            dpi=dpi,
            batch_size=batch_size,
            batch_id=batch_id
        )
        
        if result.get('success'):
            return jsonify({
                "result": result,
                "success": True,
                "message": result.get('message', '图像拼接成功')
            })
        else:
            return jsonify({
                "error": result.get('error', '图像拼接失败'),
                "success": False
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "图像拼接过程发生错误",
            "message": str(e),
            "success": False
        }), 500

