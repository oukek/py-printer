#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF处理工具类
提供PDF转图片、PDF信息获取等功能
"""

import os
import tempfile
from typing import List, Optional, Tuple
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("PDF功能需要安装PyMuPDF库: pip install PyMuPDF")


class PDFUtils:
    """PDF处理工具类"""
    
    @staticmethod
    def is_available() -> bool:
        """检查PDF处理功能是否可用"""
        return PYMUPDF_AVAILABLE
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """
        获取PDF页数
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            int: 页数，如果出错返回0
        """
        if not PDFUtils.is_available():
            return 0
            
        try:
            pdf_document = fitz.open(pdf_path)
            page_count = len(pdf_document)
            pdf_document.close()
            return page_count
        except Exception as e:
            print(f"获取PDF页数时出错: {e}")
            return 0
    
    @staticmethod
    def convert_to_images(pdf_path: str, output_dir: Optional[str] = None, 
                         scale: float = 2.0, image_format: str = "PNG") -> List[str]:
        """
        将PDF转换为图片
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录，如果为None则使用临时目录
            scale: 缩放比例，默认2.0（提高质量）
            image_format: 图片格式，默认PNG
            
        Returns:
            List[str]: 生成的图片文件路径列表
        """
        if not PDFUtils.is_available():
            raise RuntimeError("PyMuPDF库不可用，无法转换PDF")
            
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 打开PDF文件
            pdf_document = fitz.open(pdf_path)
            image_paths = []
            
            # 确定输出目录
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            elif not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 转换每一页
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # 创建变换矩阵（缩放）
                matrix = fitz.Matrix(scale, scale)
                
                # 将页面渲染为图像
                pix = page.get_pixmap(matrix=matrix)
                
                # 生成输出文件名
                image_filename = f"page_{page_num + 1:03d}.{image_format.lower()}"
                image_path = os.path.join(output_dir, image_filename)
                
                # 保存图像
                pix.save(image_path)
                image_paths.append(image_path)
            
            # 关闭PDF文档
            pdf_document.close()
            
            return image_paths
            
        except Exception as e:
            raise RuntimeError(f"PDF转图片时出错: {e}")
    
    @staticmethod
    def convert_page_to_image(pdf_path: str, page_num: int, output_path: Optional[str] = None,
                             scale: float = 2.0, image_format: str = "PNG") -> str:
        """
        将PDF的指定页转换为图片
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从0开始）
            output_path: 输出文件路径，如果为None则自动生成
            scale: 缩放比例，默认2.0
            image_format: 图片格式，默认PNG
            
        Returns:
            str: 生成的图片文件路径
        """
        if not PDFUtils.is_available():
            raise RuntimeError("PyMuPDF库不可用，无法转换PDF")
            
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 打开PDF文件
            pdf_document = fitz.open(pdf_path)
            
            # 检查页码是否有效
            if page_num < 0 or page_num >= len(pdf_document):
                pdf_document.close()
                raise ValueError(f"页码 {page_num} 超出范围 (0-{len(pdf_document)-1})")
            
            # 加载指定页面
            page = pdf_document.load_page(page_num)
            
            # 创建变换矩阵（缩放）
            matrix = fitz.Matrix(scale, scale)
            
            # 将页面渲染为图像
            pix = page.get_pixmap(matrix=matrix)
            
            # 确定输出路径
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, f"page_{page_num + 1}.{image_format.lower()}")
            
            # 保存图像
            pix.save(output_path)
            
            # 关闭PDF文档
            pdf_document.close()
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"PDF转图片时出错: {e}")
    
    @staticmethod
    def get_page_size(pdf_path: str, page_num: int = 0) -> Optional[Tuple[float, float]]:
        """
        获取PDF页面尺寸
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从0开始），默认第一页
            
        Returns:
            Tuple[float, float]: (宽度, 高度) 单位为点(point)，如果出错返回None
        """
        if not PDFUtils.is_available():
            return None
            
        try:
            pdf_document = fitz.open(pdf_path)
            
            if page_num < 0 or page_num >= len(pdf_document):
                pdf_document.close()
                return None
            
            page = pdf_document.load_page(page_num)
            rect = page.rect
            size = (rect.width, rect.height)
            
            pdf_document.close()
            return size
            
        except Exception as e:
            print(f"获取PDF页面尺寸时出错: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_images(image_paths: List[str]) -> None:
        """
        清理临时图片文件
        
        Args:
            image_paths: 图片文件路径列表
        """
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.unlink(image_path)
            except Exception as e:
                print(f"删除临时文件 {image_path} 时出错: {e}")