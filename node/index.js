const { spawn } = require('child_process');
const axios = require('axios');
const path = require('path');

class PrinterClient {
    constructor() {
        this.process = null;
        this.port = null;
        this.baseUrl = null;
    }

    /**
     * 启动打印机服务并获取端口
     * @returns {Promise<number>} 返回服务端口号
     */
    async startService() {
        return new Promise((resolve, reject) => {
            const executablePath = path.join(__dirname, '..', 'dist', 'printer-server');
            
            console.log('🚀 启动打印机服务...');
            console.log(`📁 可执行文件路径: ${executablePath}`);
            
            // 启动可执行文件
            this.process = spawn(executablePath, ['--output-port'], {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let portFound = false;
            const timeout = setTimeout(() => {
                if (!portFound) {
                    reject(new Error('获取端口超时'));
                }
            }, 10000); // 10秒超时

            // 监听标准输出
            this.process.stdout.on('data', (data) => {
                const output = data.toString();
                console.log(`📤 服务输出: ${output.trim()}`);
                
                // 查找端口信息 - 改进正则表达式匹配
                const lines = output.split('\n');
                for (const line of lines) {
                    const portMatch = line.match(/PORT:(\d+)/);
                    if (portMatch && !portFound) {
                        portFound = true;
                        clearTimeout(timeout);
                        this.port = parseInt(portMatch[1]);
                        this.baseUrl = `http://localhost:${this.port}`;
                        console.log(`✅ 服务启动成功，端口: ${this.port}`);
                        resolve(this.port);
                        return;
                    }
                }
            });

            // 监听错误输出
            this.process.stderr.on('data', (data) => {
                console.error(`❌ 服务错误: ${data.toString()}`);
            });

            // 监听进程退出
            this.process.on('close', (code) => {
                console.log(`🛑 服务进程退出，代码: ${code}`);
                if (!portFound) {
                    reject(new Error(`服务启动失败，退出代码: ${code}`));
                }
            });

            // 监听进程错误
            this.process.on('error', (error) => {
                console.error(`💥 进程错误: ${error.message}`);
                reject(error);
            });
        });
    }

    /**
     * 获取打印机列表
     * @returns {Promise<Object>} 返回打印机列表和执行时长
     */
    async getPrinters() {
        if (!this.baseUrl) {
            throw new Error('服务未启动，请先调用 startService()');
        }

        console.log('📋 获取打印机列表...');
        const startTime = Date.now();

        try {
            const response = await axios.get(`${this.baseUrl}/printers`, {
                timeout: 5000 // 5秒超时
            });
            
            const endTime = Date.now();
            const duration = endTime - startTime;

            console.log(`⏱️  请求耗时: ${duration}ms`);
            console.log(`📊 响应状态: ${response.status}`);
            
            return {
                success: true,
                data: response.data,
                duration: duration,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            console.error(`❌ 获取打印机列表失败: ${error.message}`);
            console.log(`⏱️  请求耗时: ${duration}ms`);
            
            return {
                success: false,
                error: error.message,
                duration: duration,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 测试API连接
     * @returns {Promise<Object>} 返回连接测试结果
     */
    async testConnection() {
        if (!this.baseUrl) {
            throw new Error('服务未启动，请先调用 startService()');
        }

        console.log('🔗 测试API连接...');
        const startTime = Date.now();

        try {
            const response = await axios.get(`${this.baseUrl}/`, {
                timeout: 3000
            });
            
            const endTime = Date.now();
            const duration = endTime - startTime;

            console.log(`✅ 连接测试成功，耗时: ${duration}ms`);
            
            return {
                success: true,
                data: response.data,
                duration: duration
            };

        } catch (error) {
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            console.error(`❌ 连接测试失败: ${error.message}`);
            
            return {
                success: false,
                error: error.message,
                duration: duration
            };
        }
    }

    /**
     * 停止服务
     */
    stopService() {
        if (this.process) {
            console.log('🛑 正在停止服务...');
            this.process.kill();
            this.process = null;
            this.port = null;
            this.baseUrl = null;
            console.log('✅ 服务已停止');
        }
    }
}

// 主函数
async function main() {
    const client = new PrinterClient();
    
    try {
        // 启动服务
        const port = await client.startService();
        console.log(`🎯 服务地址: http://localhost:${port}`);
        
        // 等待服务完全启动
        console.log('⏳ 等待服务完全启动...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 测试连接
        const connectionResult = await client.testConnection();
        if (!connectionResult.success) {
            throw new Error(`连接测试失败: ${connectionResult.error}`);
        }
        
        // 获取打印机列表
        const result = await client.getPrinters();
        
        console.log('\n📊 执行结果:');
        console.log('='.repeat(50));
        console.log(`✅ 成功: ${result.success}`);
        console.log(`⏱️  执行时长: ${result.duration}ms`);
        console.log(`🕐 时间戳: ${result.timestamp}`);
        
        if (result.success) {
            console.log('📋 打印机列表:');
            console.log(JSON.stringify(result.data, null, 2));
        } else {
            console.log(`❌ 错误: ${result.error}`);
        }
        
        // 等待一段时间后停止服务
        console.log('\n⏳ 5秒后自动停止服务...');
        setTimeout(() => {
            client.stopService();
            process.exit(0);
        }, 5000);
        
    } catch (error) {
        console.error(`💥 执行失败: ${error.message}`);
        client.stopService();
        process.exit(1);
    }
}

// 处理进程退出
process.on('SIGINT', () => {
    console.log('\n🛑 收到退出信号...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 收到终止信号...');
    process.exit(0);
});

// 如果直接运行此文件
if (require.main === module) {
    main();
}

module.exports = PrinterClient;