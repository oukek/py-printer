# Python打印机服务 - 打包说明

本文档说明如何将Flask打印机服务应用打包为Windows和macOS的可执行文件。

## 快速开始（推荐）

### 一键打包命令

我们提供了跨平台的自动打包脚本，可以自动检测操作系统并调用相应的打包方式：

#### Windows系统
```cmd
# 方式1: 直接运行批处理文件
build.bat

# 方式2: 直接运行Python脚本
python build.py
```

#### macOS/Linux系统
```bash
# 方式1: 运行shell脚本
chmod +x build.sh
./build.sh

# 方式2: 直接运行Python脚本
python3 build.py
```

### 自动打包脚本特点

- **自动系统检测**: 自动识别Windows、macOS、Linux系统
- **环境检查**: 自动检查Python版本和pip可用性
- **依赖管理**: 自动安装所需依赖
- **智能清理**: 自动清理之前的构建文件
- **文件重命名**: 自动生成带系统标识的可执行文件名
- **使用说明**: 打包完成后显示详细的使用说明

## 手动打包方式（可选）

## 项目结构

```
py-printer/
├── app.py                 # 主入口文件
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── build.spec           # PyInstaller配置文件
├── build_windows.bat    # Windows打包脚本
├── build_macos.sh       # macOS打包脚本
├── modules/             # 应用模块
│   ├── app_module.py
│   └── printer_module.py
└── utils/               # 工具模块
    ├── command_utils.py
    ├── pdf_utils.py
    └── printer.py
```

## 环境要求

### 通用要求
- Python 3.8 或更高版本
- pip 包管理器

### Windows要求
- Windows 10 或更高版本
- PowerShell 或命令提示符

### macOS要求
- macOS 10.12 或更高版本
- Terminal 应用程序

## 生成的可执行文件

根据不同的操作系统，自动打包脚本会生成相应的可执行文件：

- **Windows**: `dist/py-server-windows-amd64.exe`
- **macOS**: `dist/py-server-macos`
- **Linux**: `dist/py-server-linux`

## 打包文件说明

项目包含以下打包相关文件：

- **<mcfile name="build.py" path="d:\code\py-printer\build.py"></mcfile>** - 跨平台Python打包脚本（核心）
- **<mcfile name="build.bat" path="d:\code\py-printer\build.bat"></mcfile>** - Windows批处理入口
- **<mcfile name="build.sh" path="d:\code\py-printer\build.sh"></mcfile>** - Unix/Linux/macOS shell入口
- **<mcfile name="build.spec" path="d:\code\py-printer\build.spec"></mcfile>** - PyInstaller配置文件
- **<mcfile name="build_windows.bat" path="d:\code\py-printer\build_windows.bat"></mcfile>** - Windows专用打包脚本（备用）
- **<mcfile name="build_macos.sh" path="d:\code\py-printer\build_macos.sh"></mcfile>** - macOS专用打包脚本（备用）

## 手动打包步骤（可选）

如果需要使用特定系统的打包脚本，可以参考以下步骤：

### Windows系统手动打包

1. **打开命令提示符或PowerShell**
   ```cmd
   cd /d "项目目录路径"
   ```

2. **运行Windows打包脚本**
   ```cmd
   build_windows.bat
   ```

3. **脚本执行过程**
   - 检查Python和pip是否安装
   - 自动安装项目依赖（包括PyInstaller）
   - 清理之前的构建文件
   - 使用PyInstaller打包应用
   - 生成可执行文件：`dist/py-server-windows-amd64.exe`

4. **运行打包后的程序**
   ```cmd
   dist\py-server-windows-amd64.exe
   ```

### macOS系统手动打包

1. **打开Terminal终端**
   ```bash
   cd "项目目录路径"
   ```

2. **给脚本添加执行权限**
   ```bash
   chmod +x build_macos.sh
   ```

3. **运行macOS打包脚本**
   ```bash
   ./build_macos.sh
   ```

4. **脚本执行过程**
   - 检查Python3和pip3是否安装
   - 自动安装项目依赖（包括PyInstaller）
   - 清理之前的构建文件
   - 使用PyInstaller打包应用
   - 生成可执行文件：`dist/py-server-macos`

5. **运行打包后的程序**
   ```bash
   ./dist/py-server-macos
   ```

## 打包配置说明

### PyInstaller配置文件 (build.spec)

配置文件包含以下重要设置：

- **入口文件**: `app.py`
- **隐藏导入**: 自动收集Flask、Flask-CORS、PIL、PyMuPDF等模块
- **数据文件**: 包含配置文件和其他必要资源
- **排除模块**: 排除不需要的大型模块（如tkinter、matplotlib等）
- **输出格式**: 单文件可执行程序

### 依赖管理

项目依赖在 `requirements.txt` 中定义：

```txt
Flask>=2.3.0
Flask-CORS>=4.0.0
pywin32>=306; sys_platform == "win32"
Pillow>=9.0.0
PyMuPDF>=1.18.0
psutil>=5.9.0
PyInstaller>=5.13.0
```

## 使用打包后的程序

### 启动服务器

1. **Windows**:
   - 双击 `dist/py-server-windows-amd64.exe`
   - 或在命令行中运行该文件

2. **macOS**:
   - 在终端中运行 `./dist/py-server-macos`

### 访问服务

服务器启动后，可以通过以下地址访问：

- 主页: http://localhost:6789
- API文档: http://localhost:6789/app/info
- 打印机接口: http://localhost:6789/printer/

### 命令行参数

可执行文件支持以下参数：

- `--debug`: 启用调试模式
- `--output-port`: 输出服务器端口信息

示例：
```bash
# Windows
dist\py-server-windows-amd64.exe --debug

# macOS
./dist/py-server-macos --debug
```

## 故障排除

### 常见问题

1. **Python未找到**
   - 确保已安装Python 3.8+
   - 检查Python是否在系统PATH中

2. **依赖安装失败**
   - 检查网络连接
   - 尝试使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

3. **打包失败**
   - 检查是否有足够的磁盘空间
   - 确保没有其他程序占用相关文件
   - 尝试以管理员权限运行打包脚本

4. **可执行文件无法运行**
   - 检查防病毒软件是否阻止了程序
   - 确保所有依赖都已正确打包
   - 查看控制台输出的错误信息

### 日志和调试

如果程序运行出现问题，可以：

1. 使用 `--debug` 参数启动程序查看详细日志
2. 检查控制台输出的错误信息
3. 确认防火墙设置允许程序访问网络

## 文件大小优化

如果生成的可执行文件过大，可以考虑：

1. 在 `build.spec` 中添加更多排除模块
2. 使用UPX压缩（已在配置中启用）
3. 移除不必要的依赖

## 分发说明

打包完成后，可以直接分发以下文件：

- **Windows**: `dist/py-server-windows-amd64.exe`
- **macOS**: `dist/py-server-macos`

这些文件是独立的可执行程序，不需要目标机器安装Python环境。