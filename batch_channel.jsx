#target photoshop

function processFile(file, outputFolder) {
    // 1. 打开文档
    var doc = open(file);

    // 2. 修改画布宽度为 56 厘米 (保持原图居中)
    var originalUnit = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.CM; // 切换单位为厘米
    
    try {
        // 设置画布大小：宽度 56cm，高度保持不变，锚点在中心
        doc.resizeCanvas(56, doc.height.as("cm"), AnchorPosition.MIDDLECENTER);
    } catch(e) {
        alert("修改画布大小失败: " + e + "\n文件: " + file.name);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        return false;
    } finally {
        // 恢复原始单位
        app.preferences.rulerUnits = originalUnit;
    }

    // 3. 执行动作 (动作组名: 印花, 动作名: 白墨通道)
    try {
        app.doAction("白墨通道", "印花");
    } catch(e) {
        alert("执行动作失败！请确保 Photoshop 中已存在名为 '印花' 的动作组 and 名为 '白墨通道' 的动作。\n错误详情: " + e + "\n文件: " + file.name);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        return false;
    }

    // 4. 保存为 TIFF
    if (!outputFolder.exists) {
        outputFolder.create();
    }
    
    var newName = file.name.replace(/\.(png|tif|tiff)$/i, "") + ".tif";
    var saveFile = new File(outputFolder.fsName + "/" + newName);

    var opt = new TiffSaveOptions();
    opt.layers = false;             // 不保存图层，减小体积
    opt.imageCompression = TIFFEncoding.TIFFLZW; 
    opt.alphaChannels = true;       // 保留 Alpha 通道 (包含 W1 专色)
    opt.spotColors = true;          // 保留 W1 专色通道
    opt.transparency = true;        // 保留透明度
    opt.embedColorProfile = true;   // 嵌入色彩配置文件

    doc.saveAs(saveFile, opt, true);

    // 5. 关闭
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return true;
}

function main(){
    // 1. 选择源目录
    var folder = Folder.selectDialog("选择包含 PNG 或 TIF 图片的文件夹");
    if(!folder) return;

    // 2. 选择保存目录
    var outputFolder = Folder.selectDialog("选择通道图保存的目录");
    if(!outputFolder) return;

    // 3. 获取目录下所有的 PNG 和 TIF 文件
    var files = folder.getFiles(/\.(png|tif|tiff)$/i);
    
    if(files.length == 0) {
        alert("所选文件夹中没有找到 PNG 或 TIF 文件。");
        return;
    }

    var successCount = 0;
    var errorCount = 0;

    // 4. 循环处理
    for(var i = 0; i < files.length; i++) {
        var file = files[i];
        if(file instanceof File) {
            if(processFile(file, outputFolder)) {
                successCount++;
            } else {
                errorCount++;
            }
        }
    }

    // 5. 完成提示
    var msg = "处理完成！\n" +
              "成功: " + successCount + " 个文件\n";
    if(errorCount > 0) {
        msg += "失败: " + errorCount + " 个文件";
    }
    alert(msg);
}

main();