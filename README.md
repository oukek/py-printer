# 打印机服务系统

一个完整的跨平台打印机服务系统，包含Python后端服务和Node.js客户端，支持HTTP API调用和可执行文件部署。

## 🚀 项目概述

本项目提供了一套完整的打印机管理解决方案：

- **Python核心库**: 跨平台的打印机信息获取和打印功能
- **HTTP服务器**: 基于Python的RESTful API服务
- **可执行文件**: 打包好的独立服务程序
- **Node.js客户端**: 用于调用服务的JavaScript客户端
- **自动端口检测**: 避免端口冲突的智能端口分配

## 📁 项目结构

```
py-printer/
├── printer.py          # 核心打印机功能库
├── server.py           # HTTP服务器
├── dist/
│   └── printer-server  # 打包好的可执行文件
├── node/               # Node.js客户端
│   ├── index.js        # 主客户端类
│   ├── test.js         # 测试脚本
│   └── package.json    # 项目配置
├── build_example.py    # 打包示例
├── port_reader.py      # 端口读取示例
└── electron_example.py # Electron集成示例
```

## ✨ 功能特性

### 核心功能
- 🖨️ 获取系统中所有打印机的列表
- 📄 获取每个打印机支持的纸张类型和尺寸
- 🖨️ 支持文件打印和数据打印
- 🔄 跨平台支持（Windows、macOS、Linux）

### 服务特性
- 🌐 HTTP RESTful API服务
- 🔌 自动端口检测，避免端口冲突
- 📦 可执行文件部署，无需Python环境
- ⚡ 高性能异步处理
- 🛡️ 完善的错误处理机制

### 客户端特性
- 📱 Node.js客户端支持
- ⏱️ 详细的执行时长统计
- 🔄 自动服务启动和管理
- 🧪 完整的测试套件
- 📊 性能监控和报告

## 🎯 支持的操作系统

- **Windows**: 使用Windows API获取详细的打印机信息
- **macOS**: 使用CUPS命令行工具获取打印机信息
- **Linux**: 使用CUPS命令行工具获取打印机信息

## 📦 安装和部署

### 方式1: 直接使用可执行文件（推荐）

```bash
# 直接运行服务
./dist/printer-server

# 获取端口信息
./dist/printer-server --output-port
```

### 方式2: Python环境运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动HTTP服务
python server.py

# 或直接使用核心库
python printer.py
```

### 方式3: Node.js客户端

```bash
cd node
npm install
node index.js  # 基本使用
node test.js   # 完整测试
```

## 🔧 API 接口文档

### 基础信息

- **服务地址**: `http://localhost:6789` (默认端口，支持自动端口检测)
- **内容类型**: `application/json`
- **响应格式**: 统一JSON格式，包含 `success` 字段表示操作结果

### 根路径接口

#### `GET /`
获取API说明和所有可用端点列表

**响应示例**:
```json
{
  "message": "打印机服务API",
  "version": "2.0.0",
  "modules": {
    "app": {
      "prefix": "/app",
      "description": "应用控制模块",
      "endpoints": {
        "/app/info": "获取应用信息 (GET)",
        "/app/shutdown": "关闭服务器 (GET)",
        "/app/health": "健康检查 (GET)",
        "/app/status": "获取服务器状态 (GET)"
      }
    },
    "printer": {
      "prefix": "/printer",
      "description": "打印机模块",
      "endpoints": {
        "/printer/list": "获取打印机列表 (GET)",
        "/printer/print/file": "打印文件 (POST)",
        "/printer/print/data": "打印数据 (POST)",
        "/printer/default": "获取默认打印机 (GET)",
        "/printer/status/<printer_name>": "获取指定打印机状态 (GET)",
        "/printer/test": "测试打印机连接 (POST)"
      }
    }
  }
}
```

---

### 应用控制模块 (`/app`)

#### `GET /app/info`
获取应用基本信息

