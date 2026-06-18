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
  - `batch_size`: (Integer, 默认 4) 每组图片的数量
  - `batch_id`: (String, 可选) 批次号，作为输出文件名的前缀
- **返回**:
  - `success`: 是否成功
  - `message`: 包含处理结果的描述信息
  - `output_dir`: 合成文件保存的目录 (原图目录下的 `concatenate/`)
- **说明**: 每 `batch_size` 张图自动合并为一个长图（每两张图之间自动留出 0.3 厘米间距）。如果提供了 `batch_id`，输出文件名将为 `batch_id-1.tif` 等；否则默认为 `concatenate-1.tif`。输出文件固定为 **CMYK** 颜色模式（适合 T 恤印花）。使用 Adobe Deflate + Predictor 高强度压缩。

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

## 5. 指纹识别模块 (`/fingerprint`)

### 业务接入流程

推荐业务端按下面顺序接入：

1. **启动本地服务**
   - 业务端可以每次启动时都尝试启动 `py-server-windows.exe --output-port`。
   - 服务自身会检测是否已有实例运行；如果已有实例，会输出已有 `PORT:<端口>` 并退出，不会重复启动多个服务。

2. **检测并按需安装指纹环境**
   - 调用 `POST /fingerprint/installer/ensure`。
   - 如果 SDK 环境可用，接口返回 `ready=true`，不会弹安装程序。
   - 如果 SDK 环境不可用，服务会自动启动打包内置的 `setup.exe`；Windows 下默认会弹 UAC 授权窗口。
   - 安装完成后，建议业务端重新调用 `/fingerprint/diagnostics` 或重启本地服务再继续。

3. **打开指纹设备**
   - 调用 `POST /fingerprint/device/open`。
   - 打开成功后返回设备序列号和图像宽高。

4. **加载业务数据库中的指纹模板**
   - 调用 `POST /fingerprint/templates/load`。
   - SDK 的识别库是内存库，服务进程重启或设备关闭后需要重新加载。
   - 建议启动时传 `clear_existing=true`，把业务数据库里的模板全量加载到 SDK 内存识别库。

5. **录入指纹**
   - 推荐使用 `GET /fingerprint/enroll/events`。
   - 它是 SSE 事件流，会在每次采集成功后推送灰度图和当前次数，三次完成后返回最终模板。
   - 业务端收到 `completed` 事件后，把最终 `templateBase64` 保存到业务数据库。
   - 如果录入时传了 `fid`，当前 SDK 内存库会自动加入该模板。

6. **日常识别**
   - 推荐业务端轮询调用 `POST /fingerprint/identify`。
   - 每次请求等待一次手指采集并返回识别结果。
   - 建议参数为 `timeout_ms=2500`，每次响应后间隔 `300-500ms` 再发下一次；识别成功后冷却 `1.5-3s`，避免同一根手指一直按着重复上报。

### 启动服务与单实例

命令行启动：

```powershell
.\py-server-windows.exe --output-port
```

如果没有服务运行，输出示例：

```text
PORT:6789
```

如果已有服务运行，输出示例：

```text
检测到已有服务正在运行: http://localhost:6789
PORT:6789
```

业务端只需要读取 `PORT:<端口>`，后续请求都打到这个端口即可。

### 检测指纹环境
- **路径**: `/fingerprint/diagnostics`
- **方法**: `GET`
- **说明**: 检测 `pythonnet`、`libzkfpcsharp.dll`、内置安装程序 `setup.exe` 是否存在，并尝试初始化 ZKFP SDK 获取设备数量。
- **返回**:
  - `pythonnetAvailable`: 是否可加载 pythonnet
  - `clrAvailable`: 是否可加载 CLR Bridge
  - `sdkDllExists`: 是否找到 `libzkfpcsharp.dll`
  - `installerExists`: 是否找到内置 `setup.exe`
  - `sdkAvailable`: SDK 是否初始化成功
  - `deviceCount`: 已连接设备数量
  - `error`: 失败时返回错误类型、信息和安装提示

