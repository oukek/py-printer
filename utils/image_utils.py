#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理工具类
提供印花模块所需的图像处理功能
"""

import os
import base64
from io import BytesIO
from PIL import Image
# 解除大图限制，避免 DecompressionBombWarning
Image.MAX_IMAGE_PIXELS = None
import numpy as np
try:
    import tifffile
except ImportError:
    tifffile = None


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        """初始化图像处理器"""
        pass
    
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
    
    def batch_concatenate_images(self, file_paths, output_path=None, target_width=6614, dpi=300):
        """
        批量读取图片并垂直拼接，水平居中，流式保存为 TIFF
        
        Args:
            file_paths: 图片文件路径列表
            output_path: 输出文件路径
            target_width: 目标宽度，默认为 6614 (300dpi 下约 56cm)
            dpi: 打印分辨率，默认为 300
            
        Returns:
            dict: 包含处理结果的字典
        """
        if not file_paths:
            return {"success": False, "error": "文件列表为空"}
        
        if not tifffile:
            return {"success": False, "error": "未安装 tifffile 库，无法执行流式保存"}

        try:
            # 1. 预处理：计算每张图调整后的尺寸和总高度
            image_configs = []
            total_height = 0
            
            for path in file_paths:
                if not os.path.exists(path):
                    continue
                
                with Image.open(path) as img:
                    w, h = img.size
                    # 如果图片宽度超过目标宽度，则等比例缩放
                    if w > target_width:
                        new_w = target_width
                        new_h = int(h * (target_width / w))
                    else:
                        new_w, new_h = w, h
                    
                    # 水平居中的偏移量
                    offset_x = (target_width - new_w) // 2
                    
                    image_configs.append({
                        "path": path,
                        "orig_size": (w, h),
                        "new_size": (new_w, new_h),
                        "offset_x": offset_x
                    })
                    total_height += new_h

            if not image_configs:
                return {"success": False, "error": "没有有效的图片可以处理"}

            # 2. 确定输出路径并确保目录存在
            if not output_path:
                output_dir = "output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_path = os.path.join(output_dir, "batch_concatenated.tif")
            else:
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)

            # 3. 定义流式生成器 (按固定行数生成条带数据)
            rows_per_chunk = 100 
            # 确保 rows_per_chunk 不超过总高度
            actual_rows_per_strip = min(rows_per_chunk, total_height)
            
            def chunk_generator():
                current_image_idx = 0
                current_image_row = 0
                current_image_array = None
                
                total_processed_rows = 0
                
                while total_processed_rows < total_height:
                    # 总是分配固定高度的容器，确保与 actual_rows_per_strip 一致
                    # 这是 tifffile 流式写入的关键：每一块的大小必须完全相同
                    chunk = np.zeros((actual_rows_per_strip, target_width, 4), dtype=np.uint8)
                    
                    # 当前块实际需要填充的行数（最后一块可能不足 actual_rows_per_strip）
                    current_chunk_h = min(actual_rows_per_strip, total_height - total_processed_rows)
                    
                    rows_filled = 0
                    while rows_filled < current_chunk_h:
                        if current_image_array is None:
                            if current_image_idx >= len(image_configs):
                                break
                            
                            config = image_configs[current_image_idx]
                            with Image.open(config["path"]) as img:
                                if img.mode != 'RGBA':
                                    img = img.convert('RGBA')
                                if img.size != config["new_size"]:
                                    img = img.resize(config["new_size"], Image.Resampling.LANCZOS)
                                
                                full_img_array = np.zeros((config["new_size"][1], target_width, 4), dtype=np.uint8)
                                img_np = np.array(img)
                                x_start = config["offset_x"]
                                x_end = x_start + config["new_size"][0]
                                full_img_array[:, x_start:x_end, :] = img_np
                                current_image_array = full_img_array
                                current_image_row = 0
                        
                        rows_available = current_image_array.shape[0] - current_image_row
                        rows_to_copy = min(rows_available, current_chunk_h - rows_filled)
                        
                        chunk[rows_filled:rows_filled+rows_to_copy, :, :] = \
                            current_image_array[current_image_row:current_image_row+rows_to_copy, :, :]
                        
                        rows_filled += rows_to_copy
                        current_image_row += rows_to_copy
                        
                        if current_image_row >= current_image_array.shape[0]:
                            current_image_array = None
                            current_image_idx += 1
                    
                    total_processed_rows += current_chunk_h
                    # 只 yield 实际填充的部分，如果是最后一块，高度可能小于 actual_rows_per_strip
                    yield chunk[:current_chunk_h]

            # 4. 使用 TiffWriter 执行流式写入
            res_val = (dpi, dpi)
            
            with tifffile.TiffWriter(output_path, bigtiff=True) as tif:
                image_shape = (total_height, target_width, 4)
                
                tif.write(
                    data=chunk_generator(),
                    shape=image_shape,
                    dtype='uint8',
                    photometric='rgb',
                    extrasamples=(tifffile.EXTRASAMPLE.UNASSALPHA,),
                    resolution=res_val,
                    resolutionunit='inch',
                    # compression='adobe_deflate', # 经测试，开启压缩可能导致生成器流式写入失败
                    planarconfig='contig',
                    rowsperstrip=actual_rows_per_strip, # 必须与 chunk 高度严格匹配
                    metadata={'axes': 'YXS'}
                )

            return {
                "success": True,
                "output_path": output_path,
                "total_height": total_height,
                "width": target_width,
                "message": f"成功拼接 {len(image_configs)} 张图片，总高度 {total_height} 像素"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"批量拼接图片时发生错误: {str(e)}"
            }

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