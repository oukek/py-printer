#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包和使用示例
演示如何打包成可执行文件并获取端口
"""

import os
import subprocess
import sys
import platform

def build_executable():
    """使用PyInstaller打包成可执行文件"""
    print("🔨 开始打包...")
    
    # 获取平台信息
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # 根据平台设置文件名和数据分隔符
    if system == "windows":
        executable_name = f"py-server-windows-{arch}.exe"
        data_separator = ";"
    elif system == "darwin":  # macOS
        executable_name = f"py-server-macos-{arch}"
        data_separator = ":"
    else:  # Linux and others
        executable_name = f"py-server-linux-{arch}"
        data_separator = ":"
    
    # PyInstaller命令
    cmd = [
        'python', '-m', 'PyInstaller',
        '--onefile',           # 打包成单个文件
        f'--name={executable_name}', # 平台特定的可执行文件名
        f'--add-data=printer.py{data_separator}.',  # 包含printer.py (平台特定分隔符)
        'server.py'            # 主文件
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 打包成功！")
        print(f"📦 可执行文件位置: ./dist/{executable_name}")
        print(f"🖥️  平台: {system.title()} ({arch})")
        return executable_name
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None

def demo_usage():
    """演示如何使用可执行文件"""
    # 获取平台信息以确定可执行文件名
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if system == "windows":
        executable_name = f"py-server-windows-{arch}.exe"
    elif system == "darwin":  # macOS
        executable_name = f"py-server-macos-{arch}"
    else:  # Linux and others
        executable_name = f"py-server-linux-{arch}"
    
    executable_path = f"./dist/{executable_name}"
    
    if not os.path.exists(executable_path):
        print(f"❌ 可执行文件不存在: {executable_path}")
        print("请先运行打包命令")
        return
    
    print(f"\n🚀 演示可执行文件使用... ({system.title()} {arch})")
    
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
        executable_name = build_executable()
        if executable_name:
            print("\n📋 使用说明:")
            print(f"1. 直接运行: ./dist/{executable_name}")
            print(f"2. 获取端口: ./dist/{executable_name} --output-port")
            print("3. 在代码中使用: python port_reader.py")
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 演示使用
        demo_usage()
    else:
        print("使用方法:")
        print("  python build_example.py build  # 打包成可执行文件")
        print("  python build_example.py demo   # 演示使用方法")