### 启动指纹驱动安装程序
- **路径**: `/fingerprint/installer/run`
- **方法**: `POST`
- **参数 (JSON)**:
  - `elevated`: (Boolean, 默认 true) Windows 下是否请求管理员权限启动安装程序
- **说明**: 启动打包内置的 `setup.exe`。如果 `elevated=true`，Windows 会弹出 UAC 授权窗口；安装过程由安装程序自身完成。

### 检测并按需安装指纹环境
- **路径**: `/fingerprint/installer/ensure`
- **方法**: `POST`
- **参数 (JSON)**:
  - `elevated`: (Boolean, 默认 true) Windows 下是否请求管理员权限启动安装程序
- **说明**: 推荐业务端启动后调用一次。服务会先执行环境检测；如果 `sdkAvailable=true`，不会启动安装程序；如果 SDK 不可用且内置 `setup.exe` 存在，则自动启动安装程序。
- **请求示例**:
  ```json
  {
    "elevated": true
  }
  ```
- **环境可用响应示例**:
  ```json
  {
    "success": true,
    "message": "指纹环境可用，无需安装",
    "result": {
      "ready": true,
      "installStarted": false
    }
  }
  ```
- **环境不可用时响应示例**:
  ```json
  {
    "success": true,
    "message": "指纹环境不可用，已尝试启动安装程序",
    "result": {
      "ready": false,
      "installStarted": true
    }
  }
  ```

### 获取设备数量
- **路径**: `/fingerprint/device/count`
- **方法**: `GET`
- **返回**:
  - `count`: 已连接的指纹设备数量

### 获取设备状态
- **路径**: `/fingerprint/device/status`
- **方法**: `GET`
- **返回**:
  - `opened`: 当前服务是否已打开指纹设备
  - `serialNumber`: 设备序列号
  - `width`: 指纹图像宽度
  - `height`: 指纹图像高度

### 打开设备
- **路径**: `/fingerprint/device/open`
- **方法**: `POST`
- **参数 (JSON)**:
  - `index`: (Integer, 默认 0) 设备索引
- **返回**:
  - `serialNumber`: 设备序列号
  - `width`: 指纹图像宽度
  - `height`: 指纹图像高度
- **请求示例**:
  ```json
  {
    "index": 0
  }
  ```

### 关闭设备
- **路径**: `/fingerprint/device/close`
- **方法**: `POST`

### 采集指纹
- **路径**: `/fingerprint/capture`
- **方法**: `POST`
- **参数 (JSON)**:
  - `timeout_ms`: (Integer, 默认 10000) 等待手指按压的超时时间
- **返回**:
  - `templateBase64`: 指纹模板 Base64
  - `imageBase64`: 灰度指纹图像原始字节 Base64
  - `width`: 图像宽度
  - `height`: 图像高度

### 录入指纹
- **路径**: `/fingerprint/enroll`
- **方法**: `POST`
- **参数 (JSON)**:
  - `fid`: (Integer, 可选) 指纹 ID。提供后会把合并后的模板加入内存识别库
  - `sample_count`: (Integer, 默认 3) 采样次数，ZKFP2 固定要求 3 次
  - `timeout_ms`: (Integer, 默认 10000) 每次采集超时时间
- **说明**: 连续采集同一根手指 3 次并合并为注册模板。

### 流式录入指纹
- **路径**: `/fingerprint/enroll/events`
- **方法**: `GET`
- **类型**: Server-Sent Events (`text/event-stream`)
- **查询参数**:
  - `fid`: (Integer, 可选) 指纹 ID。提供后会把合并后的模板加入内存识别库
  - `sample_count`: (Integer, 默认 3) 采样次数，ZKFP2 固定要求 3 次
  - `timeout_ms`: (Integer, 默认 10000) 每次采集超时时间
- **事件**:
  - `started`: 录入开始
  - `captured`: 每次采集成功后推送，包含 `step`、`total`、`capture`
  - `completed`: 三次采集并合并模板完成
  - `error`: 录入失败
