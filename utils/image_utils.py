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
    
    def batch_concatenate_images(self, file_paths, output_path=None, target_width=6614, dpi=300, batch_size=4, batch_id=None):
        """
        批量读取图片并每 N 张一组垂直拼接，保存到同级目录下的 concatenate 文件夹中 (固定 RGBA 格式)
        
        Args:
            file_paths: 图片文件路径列表
            output_path: (已弃用) 为了兼容保留，逻辑将自动确定输出路径
            target_width: 目标宽度，默认为 6614
            dpi: 打印分辨率，默认为 300
            batch_size: 每组图片的数量，默认为 4
            batch_id: 批次号，用于作为输出文件名的前缀
            
        Returns:
            dict: 包含处理结果的字典
        """
        print(f"开始批量分组合并任务: 总文件数={len(file_paths)}, 批次号={batch_id}, 每组数量={batch_size}, 模式=RGBA, 目标宽度={target_width}, DPI={dpi}")
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
                
                # 固定为 RGBA 模式，4 个通道
                photometric = 'rgb'
                num_channels = 4
                
                # 使用 memmap 创建一个巨大的全 0 数组，映射到磁盘文件
                memmap_array = tifffile.memmap(
                    temp_tif_path,
                    shape=(total_height, target_width, num_channels),
                    dtype='uint8',
                    photometric=photometric,
                    bigtiff=True
                )
                
                # 2. 逐个将图片填入 memmap 数组中
                curr_y = 0
                for i, config in enumerate(image_configs):
                    print(f"  拼接图片: {os.path.basename(config['path'])}")
                    with Image.open(config["path"]) as img:
                        # 转换颜色模式为 RGBA
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
                            shape=(total_height, target_width, num_channels),
                            dtype='uint8',
                            photometric=photometric,
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

    def draw_sprite_by_layout(self, sprite_layout, width, height, dpi=300, output_path=None):
        """
        根据布局绘制雪碧图，并保存为 RGBA TIFF
        
        Args:
            sprite_layout: 布局数组，每个元素包含 {x, y, width, height, rotated, meta}
                           meta 可以是图片路径、base64 或 PIL.Image 对象
            width: 总宽度 (像素或物理尺寸，由调用方保证与布局一致)
            height: 总高度
            dpi: 打印分辨率，默认为 300
            output_path: 输出路径，如果为 None 则返回字节流
            
        Returns:
            bytes or str: 如果 output_path 为 None 返回字节流，否则返回路径
        """
        print(f"开始根据布局绘制雪碧图: 尺寸={width}x{height}, DPI={dpi}, 元素数={len(sprite_layout)}")
        
        if not tifffile:
            raise RuntimeError("未安装 tifffile 库，无法执行流式保存")

        # 1. 准备参数
        sharp_width = int(round(width))
        sharp_height = int(round(height))
        num_channels = 4  # RGBA
        photometric = 'rgb'
        
        # 2. 创建临时 memmap 文件
        temp_tif_path = (output_path if output_path else "temp_sprite.tif") + ".tmp"
        
        try:
            # 使用 memmap 创建一个全 0 数组 (RGBA 全 0 代表透明)
            memmap_array = tifffile.memmap(
                temp_tif_path,
                shape=(sharp_height, sharp_width, num_channels),
                dtype='uint8',
                photometric=photometric,
                bigtiff=True
            )
            
            # 初始化为全 0
            memmap_array[:] = 0

            # 3. 逐个绘制布局项
            for i, layout in enumerate(sprite_layout):
                try:
                    # 加载图片
                    img = self._load_image(layout['meta'])
                    if img is None:
                        print(f"警告: 无法加载图片，索引 {i}")
                        continue
                    
                    # 确保是 RGBA
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # 处理旋转
                    if layout.get('rotated', False):
                        img = img.rotate(270, expand=True)
                    
                    # 调整大小
                    target_w = int(round(layout['width']))
                    target_h = int(round(layout['height']))
                    if img.size != (target_w, target_h):
                        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    
                    # 转换为 numpy 数组
                    img_np = np.array(img)
                    
                    # 确定放置位置
                    x_start = int(round(layout['x']))
                    y_start = int(round(layout['y']))
                    x_end = x_start + target_w
                    y_end = y_start + target_h
                    
                    # 检查边界溢出
                    if x_end > sharp_width or y_end > sharp_height:
                        print(f"警告: 布局项 {i} 超出边界，进行裁剪")
                        x_end = min(x_end, sharp_width)
                        y_end = min(y_end, sharp_height)
                        img_np = img_np[:y_end-y_start, :x_end-x_start, :]
                    
                    # 写入 memmap
                    memmap_array[y_start:y_end, x_start:x_end, :] = img_np
                    
                    # 显式关闭 img 以释放内存
                    img.close()
                    
                    if (i + 1) % 10 == 0:
                        print(f"  已绘制 {i + 1}/{len(sprite_layout)} 个元素")
                        
                except Exception as e:
                    print(f"绘制布局项 {i} 时出错: {str(e)}")

            # 4. 刷新并关闭临时映射
            memmap_array.flush()
            del memmap_array
            
            # 5. 压缩并保存
            print("  正在执行 Adobe Deflate 压缩...")
            res_val = (dpi, dpi)
            
            final_output = output_path if output_path else BytesIO()
            
            with tifffile.TiffFile(temp_tif_path) as tif_read:
                data_view = tif_read.asarray()
                
                with tifffile.TiffWriter(final_output, bigtiff=True) as tif_write:
                    tif_write.write(
                        data=data_view,
                        shape=(sharp_height, sharp_width, num_channels),
                        dtype='uint8',
                        photometric=photometric,
                        resolution=res_val,
                        resolutionunit='inch',
                        planarconfig='contig',
                        compression='adobe_deflate',
                        compressionargs={'level': 8},
                        predictor=True
                    )
            
            # 清理临时文件
            if os.path.exists(temp_tif_path):
                os.remove(temp_tif_path)
            
            if output_path:
                print(f"雪碧图绘制完成: {output_path}")
                return output_path
            else:
                return final_output.getvalue()
                
        except Exception as e:
            if os.path.exists(temp_tif_path):
                os.remove(temp_tif_path)
            raise e

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