**响应示例**:
```json
{
  "name": "打印机服务API",
  "version": "2.0.0",
  "status": "running",
  "host": "localhost",
  "port": 6789,
  "debug": false,
  "success": true
}
```

#### `GET /app/shutdown`
关闭服务器

**响应示例**:
```json
{
  "message": "服务器正在关闭...",
  "success": true
}
```

#### `GET /app/health`
健康检查接口

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "success": true
}
```

#### `GET /app/status`
获取详细的服务器状态信息

**响应示例**:
```json
{
  "system": {
    "platform": "Windows",
    "platform_version": "10.0.19041",
    "architecture": "64bit",
    "processor": "Intel64 Family 6 Model 142 Stepping 10, GenuineIntel",
    "python_version": "3.9.7"
  },
  "process": {
    "pid": 12345,
    "memory_usage": 45.2,
    "cpu_percent": 0.1,
    "create_time": 1640995000.0
  },
  "success": true
}
```

---

### 打印机模块 (`/printer`)

#### `GET /printer/list`
获取系统中所有可用打印机列表

**响应示例**:
```json
{
  "result": [
    {
      "name": "Microsoft Print to PDF",
      "status": "Ready",
      "driver": "Microsoft Print To PDF",
      "paper_sizes": ["A4", "Letter", "Legal"]
    },
    {
      "name": "HP LaserJet Pro",
      "status": "Ready",
      "driver": "HP Universal Printing PCL 6",
      "paper_sizes": ["A4", "Letter", "A3"]
    }
  ],
  "success": true
}
```

#### `POST /printer/print/file`
打印指定文件

**请求参数**:
```json
{
  "file_path": "/path/to/document.pdf",
  "printer_name": "HP LaserJet Pro",  // 可选，不指定则使用默认打印机
  "paper_size": "A4"                  // 可选，不指定则使用默认纸张大小
}
```

**响应示例**:
```json
{
  "result": true,
  "success": true,
  "message": "打印任务已提交"
}
```

**错误响应**:
```json
{
  "error": "缺少file_path参数",
  "success": false
}
```

#### `POST /printer/print/data`
打印数据内容

**请求参数**:
```json
{
  "data": "Hello World!\n这是要打印的文本内容",
  "file_type": "txt",                 // 支持: txt, html, pdf等
  "printer_name": "HP LaserJet Pro",  // 可选
  "paper_size": "A4"                  // 可选
}
```

**响应示例**:
```json
{
  "result": true,
  "success": true,
  "message": "打印任务已提交"
}
```

**错误响应**:
```json
{
  "error": "缺少data或file_type参数",
  "success": false
}
```

#### `GET /printer/default`
获取系统默认打印机

**响应示例**:
```json
{
  "result": {
    "name": "Microsoft Print to PDF",
    "status": "Ready",
    "driver": "Microsoft Print To PDF",
    "paper_sizes": ["A4", "Letter", "Legal"]
  },
  "success": true,
  "message": "获取默认打印机成功"
}
```

#### `GET /printer/status/<printer_name>`
获取指定打印机的详细状态

**URL参数**:
- `printer_name`: 打印机名称

**响应示例**:
```json
{
  "result": {
    "name": "HP LaserJet Pro",
    "status": "Ready",
    "driver": "HP Universal Printing PCL 6",
    "paper_sizes": ["A4", "Letter", "A3"]
  },
  "success": true,
  "message": "获取打印机 HP LaserJet Pro 状态成功"
}
```

**错误响应**:
```json
{
  "error": "未找到打印机: NonExistentPrinter",
  "success": false
}
```

#### `POST /printer/test`
测试打印机连接

**请求参数**:
```json
{
  "printer_name": "HP LaserJet Pro"  // 可选，不指定则测试所有打印机
}
```

**响应示例（指定打印机）**:
```json
{
  "result": "打印机 HP LaserJet Pro 连接正常",
  "printer_info": {
    "name": "HP LaserJet Pro",
    "status": "Ready",
    "driver": "HP Universal Printing PCL 6",
    "paper_sizes": ["A4", "Letter", "A3"]
  },
  "success": true
}
```

**响应示例（测试所有打印机）**:
```json
{
  "result": "找到 2 台可用打印机",
  "printers": [
    {
      "name": "Microsoft Print to PDF",
      "status": "Ready"
    },
    {
      "name": "HP LaserJet Pro",
      "status": "Ready"
    }
  ],
  "success": true
}
```

---

### 错误处理

所有API接口都遵循统一的错误响应格式：

```json
{
  "error": "错误描述",
  "message": "详细错误信息",
  "success": false
}
```

**常见HTTP状态码**:
- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源未找到（如指定的打印机不存在）
- `500`: 服务器内部错误

## 💻 使用示例

### Python 直接调用

```python
from printer import PrinterInfo

