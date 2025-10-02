const PrinterClient = require('./index.js');
const path = require('path');

/**
 * 测试脚本 - 验证打印机服务调用功能并打印PDF文件
 */
async function runTests() {
    console.log('🧪 开始测试打印机客户端...\n');
    
    const client = new PrinterClient();
    let testResults = [];
    
    try {
        // 测试1: 启动服务
        console.log('📋 测试1: 启动服务');
        console.log('-'.repeat(30));
        const startTime = Date.now();
        
        const port = await client.startService();
        const serviceStartDuration = Date.now() - startTime;
        
        testResults.push({
            test: '启动服务',
            success: true,
            duration: serviceStartDuration,
            details: `端口: ${port}`
        });
        
        console.log(`✅ 服务启动成功，耗时: ${serviceStartDuration}ms\n`);
        
        // 等待服务完全启动
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 测试2: 连接测试
        console.log('📋 测试2: API连接测试');
        console.log('-'.repeat(30));
        
        const connectionResult = await client.testConnection();
        testResults.push({
            test: 'API连接',
            success: connectionResult.success,
            duration: connectionResult.duration,
            details: connectionResult.success ? 'API响应正常' : connectionResult.error
        });
        
        if (connectionResult.success) {
            console.log(`✅ 连接测试成功，耗时: ${connectionResult.duration}ms\n`);
        } else {
            console.log(`❌ 连接测试失败: ${connectionResult.error}\n`);
        }
        
        // 测试3: 获取打印机列表
        console.log('📋 测试3: 获取打印机列表');
        console.log('-'.repeat(30));
        
        const printersResult = await client.getPrinters();
        testResults.push({
            test: '获取打印机列表',
            success: printersResult.success,
            duration: printersResult.duration,
            details: printersResult.success ? 
                `找到 ${Array.isArray(printersResult.data) ? printersResult.data.length : 0} 台打印机` : 
                printersResult.error
        });
        
        if (printersResult.success) {
            console.log(`✅ 获取打印机列表成功，耗时: ${printersResult.duration}ms`);
            console.log('📋 打印机数据:');
            console.log(JSON.stringify(printersResult.data, null, 2));
        } else {
            console.log(`❌ 获取打印机列表失败: ${printersResult.error}`);
        }

        // 测试4: 打印PDF文件
        console.log('\n📋 测试4: 打印PDF文件');
        console.log('-'.repeat(30));
        
        const pdfPath = path.join(__dirname, '1.pdf');
        console.log(`📄 PDF文件路径: ${pdfPath}`);
        
        const printResult = await client.printFile(pdfPath);
        testResults.push({
            test: '打印PDF文件',
            success: printResult.success,
            duration: printResult.duration,
            details: printResult.success ? 
                (printResult.data?.message || '打印任务已提交') : 
                printResult.error
        });
        
        if (printResult.success) {
            console.log(`✅ PDF打印成功，耗时: ${printResult.duration}ms`);
            console.log('📋 打印结果:');
            console.log(JSON.stringify(printResult.data, null, 2));
        } else {
            console.log(`❌ PDF打印失败: ${printResult.error}`);
        }
        
        // 测试5: 性能测试 (连续3次请求)
        console.log('\n📋 测试5: 性能测试 (连续3次请求)');
        console.log('-'.repeat(30));
        
        const performanceResults = [];
        for (let i = 1; i <= 3; i++) {
            console.log(`🔄 第${i}次请求...`);
            const result = await client.getPrinters();
            performanceResults.push(result.duration);
            console.log(`   耗时: ${result.duration}ms`);
        }
        
        const avgDuration = performanceResults.reduce((a, b) => a + b, 0) / performanceResults.length;
        const minDuration = Math.min(...performanceResults);
        const maxDuration = Math.max(...performanceResults);
        
        testResults.push({
            test: '性能测试',
            success: true,
            duration: avgDuration,
            details: `平均: ${avgDuration.toFixed(2)}ms, 最快: ${minDuration}ms, 最慢: ${maxDuration}ms`
        });
        
        console.log(`📊 性能统计:`);
        console.log(`   平均耗时: ${avgDuration.toFixed(2)}ms`);
        console.log(`   最快: ${minDuration}ms`);
        console.log(`   最慢: ${maxDuration}ms`);
        
    } catch (error) {
        console.error(`💥 测试失败: ${error.message}`);
        testResults.push({
            test: '整体测试',
            success: false,
            duration: 0,
            details: error.message
        });
    } finally {
        // 停止服务
        client.stopService();
    }
    
    // 输出测试报告
    console.log('\n📊 测试报告');
    console.log('='.repeat(50));
    
    testResults.forEach((result, index) => {
        const status = result.success ? '✅' : '❌';
        console.log(`${status} ${result.test}: ${result.duration}ms - ${result.details}`);
    });
    
    const successCount = testResults.filter(r => r.success).length;
    const totalCount = testResults.length;
    
    console.log('\n📈 测试总结:');
    console.log(`   成功: ${successCount}/${totalCount}`);
    console.log(`   成功率: ${((successCount / totalCount) * 100).toFixed(1)}%`);
    
    if (successCount === totalCount) {
        console.log('🎉 所有测试通过！');
        process.exit(0);
    } else {
        console.log('⚠️  部分测试失败');
        process.exit(1);
    }
}

// 运行测试
if (require.main === module) {
    runTests().catch(error => {
        console.error(`💥 测试执行失败: ${error.message}`);
        process.exit(1);
    });
}