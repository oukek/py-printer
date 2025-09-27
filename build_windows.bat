@echo off
REM Windows打包脚本
REM 用于将Flask服务应用打包为Windows可执行文件

echo ========================================
echo Python服务 - Windows打包脚本
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查pip是否可用
pip --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到pip，请检查Python安装
    pause
    exit /b 1
)

echo 正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo 正在清理之前的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist\py-server.exe" del "dist\py--server.exe"

echo 正在使用PyInstaller打包应用...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

REM 检查生成的可执行文件
if exist "dist\py-server.exe" (
    echo ========================================
    echo 打包成功！
    echo 可执行文件位置: dist\py-server.exe
    echo ========================================
    
    REM 重命名为更具体的名称
    if exist "dist\py-server-windows-amd64.exe" del "dist\py-server-windows-amd64.exe"
    ren "dist\py-server.exe" "py-server-windows-amd64.exe"
    
    echo 文件已重命名为: dist\py-server-windows-amd64.exe
    echo.
    echo 使用方法:
    echo   双击运行或在命令行中执行: dist\py-server-windows-amd64.exe
    echo   服务器将在 http://localhost:6789 启动
    echo.
) else (
    echo 错误: 未找到生成的可执行文件
    exit /b 1
)

echo 清理临时文件...
if exist "build" rmdir /s /q "build"

echo 打包完成！
pause