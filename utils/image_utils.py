#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理工具类
提供印花模块所需的图像处理功能
"""

import os
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
import numpy as np


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        """初始化图像处理器"""
        pass
    
    def create_channel_image(self, image_data, shrink_pixels=1, channel_name="W1"):
        """
        创建通道图
        
        Args:
            image_data: 图像数据（base64编码或文件路径）
            shrink_pixels: 收缩像素数，默认为1
            channel_name: 专色通道名称，默认为"W1"
            
        Returns:
            dict: 包含处理结果的字典
        """
        try:
            # 加载图像
            image = self._load_image(image_data)
            if image is None:
                return {"success": False, "error": "无法加载图像"}
            
            # 转换为RGBA模式以便处理透明度
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 自动检测非透明区域创建选区蒙版
            mask = self._create_non_transparent_mask(image)
            
            # 收缩选区
            if shrink_pixels > 0:
                mask = self._shrink_mask(mask, shrink_pixels)
            
            # 创建专色通道
            channel_image = self._create_spot_color_channel(image, mask, channel_name)
            
            # 保存为TIF格式
            output_path = self._save_as_tif(channel_image, channel_name)
            
            return {
                "success": True,
                "output_path": output_path,
                "channel_name": channel_name,
                "message": f"成功创建专色通道 {channel_name}，自动检测非透明区域"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"处理图像时发生错误: {str(e)}"
            }
    
    def _load_image(self, image_data):
        """
        加载图像
        
        Args:
            image_data: 图像数据（base64编码或文件路径）
            
        Returns:
            PIL.Image: 加载的图像对象
        """
        try:
            # 判断是否为base64编码
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # 处理base64编码的图像
                header, encoded = image_data.split(',', 1)
                image_bytes = base64.b64decode(encoded)
                return Image.open(BytesIO(image_bytes))
            elif isinstance(image_data, str) and os.path.exists(image_data):
                # 处理文件路径
                return Image.open(image_data)
            elif isinstance(image_data, str):
                # 尝试直接解码base64
                try:
                    image_bytes = base64.b64decode(image_data)
                    return Image.open(BytesIO(image_bytes))
                except:
                    return None
            else:
                return None
        except Exception:
            return None
    
    def _create_non_transparent_mask(self, image):
        """
        创建非透明区域蒙版
        
        Args:
            image: PIL图像对象（RGBA模式）
            
        Returns:
            PIL.Image: 蒙版图像
        """
        width, height = image.size
        mask = Image.new('L', (width, height), 0)  # 创建黑色蒙版
        
        # 获取图像数据
        image_data = list(image.getdata())
        mask_data = []
        
        for pixel in image_data:
            # 检查alpha通道，如果不透明（alpha > 0）则设为白色，否则为黑色
            if len(pixel) >= 4 and pixel[3] > 0:  # RGBA模式，检查alpha通道
                mask_data.append(255)  # 白色表示选中区域
            elif len(pixel) == 3:  # RGB模式，没有透明度，全部选中
                mask_data.append(255)
            else:
                mask_data.append(0)  # 黑色表示透明区域
        
        mask.putdata(mask_data)
        return mask
    
    def _shrink_mask(self, mask, pixels):
        """
        收缩蒙版
        
        Args:
            mask: 蒙版图像
            pixels: 收缩像素数
            
        Returns:
            PIL.Image: 收缩后的蒙版
        """
        # 使用形态学操作进行收缩
        for _ in range(pixels):
            mask = mask.filter(ImageFilter.MinFilter(3))
        
        return mask
    
    def _create_spot_color_channel(self, image, mask, channel_name):
        """
        创建专色通道
        
        Args:
            image: 原始图像
            mask: 蒙版图像
            channel_name: 通道名称
            
        Returns:
            PIL.Image: 专色通道图像
        """
        # 创建CMYK图像用于专色通道
        width, height = image.size
        
        # 创建一个新的CMYK图像
        cmyk_image = Image.new('CMYK', (width, height), (0, 0, 0, 0))
        
        # 将原图转换为CMYK
        if image.mode != 'CMYK':
            rgb_image = image.convert('RGB')
            cmyk_image = rgb_image.convert('CMYK')
        else:
            cmyk_image = image.copy()
        
        # 应用蒙版到专色通道
        # 这里我们创建一个包含专色信息的图像
        # 由于PIL对专色支持有限，我们创建一个包含通道信息的特殊图像
        
        # 创建一个包含专色通道的图像
        spot_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 将蒙版应用到专色通道（这里用红色代表专色通道）
        spot_data = []
        mask_data = list(mask.getdata())
        
        for i, mask_value in enumerate(mask_data):
            if mask_value > 0:
                # 在蒙版区域设置专色（用红色表示）
                spot_data.append((255, 0, 0, mask_value))
            else:
                spot_data.append((0, 0, 0, 0))
        
        spot_image.putdata(spot_data)
        
        return spot_image
    
    def _save_as_tif(self, image, channel_name):
        """
        保存为TIF格式
        
        Args:
            image: 要保存的图像
            channel_name: 通道名称
            
        Returns:
            str: 保存的文件路径
        """
        # 创建输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成文件名
        filename = f"{channel_name}_channel.tif"
        output_path = os.path.join(output_dir, filename)
        
        # 保存为TIF格式
        image.save(output_path, format='TIFF', compression='lzw')
        
        return output_path
    
    def get_image_info(self, image_data):
        """
        获取图像信息
        
        Args:
            image_data: 图像数据
            
        Returns:
            dict: 图像信息
        """
        try:
            image = self._load_image(image_data)
            if image is None:
                return {"success": False, "error": "无法加载图像"}
            
            return {
                "success": True,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "size": f"{image.width}x{image.height}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取图像信息失败: {str(e)}"
            }