# 创建PrinterInfo实例
printer_info = PrinterInfo()

# 获取所有打印机信息
printers = printer_info.get_printers()

# 打印打印机信息
printer_info.print_printer_info()

# 打印文件
printer_info.print_file("document.pdf")

# 打印数据
printer_info.print_data("Hello World!")
```

### HTTP API 调用

```bash
# 获取API说明
curl http://localhost:6789/

# 获取应用信息
curl http://localhost:6789/app/info

# 健康检查
curl http://localhost:6789/app/health

# 获取服务器状态
curl http://localhost:6789/app/status

# 获取打印机列表
curl http://localhost:6789/printer/list

# 获取默认打印机
curl http://localhost:6789/printer/default

# 获取指定打印机状态
curl http://localhost:6789/printer/status/Microsoft%20Print%20to%20PDF

# 测试打印机连接
curl -X POST http://localhost:6789/printer/test \
  -H "Content-Type: application/json" \
  -d '{"printer_name": "Microsoft Print to PDF"}'

# 打印文件
curl -X POST http://localhost:6789/printer/print/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "document.pdf", "printer_name": "Microsoft Print to PDF"}'

# 打印数据
curl -X POST http://localhost:6789/printer/print/data \
  -H "Content-Type: application/json" \
  -d '{"data": "Hello World!", "file_type": "txt"}'

# 关闭服务器
curl http://localhost:6789/app/shutdown
```

### Node.js 客户端调用

```javascript
const PrinterClient = require('./node/index.js');

async function example() {
    const client = new PrinterClient();
    
    try {
        // 启动服务
        const port = await client.startService();
        console.log(`服务运行在端口: ${port}`);
        
        // 获取应用信息
        const appInfo = await client.request('GET', '/app/info');
        console.log('应用信息:', appInfo.data);
        
        // 健康检查
        const health = await client.request('GET', '/app/health');
        console.log('健康状态:', health.data);
        
        // 获取打印机列表
        const printers = await client.request('GET', '/printer/list');
        console.log(`执行时长: ${printers.duration}ms`);
        console.log('打印机列表:', printers.data);
        
        // 获取默认打印机
        const defaultPrinter = await client.request('GET', '/printer/default');
        console.log('默认打印机:', defaultPrinter.data);
        
        // 测试打印机连接
        const testResult = await client.request('POST', '/printer/test', {
            printer_name: 'Microsoft Print to PDF'
        });
        console.log('测试结果:', testResult.data);
        
        // 打印文件
        const printFile = await client.request('POST', '/printer/print/file', {
            file_path: 'document.pdf',
            printer_name: 'Microsoft Print to PDF'
        });
        console.log('打印文件结果:', printFile.data);
        
        // 打印数据
        const printData = await client.request('POST', '/printer/print/data', {
            data: 'Hello World!',
            file_type: 'txt'
        });
        console.log('打印数据结果:', printData.data);
        
    } finally {
        // 停止服务
        client.stopService();
    }
}

