#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台自动打包脚本
自动检测操作系统并调用相应的打包方式
"""

import os
import sys
import platform
import subprocess
import shutil


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"错误: 需要Python 3.8或更高版本，当前版本: {version.major}.{version.minor}")
        return False
    print(f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True


def check_pip():
    """检查pip是否可用"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"pip检查通过: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("错误: pip不可用，请检查Python安装")
        return False


def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False


def clean_build_files():
    """清理构建文件"""
    print("正在清理之前的构建文件...")
    
    # 清理build目录
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("已清理build目录")
    
    # 清理dist目录中的可执行文件
    if os.path.exists('dist'):
        system_name = platform.system().lower()
        if system_name == 'windows':
            exe_file = 'dist/py-server.exe'
            final_file = 'dist/py-server-windows-amd64.exe'
        elif system_name == 'darwin':
            exe_file = 'dist/py-server'
            final_file = 'dist/py-server-macos'
        else:
            exe_file = 'dist/py-server'
            final_file = 'dist/py-server-linux'
        
        for file_path in [exe_file, final_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"已清理 {file_path}")


def build_with_pyinstaller():
    """使用PyInstaller打包"""
    print("正在使用PyInstaller打包应用...")
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', 'build.spec', '--clean', '--noconfirm'], 
                      check=True)
        print("PyInstaller打包成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller打包失败: {e}")
        return False


def rename_executable():
    """重命名可执行文件"""
    system_name = platform.system().lower()
    
    if system_name == 'windows':
        source = 'dist/py-server.exe'
        target = 'dist/py-server-windows-amd64.exe'
    elif system_name == 'darwin':
        source = 'dist/py-server'
        target = 'dist/py-server-macos'
    else:  # Linux或其他Unix系统
        source = 'dist/py-server'
        target = 'dist/py-server-linux'
    
    if os.path.exists(source):
        if os.path.exists(target):
            os.remove(target)
        os.rename(source, target)
        
        # 确保可执行权限（Unix系统）
        if system_name in ['darwin', 'linux']:
            os.chmod(target, 0o755)
        
        print(f"文件已重命名为: {target}")
        return target
    else:
        print(f"错误: 未找到生成的可执行文件 {source}")
        return None


def show_usage_info(executable_path):
    """显示使用说明"""
    system_name = platform.system().lower()
    
    print("=" * 50)
    print("打包成功！")
    print("=" * 50)
    print(f"可执行文件位置: {executable_path}")
    print()
    print("使用方法:")
    
    if system_name == 'windows':
        print(f"  双击运行或在命令行中执行: {executable_path}")
    else:
        print(f"  在终端中执行: ./{executable_path}")
    
    print("  服务器将在 http://localhost:6789 启动")
    print()
    print("命令行参数:")
    print("  --debug: 启用调试模式")
    print("  --output-port: 输出服务器端口信息")
    print()
    
    # 显示文件信息
    if os.path.exists(executable_path):
        file_size = os.path.getsize(executable_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"文件大小: {file_size_mb:.1f} MB")


def main():
    """主函数"""
    print("=" * 50)
    print("Python打印机服务 - 跨平台自动打包脚本")
    print("=" * 50)
    
    # 检测操作系统
    system_name = platform.system()
    print(f"检测到操作系统: {system_name}")
    
    # 检查环境
    if not check_python_version():
        return 1
    
    if not check_pip():
        return 1
    
    # 安装依赖
    if not install_dependencies():
        return 1
    
    # 清理构建文件
    clean_build_files()
    
    # 执行打包
    if not build_with_pyinstaller():
        return 1
    
    # 重命名可执行文件
    executable_path = rename_executable()
    if not executable_path:
        return 1
    
    # 清理临时文件
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("已清理临时文件")
    
    # 显示使用说明
    show_usage_info(executable_path)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"发生未预期的错误: {e}")
        sys.exit(1)