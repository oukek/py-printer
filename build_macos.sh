#!/bin/bash
# macOS打包脚本
# 用于将Flask服务应用打包为macOS可执行文件

echo "========================================"
echo "Python服务 - macOS打包脚本"
echo "========================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查pip是否可用
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请检查Python安装"
    exit 1
fi

echo "Python版本:"
python3 --version

echo "正在安装依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo "正在清理之前的构建文件..."
rm -rf build/
rm -f dist/py-server

echo "正在使用PyInstaller打包应用..."
python3 -m PyInstaller build.spec --clean --noconfirm
if [ $? -ne 0 ]; then
    echo "错误: 打包失败"
    exit 1
fi

# 检查生成的可执行文件
if [ -f "dist/py-server" ]; then
    echo "========================================"
    echo "打包成功！"
    echo "可执行文件位置: dist/py-server"
    echo "========================================"
    
    # 重命名为更具体的名称
    mv "dist/py-server" "dist/py-server-macos"
    
    # 确保可执行权限
    chmod +x "dist/py-server-macos"
    
    echo "文件已重命名为: dist/py-server-macos"
    echo ""
    echo "使用方法:"
    echo "  在终端中执行: ./dist/py-server-macos"
    echo "  或者双击运行（如果系统允许）"
    echo "  服务器将在 http://localhost:6789 启动"
    echo ""
    
    # 显示文件信息
    echo "文件信息:"
    ls -la "dist/py-server-macos"
    echo ""
else
    echo "错误: 未找到生成的可执行文件"
    exit 1
fi

echo "清理临时文件..."
rm -rf build/

echo "打包完成！"

echo "macOS可执行文件打包完成！"
echo "可执行文件位置: dist/py-server-macos"