#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像压缩工具类 (模拟 TinyPNG 效果)
提供视觉无损的有损压缩功能，无需外部二进制依赖，仅依赖 Pillow。
"""

import os
import base64
from io import BytesIO
from PIL import Image


class ImageCompressor:
    """图像压缩器"""

    @staticmethod
    def compress(input_path, output_path=None, quality=100, png_quantize=True):
        """
        压缩图像 (支持 PNG 和 JPG)
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径。如果为 None，则在原文件名后添加 _compressed
            quality: JPG 压缩质量 (1-100)，默认 100
            png_quantize: 是否对 PNG 进行颜色量化（模拟 TinyPNG 效果）。
                          True: 有损压缩，大幅减小体积。
                          False: 无损压缩，仅优化文件结构。
                          
        Returns:
            dict: 包含处理结果的字典
        """
        try:
            if not os.path.exists(input_path):
                return {"success": False, "error": f"找不到文件: {input_path}"}

            # 处理输出路径
            if output_path is None:
                file_name, ext = os.path.splitext(input_path)
                output_path = f"{file_name}_compressed{ext}"

            # 打开图像
            img = Image.open(input_path)
            original_size = os.path.getsize(input_path)
            
            # 执行压缩逻辑
            result_io, img_format = ImageCompressor._process_compression(img, quality, png_quantize)
            
            # 保存到文件
            with open(output_path, "wb") as f:
                f.write(result_io.getvalue())

            # 获取压缩后大小
            compressed_size = len(result_io.getvalue())
            ratio = (1 - compressed_size / original_size) * 100

            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "original_size": f"{original_size / 1024:.2f} KB",
                "compressed_size": f"{compressed_size / 1024:.2f} KB",
                "ratio": f"{ratio:.2f}%",
                "message": "压缩成功"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"压缩过程中发生错误: {str(e)}"
            }

    @staticmethod
    def compress_base64(image_base64, quality=100, png_quantize=True):
        """
        压缩 base64 图像并返回压缩后的 base64 数据
        
        Args:
            image_base64: 原始图像的 base64 字符串（支持带 data:image/...;base64, 前缀或纯 base64）
            quality: JPG 质量
            png_quantize: PNG 是否量化
            
        Returns:
            dict: 包含压缩后的 base64 数据和统计信息的字典
        """
        try:
            # 处理 base64 前缀
            header = ""
            if "," in image_base64:
                header, image_base64 = image_base64.split(",", 1)
                header += ","
            
            # 解码 base64
            image_bytes = base64.b64decode(image_base64)
            original_size = len(image_bytes)
            
            # 载入图像
            img = Image.open(BytesIO(image_bytes))
            
            # 执行压缩逻辑
            result_io, img_format = ImageCompressor._process_compression(img, quality, png_quantize)
            
            # 编码为 base64
            compressed_bytes = result_io.getvalue()
            compressed_base64 = base64.b64encode(compressed_bytes).decode('utf-8')
            compressed_size = len(compressed_bytes)
            ratio = (1 - compressed_size / original_size) * 100
            
            # 如果原先有前缀，根据压缩后的格式更新前缀（如果格式发生变化）
            if header:
                ext = img_format.lower()
                if ext == "jpeg": ext = "jpg"
                header = f"data:image/{ext};base64,"

            return {
                "success": True,
                "compressed_base64": header + compressed_base64,
                "original_size": f"{original_size / 1024:.2f} KB",
                "compressed_size": f"{compressed_size / 1024:.2f} KB",
                "ratio": f"{ratio:.2f}%",
                "format": img_format,
                "message": "压缩成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Base64 压缩过程中发生错误: {str(e)}"
            }

    @staticmethod
    def _process_compression(img, quality=100, png_quantize=True):
        """内部通用的核心压缩处理逻辑"""
        img_format = img.format.upper() if img.format else "PNG"
        if img_format not in ["PNG", "JPEG", "JPG"]:
            # 如果无法识别格式，默认尝试按原有格式保存
            img_format = "PNG"

        save_kwargs = {"optimize": True}
        output_io = BytesIO()

        if img_format == "PNG":
            if png_quantize:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                try:
                    img = img.quantize(colors=256, method=getattr(Image, 'LIBIMAGEQUANT', 3), kmeans=30, dither=Image.FLOYDSTEINBERG)
                except (ValueError, Exception):
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
            img.save(output_io, "PNG", **save_kwargs)

        elif img_format in ["JPEG", "JPG"]:
            save_kwargs["quality"] = quality
            save_kwargs["progressive"] = True
            save_kwargs["subsampling"] = 0
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_io, "JPEG", **save_kwargs)
            img_format = "JPEG"
        
        else:
            img.save(output_io, format=img_format, **save_kwargs)

        return output_io, img_format


if __name__ == "__main__":
    # 示例用法
    compressor = ImageCompressor()
    # result = compressor.compress("test.png")
    # print(result)
