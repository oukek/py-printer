# 打印机信息获取工具

一个跨平台的Python工具，用于获取系统中的打印机列表和每个打印机支持的纸张类型。

## 功能特性

- 🖨️ 获取系统中所有打印机的列表
- 📄 获取每个打印机支持的纸张类型和尺寸
- 🔄 跨平台支持（Windows、macOS、Linux）
- 📊 支持将信息导出为JSON格式
- 🎯 提供丰富的示例代码

## 支持的操作系统

- **Windows**: 使用Windows API获取详细的打印机信息
- **macOS**: 使用CUPS命令行工具获取打印机信息
- **Linux**: 使用CUPS命令行工具获取打印机信息

## 安装依赖

### Windows系统
```bash
pip install pywin32
```

### macOS/Linux系统
无需额外依赖，使用系统内置的CUPS工具。

## 使用方法

### 基本使用

```python
from printer_info import PrinterInfo

# 创建PrinterInfo实例
printer_info = PrinterInfo()

# 获取所有打印机信息
printers = printer_info.get_printers()

# 打印打印机信息
printer_info.print_printer_info()
```

### 运行主程序

```bash
python printer_info.py
```

### 运行示例程序

```bash
python example.py
```

## 返回数据格式

每个打印机的信息包含以下字段：

```python
{
    'name': '打印机名称',
    'status': '打印机状态',
    'driver': '驱动程序名称',  # Windows
    'port': '端口信息',       # Windows
    'uri': 'URI地址',         # macOS/Linux
    'paper_sizes': [          # 支持的纸张类型
        {
            'name': '纸张名称',
            'display_name': '显示名称',
            'width_mm': 210,    # 宽度（毫米）- 仅Windows
            'height_mm': 297    # 高度（毫米）- 仅Windows
        }
    ]
}
```

## 示例代码

### 获取所有打印机

```python
from printer_info import PrinterInfo

printer_info = PrinterInfo()
printers = printer_info.get_printers()

for printer in printers:
    print(f"打印机: {printer['name']}")
    print(f"状态: {printer.get('status', '未知')}")
    print(f"支持的纸张类型: {len(printer.get('paper_sizes', []))} 种")
    print()
```

### 筛选可用打印机

```python
available_printers = []
for printer in printers:
    status = printer.get('status', '').lower()
    if 'ready' in status or 'enabled' in status or '就绪' in status:
        available_printers.append(printer)

print(f"找到 {len(available_printers)} 个可用打印机")
```

### 查找支持特定纸张的打印机

```python
a4_printers = []
for printer in printers:
    paper_sizes = printer.get('paper_sizes', [])
    for paper in paper_sizes:
        paper_name = paper.get('display_name', paper.get('name', '')).lower()
        if 'a4' in paper_name:
            a4_printers.append(printer['name'])
            break

print(f"支持A4纸张的打印机: {a4_printers}")
```

### 保存信息到JSON文件

```python
import json

with open('printer_info.json', 'w', encoding='utf-8') as f:
    json.dump(printers, f, ensure_ascii=False, indent=2)
```

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