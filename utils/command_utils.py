#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行工具类
提供跨平台的命令执行和打印相关的通用功能
"""

import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple


class CommandUtils:
    """命令行工具类"""
    
    @staticmethod
    def run_command(cmd: List[str], capture_output: bool = True, text: bool = True) -> subprocess.CompletedProcess:
        """
        执行命令行命令
        
        Args:
            cmd: 命令列表
            capture_output: 是否捕获输出
            text: 是否以文本模式处理输出
            
        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        try:
            return subprocess.run(cmd, capture_output=capture_output, text=text)
        except Exception as e:
            print(f"执行命令时出错: {e}")
            # 返回一个模拟的失败结果
            result = subprocess.CompletedProcess(cmd, 1, '', str(e))
            return result
    
    @staticmethod
    def build_print_command(printer_name: Optional[str] = None, 
                           paper_size: Optional[str] = None,
                           file_path: Optional[str] = None) -> List[str]:
        """
        构建打印命令（适用于macOS和Linux）
        
        Args:
            printer_name: 打印机名称
            paper_size: 纸张大小
            file_path: 文件路径
            
        Returns:
            List[str]: 命令列表
        """
        cmd = ['lp']
        
        # 添加打印机参数
        if printer_name:
            cmd.extend(['-d', printer_name])
            
        # 添加纸张大小参数
        if paper_size:
            cmd.extend(['-o', f'media={paper_size}'])
            
        # 添加文件路径
        if file_path:
            cmd.append(file_path)
            
        return cmd
    
    @staticmethod
    def get_printer_list() -> List[str]:
        """
        获取打印机列表（适用于macOS和Linux）
        
        Returns:
            List[str]: 打印机名称列表
        """
        try:
            result = CommandUtils.run_command(['lpstat', '-p'])
            if result.returncode != 0:
                return []
            
            printers = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line.startswith('printer '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 2:
                        printers.append(parts[1])
            
            return printers
            
        except Exception as e:
            print(f"获取打印机列表时出错: {e}")
            return []
    
    @staticmethod
    def get_printer_details(printer_name: str) -> Dict[str, str]:
        """
        获取打印机详细信息（适用于macOS和Linux）
        
        Args:
            printer_name: 打印机名称
            
        Returns:
            Dict[str, str]: 打印机详细信息
        """
        try:
            result = CommandUtils.run_command(['lpstat', '-l', '-p', printer_name])
            
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
    
    @staticmethod
    def get_paper_sizes(printer_name: str) -> List[Dict[str, Any]]:
        """
        获取打印机支持的纸张尺寸（适用于macOS和Linux）
        
        Args:
            printer_name: 打印机名称
            
        Returns:
            List[Dict[str, Any]]: 纸张尺寸列表
        """
        try:
            result = CommandUtils.run_command(['lpoptions', '-p', printer_name, '-l'])
            
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


class PrinterStatusUtils:
    """打印机状态工具类"""
    
    @staticmethod
    def get_status_description(status_code: int) -> str:
        """
        将Windows打印机状态码转换为可读字符串
        
        Args:
            status_code: 状态码
            
        Returns:
            str: 状态描述
        """
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


class PlatformUtils:
    """平台工具类"""
    
    @staticmethod
    def get_system() -> str:
        """获取当前操作系统"""
        return platform.system()
    
    @staticmethod
    def is_windows() -> bool:
        """是否为Windows系统"""
        return platform.system() == 'Windows'
    
    @staticmethod
    def is_macos() -> bool:
        """是否为macOS系统"""
        return platform.system() == 'Darwin'
    
    @staticmethod
    def is_linux() -> bool:
        """是否为Linux系统"""
        return platform.system() == 'Linux'
    
    @staticmethod
    def get_supported_platforms() -> List[str]:
        """获取支持的平台列表"""
        return ['Windows', 'Darwin', 'Linux']
    
    @staticmethod
    def check_platform_support() -> bool:
        """检查当前平台是否支持"""
        return PlatformUtils.get_system() in PlatformUtils.get_supported_platforms()