example().catch(console.error);
```

## 📊 性能数据

基于测试结果的性能指标：

- **服务启动时间**: ~6.5秒
- **API连接测试**: ~14ms
- **获取打印机列表**: ~80ms
- **平均响应时间**: ~85ms (连续5次请求)
- **成功率**: 100%

## 🔌 Electron 集成

项目提供了完整的Electron集成方案：

```python
from electron_example import PrinterService

# 创建服务实例
service = PrinterService()

# 启动服务（自动找到可用端口）
result = service.start()

if result['success']:
    print(f"服务地址: {result['url']}")
    print(f"端口: {result['port']}")
```

## 🛠️ 开发和打包

### 环境准备

首先确保安装了必要的依赖：

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装PyInstaller（用于打包）
pip install pyinstaller
```

### 打包成可执行文件

项目提供了完整的打包脚本 `build_example.py`：

```bash
# 使用打包脚本
python build_example.py build
```

**打包过程说明：**

1. **PyInstaller配置**: 使用 `--onefile` 参数打包成单个可执行文件
2. **文件包含**: 自动包含 `printer.py` 模块
3. **输出位置**: 生成的可执行文件位于 `dist/printer-server`
4. **跨平台**: 支持Windows、macOS、Linux

**手动打包命令：**

```bash
pyinstaller --onefile --name=printer-server --add-data=printer.py:. server.py
```

### 可执行文件使用

打包完成后，可执行文件支持以下使用方式：

```bash
# 直接启动服务（默认端口6789）
./dist/printer-server

# 启动服务并输出端口信息
./dist/printer-server --output-port

# 查看帮助信息
./dist/printer-server --help
```

### 获取服务端口

项目提供了多种方式获取动态分配的端口：

#### 方法1: 使用端口读取器

```python
from port_reader import get_server_port

# 启动服务并获取端口
process, port = get_server_port("./dist/printer-server")
print(f"服务运行在端口: {port}")

# 使用完毕后记得关闭进程
process.terminate()
```

#### 方法2: 解析标准输出

```python
import subprocess
import re

# 启动服务
process = subprocess.Popen(
    ["./dist/printer-server", "--output-port"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# 读取输出获取端口
for line in process.stdout:
    match = re.search(r'PORT:(\d+)', line)
    if match:
        port = int(match.group(1))
        print(f"检测到端口: {port}")
        break
```

#### 方法3: Node.js集成

```javascript
// 使用提供的Node.js客户端
const PrinterClient = require('./node/index.js');

const client = new PrinterClient();
const port = await client.startService();
console.log(`服务端口: ${port}`);
```

### 打包测试

使用内置的演示功能测试打包结果：

```bash
# 演示可执行文件的使用方法
python build_example.py demo
```

### 部署注意事项

1. **依赖库**: 可执行文件已包含所有Python依赖，无需额外安装
2. **系统权限**: 某些系统可能需要管理员权限访问打印机
3. **防火墙**: 确保HTTP端口（默认6789）未被防火墙阻止
4. **文件大小**: 打包后的文件大小约为20-30MB
5. **启动时间**: 首次启动可能需要几秒钟初始化时间

## 文件说明

- `printer_info.py`: 主程序文件，包含PrinterInfo类
- `example.py`: 示例程序，展示各种使用方法
- `requirements.txt`: 依赖文件
- `README.md`: 说明文档

## 注意事项

1. **Windows系统**: 需要安装`pywin32`库才能获取详细的打印机信息
2. **macOS/Linux系统**: 需要确保CUPS服务正在运行
3. **权限问题**: 某些系统可能需要管理员权限才能访问打印机信息
4. **网络打印机**: 网络打印机的信息获取可能需要额外的网络权限

## 错误处理

程序包含完善的错误处理机制：

- 自动检测操作系统类型
- 处理打印机访问权限问题
- 处理缺少依赖库的情况
- 提供详细的错误信息

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！