- **captured 事件示例**:
  ```json
  {
    "success": true,
    "step": 1,
    "total": 3,
    "capture": {
      "templateBase64": "...",
      "imageBase64": "...",
      "width": 256,
      "height": 360
    }
  }
  ```
- **completed 事件示例**:
  ```json
  {
    "success": true,
    "message": "指纹录入成功",
    "fid": 1001,
    "templateBase64": "...",
    "templateLength": 2048,
    "captures": []
  }
  ```
- **前端示例**:
  ```javascript
  const source = new EventSource(
    "http://localhost:6789/fingerprint/enroll/events?fid=1001&timeout_ms=10000"
  );

  source.addEventListener("captured", (event) => {
    const data = JSON.parse(event.data);
    console.log(`第 ${data.step}/${data.total} 次采集成功`);
    console.log(data.capture.imageBase64);
  });

  source.addEventListener("completed", (event) => {
    const data = JSON.parse(event.data);
    console.log("最终模板", data.templateBase64);
    source.close();
  });

  source.addEventListener("error", (event) => {
    console.error(event.data);
    source.close();
  });
  ```

### 识别指纹
- **路径**: `/fingerprint/identify`
- **方法**: `POST`
- **参数 (JSON)**:
  - `template_base64`: (String, 可选) 指定要识别的模板。不传则现场采集
  - `timeout_ms`: (Integer, 默认 10000) 现场采集超时时间
  - `min_score`: (Integer, 默认 1) 最低匹配分数，小于该值时 `matched` 为 `false`
- **返回**:
  - `fid`: 命中的指纹 ID，未命中时通常为 0
  - `score`: 匹配分数
  - `matched`: 是否匹配成功
  - `capture`: 现场采集时返回采集结果
- **业务轮询建议**:
  ```json
  {
    "timeout_ms": 2500,
    "min_score": 1
  }
  ```
  业务端收到响应后间隔 300-500ms 发起下一次识别；识别成功后建议冷却 1.5-3 秒，避免同一根手指一直按着时重复上报。
- **响应示例**:
  ```json
  {
    "success": true,
    "message": "指纹识别完成",
    "result": {
      "fid": 1001,
      "score": 87,
      "matched": true,
      "minScore": 1,
      "timeoutMs": 2500,
      "capture": {
        "templateBase64": "...",
        "imageBase64": "...",
        "width": 256,
        "height": 360
      }
    }
  }
  ```

### 1:1 比对
- **路径**: `/fingerprint/match`
- **方法**: `POST`
- **参数 (JSON)**:
  - `template1_base64`: (String, 必填) 第一个模板
  - `template2_base64`: (String, 必填) 第二个模板
- **返回**:
  - `score`: 比对分数

### 模板管理
- **添加模板**: `POST /fingerprint/templates/add`
  - `fid`: (Integer, 必填) 指纹 ID
  - `template_base64`: (String, 必填) 指纹模板
- **批量加载模板**: `POST /fingerprint/templates/load`
  - `templates`: (Array, 必填) 模板列表，格式为 `[{ "fid": 1, "template_base64": "..." }]`
  - `clear_existing`: (Boolean, 默认 false) 是否先清空 SDK 内存识别库
- **批量加载请求示例**:
  ```json
  {
    "clear_existing": true,
    "templates": [
      {
        "fid": 1001,
        "template_base64": "..."
      }
    ]
  }
  ```
- **删除模板**: `POST /fingerprint/templates/delete`
  - `fid`: (Integer, 必填) 指纹 ID
- **清空模板**: `POST /fingerprint/templates/clear`
- **合并模板**: `POST /fingerprint/templates/merge`
  - `templates_base64`: (Array, 必填) 长度为 3 的模板数组
  - `fid`: (Integer, 可选) 指定后加入内存识别库

### 控制灯光
- **路径**: `/fingerprint/light`
- **方法**: `POST`
- **参数 (JSON)**:
  - `color`: `white` / `green` / `red`，默认 `green`
  - `duration`: 持续秒数，默认 `0.5`

---

## 6. 统一响应格式

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
