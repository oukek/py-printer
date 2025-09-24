#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机信息获取工具
获取系统中的打印机列表和每个打印机支持的纸张类型
支持PDF和图片打印功能
"""

import platform
import subprocess
import json
import os
import base64
import tempfile
from typing import List, Dict, Any, Optional

# 条件导入Windows相关模块
if platform.system() == 'Windows':
    try:
        import win32con
    except ImportError:
        win32con = None
        print("Windows系统需要安装pywin32库: pip install pywin32")
else:
    win32con = None

# 导入图像和PDF处理库
from PIL import Image
try:
    from pdf2image import convert_from_path, convert_from_bytes
except ImportError:
    print("PDF功能需要安装pdf2image库: pip install pdf2image")
    # 如果没有安装pdf2image，程序仍然可以运行，但PDF功能不可用


class PrinterInfo:
    """打印机信息类"""
    
    def __init__(self):
        self.system = platform.system()
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """
        获取系统中所有打印机的信息
        
        Returns:
            List[Dict]: 包含打印机信息的列表
        """
        
    def print_file(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        打印文件（支持PDF和图片）
        
        Args:
            file_path: 要打印的文件路径
            printer_name: 打印机名称，如果为None则使用默认打印机
            
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
            return self._print_pdf(file_path, printer_name)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
            return self._print_image(file_path, printer_name)
        else:
            print(f"不支持的文件类型: {file_ext}")
            return False
            
    def print_data(self, data: str, file_type: str, printer_name: Optional[str] = None) -> bool:
        """
        打印Base64编码的数据或文件路径
        
        Args:
            data: Base64编码的数据或文件路径
            file_type: 文件类型，如'pdf'、'jpg'等
            printer_name: 打印机名称，如果为None则使用默认打印机
            
        Returns:
            bool: 打印是否成功
        """
        # 检查是否是文件路径
        if os.path.exists(data):
            return self.print_file(data, printer_name)
            
        # 尝试解码Base64数据
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as temp_file:
                temp_path = temp_file.name
                
                # 解码Base64数据并写入临时文件
                file_data = base64.b64decode(data)
                temp_file.write(file_data)
                
            # 打印临时文件
            result = self.print_file(temp_path, printer_name)
            
            # 删除临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return result
            
        except Exception as e:
            print(f"处理Base64数据时出错: {e}")
            return False
    
    def _print_pdf(self, pdf_path: str, printer_name: Optional[str] = None) -> bool:
        """
        打印PDF文件
        """
        try:
            # 检查pdf2image是否可用
            if 'convert_from_path' not in globals():
                print("错误: 缺少pdf2image库，无法打印PDF文件")
                return False
                
            # 将PDF转换为图像
            images = convert_from_path(pdf_path)
            
            # 创建临时目录保存图像
            with tempfile.TemporaryDirectory() as temp_dir:
                image_paths = []
                
                # 保存每一页为图像
                for i, image in enumerate(images):
                    image_path = os.path.join(temp_dir, f"page_{i+1}.png")
                    image.save(image_path, "PNG")
                    image_paths.append(image_path)
                
                # 打印每一页
                success = True
                for image_path in image_paths:
                    if not self._print_image(image_path, printer_name):
                        success = False
                        
                return success
                
        except Exception as e:
            print(f"打印PDF时出错: {e}")
            return False
    
    def _print_image(self, image_path: str, printer_name: Optional[str] = None) -> bool:
        """
        打印图像文件
        """
        try:
            # 打开图像
            image = Image.open(image_path)
            
            if self.system == "Windows":
                return self._print_image_windows(image, printer_name)
            elif self.system == "Darwin":  # macOS
                return self._print_image_macos(image_path, printer_name)
            elif self.system == "Linux":
                return self._print_image_linux(image_path, printer_name)
            else:
                print(f"不支持的操作系统: {self.system}")
                return False
                
        except Exception as e:
            print(f"打印图像时出错: {e}")
            return False
    
    def _print_image_windows(self, image: Image.Image, printer_name: Optional[str] = None) -> bool:
        """
        在Windows上打印图像
        """
        try:
            import win32print
            import win32ui
            from PIL import ImageWin
            
            # 获取打印机设备上下文
            if printer_name is None:
                printer_name = win32print.GetDefaultPrinter()
                
            # 创建设备上下文
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            
            # 开始文档打印
            hDC.StartDoc("图像打印")
            hDC.StartPage()
            
            # 获取打印机分辨率
            # 使用常量值代替win32con，避免跨平台问题
            dpi_x = hDC.GetDeviceCaps(88)  # LOGPIXELSX = 88
            dpi_y = hDC.GetDeviceCaps(90)  # LOGPIXELSY = 90
            
            # 计算打印尺寸（英寸）
            width_inch = image.width / dpi_x
            height_inch = image.height / dpi_y
            
            # 打印图像
            ImageWin.Dib(image).draw(hDC.GetHandleOutput(), 
                                    (0, 0, int(width_inch * dpi_x), int(height_inch * dpi_y)))
            
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
    
    def _print_image_macos(self, image_path: str, printer_name: Optional[str] = None) -> bool:
        """
        在macOS上打印图像
        """
        try:
            cmd = ['lp']
            
            # 如果指定了打印机，添加打印机参数
            if printer_name:
                cmd.extend(['-d', printer_name])
                
            # 添加文件路径
            cmd.append(image_path)
            
            # 执行打印命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"打印失败: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"macOS打印图像时出错: {e}")
            return False
    
    def _print_image_linux(self, image_path: str, printer_name: Optional[str] = None) -> bool:
        """
        在Linux上打印图像
        """
        try:
            cmd = ['lp']
            
            # 如果指定了打印机，添加打印机参数
            if printer_name:
                cmd.extend(['-d', printer_name])
                
            # 添加文件路径
            cmd.append(image_path)
            
            # 执行打印命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
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
        try:
            import win32print
            
            # 获取打印机名称
            printer_info = win32print.GetPrinter(printer_handle, 2)
            printer_name = printer_info['pPrinterName']
            
            # 尝试不同的方式获取纸张尺寸
            try:
                # 方法1：使用打印机名称和空端口名
                # 使用常量值代替win32con，避免跨平台问题
                paper_sizes = win32print.DeviceCapabilities(printer_name, "", 24, None)  # DC_PAPERS = 24
                paper_names = win32print.DeviceCapabilities(printer_name, "", 16, None)  # DC_PAPERNAMES = 16
                paper_dimensions = win32print.DeviceCapabilities(printer_name, "", 3, None)  # DC_PAPERSIZE = 3
                
                # 如果返回0，尝试使用默认纸张尺寸
                if not paper_sizes or paper_sizes == 0:
                    # 常见纸张尺寸ID和名称
                    paper_sizes = [1, 9]  # 1=Letter, 9=A4
                    paper_names = ["Letter", "A4"]
                    paper_dimensions = [[2159, 2794], [2100, 2970]]  # 单位：0.1mm
            except Exception:
                # 使用默认纸张尺寸
                paper_sizes = [1, 9]  # 1=Letter, 9=A4
                paper_names = ["Letter", "A4"]
                paper_dimensions = [[2159, 2794], [2100, 2970]]  # 单位：0.1mm
            
            papers = []
            if paper_sizes and paper_names and paper_dimensions:
                for i, (size_id, name, dimensions) in enumerate(zip(paper_sizes, paper_names, paper_dimensions)):
                    if isinstance(name, str):
                        name_str = name.strip('\x00')
                    else:
                        name_str = f"纸张 {size_id}"
                        
                    papers.append({
                        'id': size_id,
                        'name': name_str,
                        'width_mm': dimensions[0] / 10 if isinstance(dimensions, list) else 210,  # 默认A4宽度
                        'height_mm': dimensions[1] / 10 if isinstance(dimensions, list) else 297   # 默认A4高度
                    })
            
            return papers
            
        except Exception:
            # 返回一些默认的纸张尺寸
            return [
                {'id': 1, 'name': 'Letter', 'width_mm': 215.9, 'height_mm': 279.4},
                {'id': 9, 'name': 'A4', 'width_mm': 210.0, 'height_mm': 297.0}
            ]
    
    def _get_macos_printers(self) -> List[Dict[str, Any]]:
        """获取macOS系统的打印机信息"""
        try:
            # 使用lpstat命令获取打印机列表
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode != 0:
                print("无法获取打印机列表")
                return []
            
            printers = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line.startswith('printer '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        
                        # 获取打印机详细信息
                        printer_info = self._get_macos_printer_details(printer_name)
                        
                        # 获取支持的纸张类型
                        paper_sizes = self._get_macos_paper_sizes(printer_name)
                        
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
    
    def _get_macos_printer_details(self, printer_name: str) -> Dict[str, str]:
        """获取macOS打印机详细信息"""
        try:
            result = subprocess.run(['lpstat', '-l', '-p', printer_name], 
                                  capture_output=True, text=True)
            
            info = {}
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Interface:' in line:
                        info['uri'] = line.split('Interface:')[1].strip()
                    elif 'enabled' in line or 'disabled' in line:
                        info['status'] = 'enabled' if 'enabled' in line else 'disabled'
            
            return info
            
        except Exception as e:
            print(f"获取打印机详细信息时出错: {e}")
            return {}
    
    def _get_macos_paper_sizes(self, printer_name: str) -> List[Dict[str, Any]]:
        """获取macOS打印机支持的纸张尺寸"""
        try:
            # 使用lpoptions获取打印机选项
            result = subprocess.run(['lpoptions', '-p', printer_name, '-l'], 
                                  capture_output=True, text=True)
            
            papers = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('PageSize/'):
                        # 解析纸张尺寸选项
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            size_info = parts[0].replace('PageSize/', '')
                            options = parts[1].strip().split(' ')
                            
                            for option in options:
                                if option and not option.startswith('*'):
                                    papers.append({
                                        'name': option,
                                        'display_name': option.replace('_', ' ')
                                    })
            
            # 如果没有获取到纸张信息，添加常见的纸张类型
            if not papers:
                papers = [
                    {'name': 'A4', 'display_name': 'A4'},
                    {'name': 'Letter', 'display_name': 'Letter'},
                    {'name': 'Legal', 'display_name': 'Legal'}
                ]
            
            return papers
            
        except Exception as e:
            print(f"获取纸张尺寸时出错: {e}")
            return []
    
    def _get_linux_printers(self) -> List[Dict[str, Any]]:
        """获取Linux系统的打印机信息"""
        try:
            # 使用lpstat命令获取打印机列表
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode != 0:
                print("无法获取打印机列表，请确保CUPS服务正在运行")
                return []
            
            printers = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line.startswith('printer '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 2:
                        printer_name = parts[1]
                        
                        # 获取打印机详细信息
                        printer_info = self._get_linux_printer_details(printer_name)
                        
                        # 获取支持的纸张类型
                        paper_sizes = self._get_linux_paper_sizes(printer_name)
                        
                        printers.append({
                            'name': printer_name,
                            'driver': printer_info.get('driver', ''),
                            'uri': printer_info.get('uri', ''),
                            'status': printer_info.get('status', ''),
                            'paper_sizes': paper_sizes
                        })
            
            return printers
            
        except Exception as e:
            print(f"获取Linux打印机信息时出错: {e}")
            return []
    
    def _get_linux_printer_details(self, printer_name: str) -> Dict[str, str]:
        """获取Linux打印机详细信息"""
        try:
            result = subprocess.run(['lpstat', '-l', '-p', printer_name], 
                                  capture_output=True, text=True)
            
            info = {}
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Interface:' in line:
                        info['uri'] = line.split('Interface:')[1].strip()
                    elif 'enabled' in line or 'disabled' in line:
                        info['status'] = 'enabled' if 'enabled' in line else 'disabled'
            
            return info
            
        except Exception as e:
            print(f"获取打印机详细信息时出错: {e}")
            return {}
    
    def _get_linux_paper_sizes(self, printer_name: str) -> List[Dict[str, Any]]:
        """获取Linux打印机支持的纸张尺寸"""
        try:
            # 使用lpoptions获取打印机选项
            result = subprocess.run(['lpoptions', '-p', printer_name, '-l'], 
                                  capture_output=True, text=True)
            
            papers = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('PageSize/'):
                        # 解析纸张尺寸选项
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            options = parts[1].strip().split(' ')
                            
                            for option in options:
                                if option and not option.startswith('*'):
                                    papers.append({
                                        'name': option,
                                        'display_name': option.replace('_', ' ')
                                    })
            
            # 如果没有获取到纸张信息，添加常见的纸张类型
            if not papers:
                papers = [
                    {'name': 'A4', 'display_name': 'A4'},
                    {'name': 'Letter', 'display_name': 'Letter'},
                    {'name': 'Legal', 'display_name': 'Legal'}
                ]
            
            return papers
            
        except Exception as e:
            print(f"获取纸张尺寸时出错: {e}")
            return []
    
    def _get_printer_status(self, status_code: int) -> str:
        """将Windows打印机状态码转换为可读字符串"""
        status_map = {
            0: '就绪',
            1: '暂停',
            2: '错误',
            3: '正在删除',
            4: '纸张卡住',
            5: '缺纸',
            6: '需要手动送纸',
            7: '纸张问题',
            8: '离线',
            9: '输入/输出活动',
            10: '忙碌',
            11: '正在打印',
            12: '输出纸盒已满',
            13: '不可用',
            14: '等待',
            15: '正在处理',
            16: '正在初始化',
            17: '正在预热',
            18: '墨粉不足',
            19: '无墨粉',
            20: '页面错误',
            21: '用户干预',
            22: '内存不足',
            23: '门开启'
        }
        return status_map.get(status_code, f'未知状态({status_code})')
    
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


def main():
    """主函数"""
    print("打印机信息获取工具")
    print("=" * 50)
    
    try:
        printer_info = PrinterInfo()
        printer_info.print_printer_info()
        
        # 可选：将信息保存为JSON文件
        save_to_file = input("\n是否将打印机信息保存到文件? (y/n): ").lower().strip()
        if save_to_file == 'y':
            printers = printer_info.get_printers()
            with open('printer_info.json', 'w', encoding='utf-8') as f:
                json.dump(printers, f, ensure_ascii=False, indent=2)
            print("打印机信息已保存到 printer_info.json")
        
    except Exception as e:
        print(f"程序运行出错: {e}")


if __name__ == "__main__":
    main()