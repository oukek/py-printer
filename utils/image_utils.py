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
    import imagecodecs # 显式导入以确保打包时被包含
except ImportError:
    tifffile = None
    imagecodecs = None


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
    
    def batch_concatenate_images(self, file_paths, target_width=6614, dpi=300, batch_size=4, batch_id=None):
        """
        批量读取图片并每 N 张一组垂直拼接，保存到同级目录下的 concatenate 文件夹中
        
        Args:
            file_paths: 图片文件路径列表
            target_width: 目标宽度，默认为 6614
            dpi: 打印分辨率，默认为 300
            batch_size: 每组图片的数量，默认为 4
            batch_id: 批次号，用于作为输出文件名的前缀
            
        Returns:
            dict: 包含处理结果的字典
        """
        print(f"开始批量分组合并任务: 总文件数={len(file_paths)}, 批次号={batch_id}, 每组数量={batch_size}, 目标宽度={target_width}, DPI={dpi}")
        if not file_paths:
            print("警告: 文件列表为空，取消拼接任务")
            return {"success": False, "error": "文件列表为空"}
        
        if not tifffile:
            print("错误: 未安装 tifffile 库，无法执行流式保存")
            return {"success": False, "error": "未安装 tifffile 库，无法执行流式保存"}

        # 1. 确定输出目录：同级目录下的 concatenate
        first_file = file_paths[0]
        base_dir = os.path.dirname(os.path.abspath(first_file))
        target_output_dir = os.path.join(base_dir, "concatenate")
        if not os.path.exists(target_output_dir):
            os.makedirs(target_output_dir)
            print(f"创建输出目录: {target_output_dir}")

        # 2. 每 N 张图一组进行拆分
        batches = [file_paths[i:i + batch_size] for i in range(0, len(file_paths), batch_size)]
        print(f"共拆分为 {len(batches)} 组进行处理")

        success_batches = 0
        total_processed_files = 0

        for batch_idx, batch_files in enumerate(batches):
            prefix = f"{batch_id}-" if batch_id else "concatenate-"
            current_output_path = os.path.join(target_output_dir, f"{prefix}{batch_idx + 1}.tif")
            print(f"\n--- 正在处理第 {batch_idx + 1}/{len(batches)} 组 ---")
            
            try:
                # 预处理当前组
                image_configs = []
                total_height = 0
                
                # 计算间距 (0.3cm) 对应的像素值
                gap_px = int(0.3 * dpi / 2.54)
                
                for path in batch_files:
                    if not os.path.exists(path):
                        print(f"警告: 文件不存在，跳过: {path}")
                        continue
                    
                    with Image.open(path) as img:
                        w, h = img.size
                        if w > target_width:
                            new_w = target_width
                            new_h = int(h * (target_width / w))
                        else:
                            new_w, new_h = w, h
                        
                        offset_x = (target_width - new_w) // 2
                        image_configs.append({
                            "path": path,
                            "orig_size": (w, h),
                            "new_size": (new_w, new_h),
                            "offset_x": offset_x
                        })
                        total_height += new_h
                
                # 加上图片之间的间距
                if len(image_configs) > 1:
                    total_height += gap_px * (len(image_configs) - 1)

                if not image_configs:
                    print(f"警告: 第 {batch_idx + 1} 组没有有效的图片")
                    continue

                # 1. 创建临时内存映射文件 (未压缩，用于暂存拼接结果)
                temp_tif_path = current_output_path + ".tmp"
                print(f"  创建临时缓存文件: {temp_tif_path}")
                
                # 使用 memmap 创建一个巨大的全 0 数组，映射到磁盘文件
                memmap_array = tifffile.memmap(
                    temp_tif_path,
                    shape=(total_height, target_width, 4),
                    dtype='uint8',
                    photometric='rgb',
                    bigtiff=True
                )
                
                # 2. 逐个将图片填入 memmap 数组中
                curr_y = 0
                for i, config in enumerate(image_configs):
                    print(f"  拼接图片: {os.path.basename(config['path'])}")
                    with Image.open(config["path"]) as img:
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        if img.size != config["new_size"]:
                            img = img.resize(config["new_size"], Image.Resampling.LANCZOS)
                        
                        img_np = np.array(img)
                        x_start = config["offset_x"]
                        x_end = x_start + config["new_size"][0]
                        
                        # 写入 memmap 的对应切片区域
                        memmap_array[curr_y:curr_y+config["new_size"][1], x_start:x_end, :] = img_np
                        curr_y += config["new_size"][1]
                        
                        # 如果不是最后一张，则加上间距
                        if i < len(image_configs) - 1:
                            curr_y += gap_px
                
                # 刷新并关闭临时映射
                memmap_array.flush()
                del memmap_array # 必须删除引用才能释放文件锁定
                
                # 3. 将暂存的临时文件压缩后写入最终文件
                print(f"  正在执行 Adobe Deflate + Predictor 压缩...")
                res_val = (dpi, dpi)
                
                # 重新以读取模式打开临时文件
                with tifffile.TiffFile(temp_tif_path) as tif_read:
                    data_view = tif_read.asarray() # 这会返回一个 memmap 视图，不会占用大量内存
                    
                    with tifffile.TiffWriter(current_output_path, bigtiff=True) as tif_write:
                        tif_write.write(
                            data=data_view,
                            shape=(total_height, target_width, 4),
                            dtype='uint8',
                            photometric='rgb',
                            extrasamples=(tifffile.EXTRASAMPLE.UNASSALPHA,),
                            resolution=res_val,
                            resolutionunit='inch',
                            planarconfig='contig',
                            compression='adobe_deflate', # 启用 ZIP 压缩
                            compressionargs={'level': 8}, # 压缩等级 8 (速度与体积的平衡)
                            predictor=True,               # 启用水平预测器，大幅减小体积
                            rowsperstrip=100              # 条带高度
                        )
                
                # 4. 清理临时文件
                if os.path.exists(temp_tif_path):
                    os.remove(temp_tif_path)
                    
                print(f"第 {batch_idx + 1} 组合并成功: {current_output_path}")
                success_batches += 1
                total_processed_files += len(image_configs)

            except Exception as e:
                import traceback
                print(f"处理第 {batch_idx + 1} 组时发生错误: {str(e)}")
                traceback.print_exc()

        if success_batches > 0:
            msg = f"分组合并完成！共生成 {success_batches} 个长图文件，处理了 {total_processed_files} 张图片。保存目录: {target_output_dir}"
            print(f"\n{msg}")
            return {
                "success": True,
                "message": msg,
                "output_dir": target_output_dir,
                "success_count": success_batches
            }
        else:
            return {"success": False, "error": "所有分组合并均失败"}

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