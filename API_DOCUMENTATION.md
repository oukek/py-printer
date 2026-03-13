# 打印机服务 API 文档

本服务提供打印机管理、文件打印、图像处理（拼接与压缩）等功能。默认端口为 `6789`。

---

## 1. 应用控制模块 (`/app`)

### 获取应用信息
- **路径**: `/app/info`
- **方法**: `GET`
- **返回示例**:
  ```json
  {
    "success": true,
    "name": "打印机服务API",
    "version": "2.0.0",
    "status": "running",
    "host": "localhost",
    "port": 6789,
    "debug": false
  }
  ```

### 获取服务器状态
- **路径**: `/app/status`
- **方法**: `GET`
- **返回**:
  - `success`: 是否成功
  - `system`: 系统信息（平台、架构、Python 版本等）
  - `process`: 进程信息（PID、内存占用、CPU 占用等）

### 关闭服务器
- **路径**: `/app/shutdown`
- **方法**: `GET`
- **说明**: 异步触发服务器关闭任务。

---

## 2. 打印机模块 (`/printer`)

### 获取打印机列表
- **路径**: `/printer/list`
- **方法**: `GET`
- **返回**:
  - `success`: 是否成功
  - `result`: 打印机对象数组（包含名称、状态等）

### 打印本地文件
- **路径**: `/printer/print/file`
- **方法**: `POST`
- **参数 (JSON)**:
  - `file_path`: (String, 必填) 本地文件绝对路径
  - `printer_name`: (String, 可选) 指定打印机名称
  - `paper_size`: (String, 可选) 纸张尺寸
- **返回**: `success`, `message`

### 打印 Base64 数据
- **路径**: `/printer/print/data`
- **方法**: `POST`
- **参数 (JSON)**:
  - `data`: (String, 必填) Base64 编码的文件数据
  - `file_type`: (String, 必填) 文件类型 (如 `pdf`, `jpg`, `png`)
  - `printer_name`: (String, 可选) 指定打印机名称
- **返回**: `success`, `message`

---

## 3. 图像处理模块 (`/printing`)

### 获取图像信息
- **路径**: `/printing/image/info`
- **方法**: `POST`
- **参数 (JSON)**:
  - `image_data`: (String, 必填) 图片路径或 Base64 数据
- **返回**:
  - `width`: 宽度
  - `height`: 高度
  - `mode`: 颜色模式 (如 `RGBA`)
  - `format`: 格式 (如 `PNG`)

### 批量分组合并 TIFF
- **路径**: `/printing/image/concatenate`
- **方法**: `POST`
- **参数 (JSON)**:
  - `file_paths`: (Array, 必填) 图片绝对路径列表
  - `target_width`: (Integer, 默认 6614) 目标宽度
  - `dpi`: (Integer, 默认 300) 分辨率
- **返回**:
  - `success`: 是否成功
  - `message`: 包含处理结果的描述信息
  - `output_dir`: 合成文件保存的目录 (原图目录下的 `concatenate/`)
- **说明**: 每 4 张图自动合并为一个长图，使用 Adobe Deflate + Predictor 高强度压缩。

---

## 4. 图像压缩模块 (`/compress`)

### 压缩本地文件
- **路径**: `/compress/image`
- **方法**: `POST`
- **参数 (JSON)**:
  - `input_path`: (String, 必填) 输入文件绝对路径
  - `quality`: (Integer, 默认 100) JPG 质量 (1-100)
  - `png_quantize`: (Boolean, 默认 True) 是否对 PNG 进行颜色量化（模拟 TinyPNG）
- **返回**:
  - `output_path`: 压缩后的文件路径
  - `original_size`: 原始大小
  - `compressed_size`: 压缩后大小
  - `ratio`: 压缩率

### 直接压缩 Base64 数据
- **路径**: `/compress/image/base64`
- **方法**: `POST`
- **参数 (JSON)**:
  - `image_base64`: (String, 必填) 原始图片 Base64 字符串
  - `quality`: (Integer, 默认 100) JPG 质量 (1-100)
  - `png_quantize`: (Boolean, 默认 True) 是否对 PNG 进行颜色量化
- **返回**:
  - `compressed_base64`: 压缩后的 Base64 字符串
  - `ratio`: 压缩率
  - `format`: 图像格式

---

## 5. 统一响应格式

### 成功响应
```json
{
  "success": true,
  "result": { ...数据... },
  "message": "描述信息"
}
```

### 失败响应
```json
{
  "success": false,
  "error": "错误类型",
  "message": "具体错误原因"
}
```
