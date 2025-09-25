# 打印机服务 Node.js 客户端

这是一个 Node.js 客户端，用于调用打包好的打印机服务可执行文件，并通过 HTTP API 获取打印机列表。

## 📁 文件结构

```
node/
├── package.json    # 项目配置和依赖
├── index.js        # 主要的客户端类
├── test.js         # 完整的测试脚本
└── README.md       # 使用说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd node
npm install
```

### 2. 运行客户端

```bash
# 基本使用
node index.js

# 运行完整测试
node test.js
```

## 📊 功能特性

### ✅ 已实现功能

- **自动启动服务**: 调用 `../dist/printer-server` 可执行文件
- **端口自动获取**: 解析服务输出获取实际端口号
- **API 调用**: 通过 HTTP 请求获取打印机列表
- **执行时长记录**: 精确记录每次 API 调用的耗时
- **错误处理**: 完善的错误处理和超时机制
- **性能测试**: 支持连续多次请求的性能测试

### 📈 测试结果

根据最新测试结果：

- **服务启动时间**: ~6.5秒
- **API 连接测试**: ~14ms
- **获取打印机列表**: ~80ms
- **平均响应时间**: ~85ms (5次请求平均)
- **成功率**: 100%

## 🔧 使用方法

### 基本用法

```javascript
const PrinterClient = require('./index.js');

async function example() {
    const client = new PrinterClient();
    
    try {
        // 启动服务
        const port = await client.startService();
        console.log(`服务运行在端口: ${port}`);
        
        // 获取打印机列表
        const result = await client.getPrinters();
        console.log(`执行时长: ${result.duration}ms`);
        console.log('打印机列表:', result.data);
        
    } finally {
        // 停止服务
        client.stopService();
    }
}
```

### API 说明

#### `startService()`
启动打印机服务并获取端口号
- **返回**: `Promise<number>` - 服务端口号
- **异常**: 服务启动失败或超时

#### `getPrinters()`
获取打印机列表
- **返回**: `Promise<Object>` - 包含数据和执行时长的结果对象
- **格式**:
  ```javascript
  {
    success: true,
    data: [...],           // 打印机列表
    duration: 80,          // 执行时长(ms)
    timestamp: "2025-09-25T12:07:19.794Z"
  }
  ```

#### `testConnection()`
测试 API 连接
- **返回**: `Promise<Object>` - 连接测试结果

#### `stopService()`
停止打印机服务
- **返回**: `void`

## 📋 测试脚本

运行 `node test.js` 将执行以下测试：

1. **启动服务测试** - 验证可执行文件能否正常启动
2. **API 连接测试** - 验证 HTTP 连接是否正常
3. **获取打印机列表** - 验证核心功能
4. **性能测试** - 连续 5 次请求测试响应时间

## ⚙️ 配置说明

### 超时设置
- 服务启动超时: 10秒
- API 请求超时: 5秒
- 连接测试超时: 3秒

### 可执行文件路径
默认路径: `../dist/printer-server`

如需修改，请编辑 `index.js` 中的 `executablePath` 变量。

## 🐛 故障排除

### 常见问题

1. **"获取端口超时"**
   - 检查可执行文件是否存在: `../dist/printer-server`
   - 确认可执行文件有执行权限
   - 检查是否有其他进程占用端口

2. **"连接测试失败"**
   - 确认服务已正常启动
   - 检查防火墙设置
   - 验证端口是否被正确获取

3. **"API 请求超时"**
   - 检查网络连接
   - 确认服务响应正常
   - 适当增加超时时间

### 调试模式

所有输出都包含详细的日志信息，包括：
- 🚀 服务启动状态
- 📤 服务输出信息  
- ⏱️ 执行时长记录
- 📊 响应状态码
- ❌ 错误详情

## 📞 技术支持

如遇问题，请检查：
1. Node.js 版本 (建议 14+)
2. 依赖包是否正确安装
3. 可执行文件是否存在且可执行
4. 系统防火墙设置