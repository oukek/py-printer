#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像压缩工具类 (模拟 TinyPNG 效果)
提供视觉无损的有损压缩功能，无需外部二进制依赖，仅依赖 Pillow。
"""

import os
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
            img_format = img.format.upper() if img.format else ""
            
            # 获取原始大小
            original_size = os.path.getsize(input_path)

            save_kwargs = {"optimize": True}

            if img_format == "PNG":
                # PNG 压缩逻辑
                if png_quantize:
                    # 模拟 TinyPNG: 针对原生 Pillow 环境优化的量化方案
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # 尝试使用最高质量的 LIBIMAGEQUANT，如果不可用则使用高质量的原生适配方案
                    try:
                        # 优先尝试 LIBIMAGEQUANT (method=3)
                        img = img.quantize(colors=256, method=getattr(Image, 'LIBIMAGEQUANT', 3), kmeans=30, dither=Image.FLOYDSTEINBERG)
                    except (ValueError, Exception):
                        # 如果 LIBIMAGEQUANT 不可用，改用 Image.ADAPTIVE 调色板转换
                        # 这是原生 Pillow 处理渐变最细腻的方案，能有效减少“结块”感
                        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                
                img.save(output_path, "PNG", **save_kwargs)

            elif img_format in ["JPEG", "JPG"]:
                # JPG 压缩逻辑
                # 开启渐进式 (progressive) 和重新计算哈夫曼表 (optimize)
                # 禁用色度抽样 (subsampling=0) 以保持色彩鲜艳
                save_kwargs["quality"] = quality
                save_kwargs["progressive"] = True
                save_kwargs["subsampling"] = 0
                
                # 转换为 RGB (JPG 不支持 Alpha 通道)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(output_path, "JPEG", **save_kwargs)
            
            else:
                # 其他格式直接优化保存
                img.save(output_path, **save_kwargs)

            # 获取压缩后大小
            compressed_size = os.path.getsize(output_path)
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


if __name__ == "__main__":
    # 示例用法
    compressor = ImageCompressor()
    # result = compressor.compress("test.png")
    # print(result)
