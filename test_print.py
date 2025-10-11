#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 打印1.pdf文件
"""

import os
import sys
from utils.printer import PrinterInfo


def test_print_pdf():
    """测试打印PDF文件"""
    
    # PDF文件路径
    pdf_file = "1.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        print(f"错误: 文件 {pdf_file} 不存在")
        return False
    
    print(f"准备打印文件: {pdf_file}")
    
    # 创建打印机实例
    printer_info = PrinterInfo()
    
    # 获取可用打印机列表
    print("\n获取可用打印机列表...")
    try:
        printers = printer_info.get_printers()
        if not printers:
            print("错误: 没有找到可用的打印机")
            return False
        
        print(f"找到 {len(printers)} 个打印机:")
        for i, printer in enumerate(printers):
            status = "默认" if printer.get('is_default', False) else "可用"
            print(f"  {i+1}. {printer['name']} ({status})")
            
    except Exception as e:
        print(f"获取打印机列表失败: {e}")
        return False
    
    # 指定使用Q5BT打印机
    target_printer = "Q5BT"
    selected_printer = None
    
    # 查找指定的打印机
    for printer in printers:
        if printer['name'] == target_printer:
            selected_printer = printer['name']
            break
    
    if not selected_printer:
        print(f"错误: 未找到指定的打印机 '{target_printer}'")
        print("可用的打印机:")
        for printer in printers:
            print(f"  - {printer['name']}")
        return False
    
    print(f"\n使用打印机: {selected_printer}")
    
    # 执行打印
    print(f"开始打印 {pdf_file}...")
    try:
        success = printer_info.print_file(pdf_file, selected_printer)
        
        if success:
            print("✓ 打印任务已成功发送到打印机")
            return True
        else:
            print("✗ 打印失败")
            return False
            
    except Exception as e:
        print(f"打印过程中出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("PDF打印测试脚本")
    print("=" * 50)
    
    # 执行测试
    success = test_print_pdf()
    
    print("\n" + "=" * 50)
    if success:
        print("测试完成: 打印任务已发送")
    else:
        print("测试失败: 打印任务未能成功发送")
    print("=" * 50)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())