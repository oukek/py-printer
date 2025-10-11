#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机信息获取工具
获取系统中的打印机列表和每个打印机支持的纸张类型
支持PDF和图片打印功能
"""

import os
import base64
import tempfile
from typing import List, Dict, Any, Optional

# 导入自定义工具类
from .pdf_utils import PDFUtils
from .command_utils import CommandUtils, PrinterStatusUtils, PlatformUtils

# 条件导入Windows相关模块
if PlatformUtils.is_windows():
    try:
        import win32con
    except ImportError:
        win32con = None
        print("Windows系统需要安装pywin32库: pip install pywin32")
else:
    win32con = None

# 导入图像处理库
from PIL import Image


class PrinterInfo:
    """打印机信息类"""
    
    def __init__(self):
        self.system = PlatformUtils.get_system()
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """
        获取系统中所有打印机的信息
        
        Returns:
            List[Dict]: 包含打印机信息的列表
        """
        if PlatformUtils.is_windows():
            return self._get_windows_printers()
        elif PlatformUtils.is_macos():
            return self._get_macos_printers()
        elif PlatformUtils.is_linux():
            return self._get_linux_printers()
        else:
            raise NotImplementedError(f"不支持的操作系统: {self.system}")
    
    def get_paper_dimensions(self, printer_name: str, paper_size: str) -> Optional[Dict[str, float]]:
        """
        获取指定打印机和纸张的尺寸信息
        
        Args:
            printer_name: 打印机名称
            paper_size: 纸张大小名称
            
        Returns:
            Dict[str, float]: 包含width和height的字典（单位：毫米），如果未找到则返回None
        """
        try:
            printers = self.get_printers()
            
            # 查找指定打印机
            target_printer = None
            for printer in printers:
                if printer['name'] == printer_name:
                    target_printer = printer
                    break
            
            if not target_printer:
                print(f"未找到打印机: {printer_name}")
                return None
            
            # 查找指定纸张
            for paper in target_printer.get('paper_sizes', []):
                if PlatformUtils.is_windows():
                    # Windows平台有详细的尺寸信息
                    if paper.get('name', '').lower() == paper_size.lower():
                        # Windows返回的尺寸单位是0.1mm，需要转换为mm
                        return {
                            'width': paper['width'] / 10.0,
                            'height': paper['height'] / 10.0
                        }
                else:
                    # macOS/Linux平台需要通过纸张名称映射到标准尺寸
                    if paper.get('name', '').lower() == paper_size.lower():
                        return self._get_standard_paper_size(paper_size)
            
            print(f"未找到纸张: {paper_size}")
            return None
            
        except Exception as e:
            print(f"获取纸张尺寸时出错: {e}")
            return None
    
    def _get_standard_paper_size(self, paper_name: str) -> Optional[Dict[str, float]]:
        """
        获取标准纸张尺寸（用于macOS/Linux平台）
        
        Args:
            paper_name: 纸张名称
            
        Returns:
            Dict[str, float]: 包含width和height的字典（单位：毫米）
        """
        # 标准纸张尺寸映射表（单位：毫米）
        standard_sizes = {
            # ISO A系列
            'a4': {'width': 210, 'height': 297},
            'a3': {'width': 297, 'height': 420},
            'a5': {'width': 148, 'height': 210},
            
            # 北美标准
            'letter': {'width': 216, 'height': 279},
            'legal': {'width': 216, 'height': 356},
            'tabloid': {'width': 279, 'height': 432},
            
            # 其他常见尺寸
            'b4': {'width': 250, 'height': 353},
            'b5': {'width': 176, 'height': 250},
            'executive': {'width': 184, 'height': 267},
            'folio': {'width': 210, 'height': 330},
            
            # 热敏纸标准尺寸
            # 小票纸
            '58mm': {'width': 58, 'height': 297},  # 58mm宽度，长度可变，默认A4长度
            '80mm': {'width': 80, 'height': 297},  # 80mm宽度，长度可变
            
            # 标签纸
            '40x30': {'width': 40, 'height': 30},   # 40x30mm标签
            '50x30': {'width': 50, 'height': 30},   # 50x30mm标签
            '60x40': {'width': 60, 'height': 40},   # 60x40mm标签
            '70x50': {'width': 70, 'height': 50},   # 70x50mm标签
            '100x50': {'width': 100, 'height': 50}, # 100x50mm标签
            '100x70': {'width': 100, 'height': 70}, # 100x70mm标签
            '100x100': {'width': 100, 'height': 100}, # 100x100mm标签
            
            # 快递单据
            '100x150': {'width': 100, 'height': 150}, # 快递标签
            '100x180': {'width': 100, 'height': 180}, # 大号快递标签
            
            # 珠宝标签
            '30x20': {'width': 30, 'height': 20},   # 珠宝小标签
            '40x20': {'width': 40, 'height': 20},   # 珠宝标签
            
            # 服装吊牌
            '40x60': {'width': 40, 'height': 60},   # 服装吊牌
            '50x80': {'width': 50, 'height': 80},   # 大号服装吊牌
            
            # 条码标签
            '25x15': {'width': 25, 'height': 15},   # 小条码标签
            '32x19': {'width': 32, 'height': 19},   # 标准条码标签
            '40x25': {'width': 40, 'height': 25},   # 大条码标签
            
            # 价格标签
            '22x12': {'width': 22, 'height': 12},   # 价格标签
            '26x16': {'width': 26, 'height': 16},   # 价格标签
            
            # 医疗标签
            '25x25': {'width': 25, 'height': 25},   # 医疗标签
            '38x25': {'width': 38, 'height': 25},   # 医疗标签
            
            # 物流标签
            '76x25': {'width': 76, 'height': 25},   # 物流标签
            '76x38': {'width': 76, 'height': 38},   # 物流标签
            
            # 热敏纸卷纸（宽度固定，长度连续）
            'thermal57': {'width': 57, 'height': 297},  # 57mm热敏纸
            'thermal80': {'width': 80, 'height': 297},  # 80mm热敏纸
            'thermal110': {'width': 110, 'height': 297}, # 110mm热敏纸
        }
        
        # 清理纸张名称（去除空格、下划线，转小写）
        clean_name = paper_name.lower().replace('_', '').replace(' ', '').replace('x', 'x')
        
        return standard_sizes.get(clean_name)
    
    def _resize_image_for_printing(self, image: Image.Image, paper_width_mm: float, paper_height_mm: float, dpi: int = 300, margin_mm: float = 10) -> Image.Image:
        """
        调整图片尺寸以适应可打印区域
        
        Args:
            image: 原始图片
            paper_width_mm: 纸张宽度（毫米）
            paper_height_mm: 纸张高度（毫米）
            dpi: 目标DPI
            margin_mm: 边距（毫米）
            
        Returns:
            调整后的图片
        """
        # 计算可打印区域（减去边距）
        printable_width_mm = paper_width_mm - 2 * margin_mm
        printable_height_mm = paper_height_mm - 2 * margin_mm
        
        # 将毫米转换为像素
        printable_width_px = int(printable_width_mm * dpi / 25.4)
        printable_height_px = int(printable_height_mm * dpi / 25.4)
        
        # 计算缩放比例
        width_ratio = printable_width_px / image.width
        height_ratio = printable_height_px / image.height
        
        # 选择较小的缩放比例，确保图片完全适应纸张
        scale_ratio = min(width_ratio, height_ratio)
        
        # 如果图片已经比可打印区域小，不进行放大
        if scale_ratio > 1:
            scale_ratio = 1
        
        # 计算新尺寸
        new_width = int(image.width * scale_ratio)
        new_height = int(image.height * scale_ratio)
        
        print(f"图片缩放信息:")
        print(f"  原始尺寸: {image.width}x{image.height} 像素")
        print(f"  可打印区域: {printable_width_px}x{printable_height_px} 像素")
        print(f"  缩放比例: {scale_ratio:.2f}")
        print(f"  新尺寸: {new_width}x{new_height} 像素")
        
        # 缩放图片
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def print_file(self, file_path: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        打印文件（支持PDF和图片）
        
        Args:
            file_path: 要打印的文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
            
        Returns:
            bool: 打印是否成功
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件 {file_path} 不存在")
            return False
            
        # 根据文件类型选择打印方法
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._print_pdf(file_path, printer_name, paper_size)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
            return self._print_image(file_path, printer_name, paper_size)
        else:
            print(f"不支持的文件类型: {file_ext}")
            return False
            
    def print_data(self, data: str, file_type: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        打印Base64编码的数据或文件路径
        
        Args:
            data: Base64编码的数据或文件路径
            file_type: 文件类型，如'pdf'、'jpg'等
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
            
        Returns:
            bool: 打印是否成功
        """
        # 检查是否是文件路径
        if os.path.exists(data):
            return self.print_file(data, printer_name, paper_size)
            
        # 尝试解码Base64数据
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as temp_file:
                temp_path = temp_file.name
                
                # 解码Base64数据并写入临时文件
                file_data = base64.b64decode(data)
                temp_file.write(file_data)
                
            # 打印临时文件
            result = self.print_file(temp_path, printer_name, paper_size)
            
            # 删除临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return result
            
        except Exception as e:
            print(f"处理Base64数据时出错: {e}")
            return False
    
    def _print_pdf(self, pdf_path: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        打印PDF文件
        
        Args:
            pdf_path: PDF文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
        """
        try:
            # 检查PDF工具是否可用
            if not PDFUtils.is_available():
                print("错误: 缺少PyMuPDF库，无法打印PDF文件")
                return False
                
            # 使用PDF工具类转换为图片
            image_paths = PDFUtils.convert_to_images(pdf_path)
            
            # 打印每一页
            success = True
            for image_path in image_paths:
                if not self._print_image(image_path, printer_name, paper_size):
                    success = False
            
            # 清理临时文件
            PDFUtils.cleanup_temp_images(image_paths)
            
            return success
                
        except Exception as e:
            print(f"打印PDF时出错: {e}")
            return False
    
    def _print_image(self, image_path: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        打印图像文件
        
        Args:
            image_path: 图像文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
        """
        try:
            # 打开图像
            image = Image.open(image_path)
            
            # 如果指定了纸张大小，进行图片缩放
            if paper_size and printer_name:
                paper_dimensions = self.get_paper_dimensions(printer_name, paper_size)
                if paper_dimensions:
                    print(f"纸张尺寸: {paper_dimensions['width']}mm x {paper_dimensions['height']}mm")
                    image = self._resize_image_for_printing(
                        image, 
                        paper_dimensions['width'], 
                        paper_dimensions['height']
                    )
                else:
                    print("无法获取纸张尺寸，使用原始图片尺寸打印")
            
            if PlatformUtils.is_windows():
                return self._print_image_windows(image, printer_name, paper_size)
            elif PlatformUtils.is_macos():
                # 对于macOS，需要保存缩放后的图片到临时文件
                if paper_size and printer_name:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        image.save(temp_file.name, 'PNG')
                        result = self._print_image_macos(temp_file.name, printer_name, paper_size)
                        os.unlink(temp_file.name)  # 删除临时文件
                        return result
                else:
                    return self._print_image_macos(image_path, printer_name, paper_size)
            elif PlatformUtils.is_linux():
                # 对于Linux，需要保存缩放后的图片到临时文件
                if paper_size and printer_name:
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        image.save(temp_file.name, 'PNG')
                        result = self._print_image_linux(temp_file.name, printer_name, paper_size)
                        os.unlink(temp_file.name)  # 删除临时文件
                        return result
                else:
                    return self._print_image_linux(image_path, printer_name, paper_size)
            else:
                print(f"不支持的操作系统: {self.system}")
                return False
                
        except Exception as e:
            print(f"打印图像时出错: {e}")
            return False
    
    def _print_image_windows(self, image: Image.Image, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        在Windows上打印图像
        
        Args:
            image: PIL图像对象
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
        """
        try:
            import win32print
            import win32ui
            from PIL import ImageWin
            
            # 获取打印机设备上下文
            if printer_name is None:
                printer_name = win32print.GetDefaultPrinter()
            
            # 设置纸张大小
            if paper_size is not None:
                # 获取打印机句柄
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    # 获取打印机属性
                    devmode = win32print.GetPrinter(hPrinter, 2)["pDevMode"]
                    # 查找匹配的纸张大小
                    paper_sizes = self._get_windows_paper_sizes(hPrinter)
                    for paper in paper_sizes:
                        if paper['name'].lower() == paper_size.lower():
                            devmode.PaperSize = paper['id']
                            win32print.SetPrinter(hPrinter, 2, {"pDevMode": devmode}, 0)
                            break
                finally:
                    win32print.ClosePrinter(hPrinter)
                
            # 创建设置上下文
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            
            # 开始文档打印
            hDC.StartDoc("图像打印")
            hDC.StartPage()
            
            # 获取打印机分辨率
            # 使用常量值代替win32con，避免跨平台问题
            dpi_x = hDC.GetDeviceCaps(88)  # LOGPIXELSX = 88
            dpi_y = hDC.GetDeviceCaps(90)  # LOGPIXELSY = 90
            
            # 获取打印机物理页面和可打印区域信息
            # 物理页面尺寸
            physical_width = hDC.GetDeviceCaps(110)   # HORZRES = 110
            physical_height = hDC.GetDeviceCaps(111)  # VERTRES = 111
            
            # 物理页面的左上角偏移（物理边距）
            physical_offset_x = hDC.GetDeviceCaps(112)  # PHYSICALOFFSETX = 112
            physical_offset_y = hDC.GetDeviceCaps(113)  # PHYSICALOFFSETY = 113
            
            # 实际可打印区域尺寸（考虑物理边距）
            printable_width = physical_width
            printable_height = physical_height
            
            print(f"打印区域信息:")
            print(f"  物理页面尺寸: {physical_width}x{physical_height} 像素")
            print(f"  物理边距偏移: ({physical_offset_x}, {physical_offset_y}) 像素")
            print(f"  可打印区域: {printable_width}x{printable_height} 像素")
            
            # 计算图片在打印区域的位置（居中）
            img_width = image.width
            img_height = image.height
            
            print(f"原始图片尺寸: {img_width}x{img_height} 像素")
            
            # 如果图片比可打印区域大，按比例缩放
            if img_width > printable_width or img_height > printable_height:
                scale_x = printable_width / img_width
                scale_y = printable_height / img_height
                scale = min(scale_x, scale_y)
                img_width = int(img_width * scale)
                img_height = int(img_height * scale)
                print(f"缩放后图片尺寸: {img_width}x{img_height} 像素 (缩放比例: {scale:.2f})")
            
            # 计算打印位置：横向居中，垂直从上开始
            # 横向居中：在可打印区域内居中，然后加上物理边距偏移
            x = physical_offset_x + (printable_width - img_width) // 2
            # 垂直从上开始：直接使用物理边距偏移作为起始位置
            y = physical_offset_y
            
            print(f"图片打印位置: ({x}, {y}) 像素 (横向居中，垂直从上开始)")
            
            # 打印图像
            ImageWin.Dib(image).draw(hDC.GetHandleOutput(), 
                                    (x, y, x + img_width, y + img_height))
            
            # 结束打印
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            
            return True
            
        except ImportError:
            print("Windows系统需要安装pywin32库: pip install pywin32")
            return False
        except Exception as e:
            print(f"Windows打印图像时出错: {e}")
            return False
    
    def _print_image_macos(self, image_path: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        在macOS上打印图像
        
        Args:
            image_path: 图像文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
        """
        try:
            cmd = CommandUtils.build_print_command(printer_name, paper_size, image_path)
            result = CommandUtils.run_command(cmd)
            
            if result.returncode != 0:
                print(f"打印失败: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"macOS打印图像时出错: {e}")
            return False
    
    def _print_image_linux(self, image_path: str, printer_name: Optional[str] = None, paper_size: Optional[str] = None) -> bool:
        """
        在Linux上打印图像
        
        Args:
            image_path: 图像文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            paper_size: 纸张大小，如果为None则使用默认纸张大小
        """
        try:
            cmd = CommandUtils.build_print_command(printer_name, paper_size, image_path)
            result = CommandUtils.run_command(cmd)
            
            if result.returncode != 0:
                print(f"打印失败: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Linux打印图像时出错: {e}")
            return False
    
    def _get_windows_printers(self) -> List[Dict[str, Any]]:
        """获取Windows系统的打印机信息"""
        try:
            import win32print
            printers = []
            
            # 获取所有打印机
            printer_list = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            
            for printer in printer_list:
                printer_name = printer[2]  # 打印机名称
                
                try:
                    # 获取打印机句柄
                    handle = win32print.OpenPrinter(printer_name)
                    
                    # 获取打印机属性
                    printer_info = win32print.GetPrinter(handle, 2)
                    
                    # 获取支持的纸张类型
                    paper_sizes = self._get_windows_paper_sizes(handle)
                    
                    printers.append({
                        'name': printer_name,
                        'driver': printer_info.get('pDriverName', ''),
                        'port': printer_info.get('pPortName', ''),
                        'status': self._get_printer_status(printer_info.get('Status', 0)),
                        'paper_sizes': paper_sizes
                    })
                    
                    win32print.ClosePrinter(handle)
                    
                except Exception as e:
                    print(f"获取打印机 {printer_name} 信息时出错: {e}")
                    printers.append({
                        'name': printer_name,
                        'driver': '',
                        'port': '',
                        'status': '未知',
                        'paper_sizes': []
                    })
            
            return printers
            
        except ImportError:
            print("Windows系统需要安装pywin32库: pip install pywin32")
            return []
        except Exception as e:
            print(f"获取Windows打印机信息时出错: {e}")
            return []
    
    def _get_windows_paper_sizes(self, printer_handle) -> List[Dict[str, Any]]:
        """获取Windows打印机支持的纸张尺寸"""
        import win32print
        
        try:
            # 获取打印机名称
            printer_info = win32print.GetPrinter(printer_handle, 2)
            printer_name = printer_info['pPrinterName']
            
            # 初始化变量
            paper_sizes = None
            paper_names = None
            paper_dimensions = None
            
            # 尝试获取纸张信息
            try:
                # DC_PAPERS = 2，使用空字符串作为端口名
                paper_sizes = win32print.DeviceCapabilities(printer_name, "", 2)
            except Exception:
                pass
                
            try:
                # DC_PAPERNAMES = 16
                paper_names = win32print.DeviceCapabilities(printer_name, "", 16)
            except Exception:
                pass
                
            try:
                # DC_PAPERSIZE = 3
                paper_dimensions = win32print.DeviceCapabilities(printer_name, "", 3)
            except Exception:
                pass
            
            # 检查是否成功获取了纸张信息
            if not paper_sizes or not paper_names or not paper_dimensions:
                return []
                
            return self._create_paper_list(paper_sizes, paper_names, paper_dimensions)
            
        except Exception:
            return []
            
    def _create_paper_list(self, paper_sizes, paper_names, paper_dimensions) -> List[Dict[str, Any]]:
        """创建纸张列表"""
        papers = []
        try:
            if paper_sizes and paper_names and paper_dimensions:
                for i, (size_id, name, dimensions) in enumerate(zip(paper_sizes, paper_names, paper_dimensions)):
                    try:
                        if isinstance(name, str):
                            name_str = name.strip('\x00')
                        else:
                            name_str = f"纸张 {size_id}"
                        
                        # 检查dimensions的格式
                        if isinstance(dimensions, dict) and 'x' in dimensions and 'y' in dimensions:
                            # Windows DeviceCapabilities 返回的格式是 {'x': width, 'y': height}
                            width = dimensions['x']
                            height = dimensions['y']
                        elif isinstance(dimensions, (list, tuple)) and len(dimensions) >= 2:
                            # 列表或元组格式
                            width = dimensions[0]
                            height = dimensions[1]
                        else:
                            continue
                            
                        papers.append({
                            "id": size_id,
                            "name": name_str,
                            "width": width,  # 单位：0.1mm
                            "height": height  # 单位：0.1mm
                        })
                    except Exception:
                        continue
                        
        except Exception:
            pass
            
        return papers
    
    def _get_macos_printers(self) -> List[Dict[str, Any]]:
        """获取macOS系统的打印机信息"""
        try:
            printer_names = CommandUtils.get_printer_list()
            printers = []
            
            for printer_name in printer_names:
                # 获取打印机详细信息
                printer_info = CommandUtils.get_printer_details(printer_name)
                
                # 获取支持的纸张类型
                paper_sizes = CommandUtils.get_paper_sizes(printer_name)
                
                printers.append({
                    'name': printer_name,
                    'driver': printer_info.get('driver', ''),
                    'uri': printer_info.get('uri', ''),
                    'status': printer_info.get('status', ''),
                    'paper_sizes': paper_sizes
                })
            
            return printers
            
        except Exception as e:
            print(f"获取macOS打印机信息时出错: {e}")
            return []
    
    def _get_printer_status(self, status_code: int) -> str:
        """将Windows打印机状态码转换为可读字符串"""
        return PrinterStatusUtils.get_status_description(status_code)
    
    def print_printer_info(self):
        """打印所有打印机信息"""
        printers = self.get_printers()
        
        if not printers:
            print("未找到任何打印机")
            return
        
        print(f"系统: {self.system}")
        print(f"找到 {len(printers)} 个打印机:\n")
        
        for i, printer in enumerate(printers, 1):
            print(f"打印机 {i}: {printer['name']}")
            print(f"  状态: {printer.get('status', '未知')}")
            
            if 'driver' in printer and printer['driver']:
                print(f"  驱动: {printer['driver']}")
            
            if 'port' in printer and printer['port']:
                print(f"  端口: {printer['port']}")
            
            if 'uri' in printer and printer['uri']:
                print(f"  URI: {printer['uri']}")
            
            paper_sizes = printer.get('paper_sizes', [])
            if paper_sizes:
                print(f"  支持的纸张类型 ({len(paper_sizes)} 种):")
                for paper in paper_sizes[:10]:  # 只显示前10种
                    if 'width_mm' in paper and 'height_mm' in paper:
                        print(f"    - {paper['name']} ({paper['width_mm']}x{paper['height_mm']}mm)")
                    else:
                        print(f"    - {paper.get('display_name', paper['name'])}")
                
                if len(paper_sizes) > 10:
                    print(f"    ... 还有 {len(paper_sizes) - 10} 种纸张类型")
            else:
                print("  支持的纸张类型: 无法获取")
            
            print()


if __name__ == "__main__":
    # 如果直接运行此文件，显示打印机信息
    printer_info = PrinterInfo()
    printer_info.print_printer_info()