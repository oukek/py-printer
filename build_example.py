#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包和使用示例
演示如何打包成可执行文件并获取端口
"""

import os
import subprocess
import sys

def build_executable():
    """使用PyInstaller打包成可执行文件"""
    print("🔨 开始打包...")
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',           # 打包成单个文件
        '--name=printer-server', # 可执行文件名
        '--add-data=printer.py:.',  # 包含printer.py
        'server.py'            # 主文件
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 打包成功！")
        print(f"📦 可执行文件位置: ./dist/printer-server")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def demo_usage():
    """演示如何使用可执行文件"""
    executable_path = "./dist/printer-server"
    
    if not os.path.exists(executable_path):
        print(f"❌ 可执行文件不存在: {executable_path}")
        print("请先运行打包命令")
        return
    
    print("\n🚀 演示可执行文件使用...")
    
    # 方法1: 直接运行并解析输出
    print("\n方法1: 解析标准输出获取端口")
    try:
        process = subprocess.Popen(
            [executable_path, '--output-port'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 读取输出
        for line in process.stdout:
            print(f"输出: {line.strip()}")
            if line.startswith("PORT:"):
                port = line.split(":")[1].strip()
                print(f"🎯 获取到端口: {port}")
                break
        
        # 终止进程
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"❌ 方法1失败: {e}")
    
    # 方法2: 使用端口读取器
    print("\n方法2: 使用端口读取器")
    print("可以使用 port_reader.py 来自动处理")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        # 打包
        if build_executable():
            print("\n📋 使用说明:")
            print("1. 直接运行: ./dist/printer-server")
            print("2. 获取端口: ./dist/printer-server --output-port")
            print("3. 在代码中使用: python port_reader.py")
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 演示使用
        demo_usage()
    else:
        print("使用方法:")
        print("  python build_example.py build  # 打包成可执行文件")
        print("  python build_example.py demo   # 演示使用方法")