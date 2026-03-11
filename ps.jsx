#target photoshop

function main(){

    // 1. 选择文件 (支持 PNG 或 TIF)
    var file = File.openDialog("选择 PNG 或 TIF 图片","PNG:*.png,TIFF:*.tif;*.tiff");
    if(!file) return;

    // 2. 打开文档
    var doc = open(file);

    // 3. 修改画布宽度为 56 厘米 (保持原图居中)
    // 记录原始单位，处理完后再恢复
    var originalUnit = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.CM; // 切换单位为厘米
    
    try {
        // 设置画布大小：宽度 56cm，高度保持不变，锚点在中心
        doc.resizeCanvas(56, doc.height.as("cm"), AnchorPosition.MIDDLECENTER);
    } catch(e) {
        alert("修改画布大小失败: " + e);
    } finally {
        // 恢复原始单位
        app.preferences.rulerUnits = originalUnit;
    }

    // 4. 执行动作 (动作组名: 印花, 动作名: 白墨通道)
    try {
        app.doAction("白墨通道", "印花");
    } catch(e) {
        alert("执行动作失败！请确保 Photoshop 中已存在名为 '印花' 的动作组和名为 '白墨通道' 的动作。\n错误详情: " + e);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        return;
    }

    // 4. 保存为 TIFF (格式: 原文件名-channel.tif)
    // 移除原有扩展名并添加后缀
    var newName = file.name.replace(/\.(png|tif|tiff)$/i, "") + "-channel.tif";
    var saveFile = new File(file.path + "/" + newName);

    var opt = new TiffSaveOptions();
    opt.layers = false;             // 不保存图层，减小体积
    opt.imageCompression = TIFFEncoding.TIFFLZW; // 建议使用 LZW 压缩，预览更兼容
    opt.alphaChannels = true;       // 必须开启以保留 Alpha 通道 (包含 W1 专色)
    opt.spotColors = true;          // 必须开启以保留 W1 专色通道
    opt.transparency = true;        // 关键：保留透明度，解决背景变白的问题
    opt.embedColorProfile = true;   // 嵌入色彩配置文件，解决颜色变黑的问题

    doc.saveAs(saveFile, opt, true);

    // 5. 关闭
    doc.close(SaveOptions.DONOTSAVECHANGES);

    alert("处理完成！文件已保存至:\n" + saveFile.fsName);
}

main();