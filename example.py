#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印机信息获取示例程序
演示如何使用PrinterInfo类获取打印机和纸张信息
"""

from printer_info import PrinterInfo
import json


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建PrinterInfo实例
    printer_info = PrinterInfo()
    
    # 获取所有打印机信息
    printers = printer_info.get_printers()
    
    print(f"找到 {len(printers)} 个打印机:")
    for printer in printers:
        print(f"- {printer['name']}")
    
    print()


def example_detailed_info():
    """详细信息示例"""
    print("=== 详细信息示例 ===")
    
    printer_info = PrinterInfo()
    printers = printer_info.get_printers()
    
    if not printers:
        print("未找到任何打印机")
        return
    
    # 显示第一个打印机的详细信息
    first_printer = printers[0]
    print(f"打印机名称: {first_printer['name']}")
    print(f"状态: {first_printer.get('status', '未知')}")
    
    if 'driver' in first_printer:
        print(f"驱动程序: {first_printer['driver']}")
    
    if 'port' in first_printer:
        print(f"端口: {first_printer['port']}")
    
    if 'uri' in first_printer:
        print(f"URI: {first_printer['uri']}")
    
    # 显示支持的纸张类型
    paper_sizes = first_printer.get('paper_sizes', [])
    if paper_sizes:
        print(f"\n支持的纸张类型 ({len(paper_sizes)} 种):")
        for paper in paper_sizes:
            if 'width_mm' in paper and 'height_mm' in paper:
                print(f"  {paper['name']}: {paper['width_mm']}x{paper['height_mm']}mm")
            else:
                print(f"  {paper.get('display_name', paper['name'])}")
    
    print()


def example_filter_printers():
    """筛选打印机示例"""
    print("=== 筛选打印机示例 ===")
    
    printer_info = PrinterInfo()
    printers = printer_info.get_printers()
    
    # 筛选可用的打印机
    available_printers = []
    for printer in printers:
        status = printer.get('status', '').lower()
        if 'ready' in status or 'enabled' in status or '就绪' in status:
            available_printers.append(printer)
    
    print(f"可用的打印机 ({len(available_printers)} 个):")
    for printer in available_printers:
        print(f"- {printer['name']} ({printer.get('status', '未知')})")
    
    print()


def example_paper_size_analysis():
    """纸张尺寸分析示例"""
    print("=== 纸张尺寸分析示例 ===")
    
    printer_info = PrinterInfo()
    printers = printer_info.get_printers()
    
    # 统计所有打印机支持的纸张类型
    all_paper_types = set()
    for printer in printers:
        paper_sizes = printer.get('paper_sizes', [])
        for paper in paper_sizes:
            paper_name = paper.get('display_name', paper.get('name', ''))
            if paper_name:
                all_paper_types.add(paper_name)
    
    print(f"所有打印机支持的纸张类型 ({len(all_paper_types)} 种):")
    for paper_type in sorted(all_paper_types):
        print(f"- {paper_type}")
    
    # 找出支持A4纸张的打印机
    a4_printers = []
    for printer in printers:
        paper_sizes = printer.get('paper_sizes', [])
        for paper in paper_sizes:
            paper_name = paper.get('display_name', paper.get('name', '')).lower()
            if 'a4' in paper_name:
                a4_printers.append(printer['name'])
                break
    
    print(f"\n支持A4纸张的打印机 ({len(a4_printers)} 个):")
    for printer_name in a4_printers:
        print(f"- {printer_name}")
    
    print()


def example_save_to_json():
    """保存到JSON文件示例"""
    print("=== 保存到JSON文件示例 ===")
    
    printer_info = PrinterInfo()
    printers = printer_info.get_printers()
    
    # 保存完整信息到JSON文件
    with open('all_printers.json', 'w', encoding='utf-8') as f:
        json.dump(printers, f, ensure_ascii=False, indent=2)
    
    print("完整打印机信息已保存到 all_printers.json")
    
    # 保存简化信息到JSON文件
    simplified_info = []
    for printer in printers:
        simplified_info.append({
            'name': printer['name'],
            'status': printer.get('status', '未知'),
            'paper_count': len(printer.get('paper_sizes', []))
        })
    
    with open('printers_summary.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_info, f, ensure_ascii=False, indent=2)
    
    print("简化打印机信息已保存到 printers_summary.json")
    print()


def example_find_printer_by_name():
    """根据名称查找打印机示例"""
    print("=== 根据名称查找打印机示例 ===")
    
    printer_info = PrinterInfo()
    printers = printer_info.get_printers()
    
    if not printers:
        print("未找到任何打印机")
        return
    
    # 假设要查找包含"PDF"的打印机
    search_term = "PDF"
    found_printers = []
    
    for printer in printers:
        if search_term.lower() in printer['name'].lower():
            found_printers.append(printer)
    
    if found_printers:
        print(f"找到包含'{search_term}'的打印机 ({len(found_printers)} 个):")
        for printer in found_printers:
            print(f"- {printer['name']}")
            paper_count = len(printer.get('paper_sizes', []))
            print(f"  支持 {paper_count} 种纸张类型")
    else:
        print(f"未找到包含'{search_term}'的打印机")
    
    print()


def main():
    """主函数 - 运行所有示例"""
    print("打印机信息获取示例程序")
    print("=" * 60)
    
    try:
        # 运行各种示例
        example_basic_usage()
        example_detailed_info()
        example_filter_printers()
        example_paper_size_analysis()
        example_save_to_json()
        example_find_printer_by_name()
        
        print("所有示例运行完成!")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()