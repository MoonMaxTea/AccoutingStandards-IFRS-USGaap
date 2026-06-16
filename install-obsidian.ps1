# Obsidian 安装脚本 - 下载完成后运行此脚本
$installer = "$env:TEMP\Obsidian.Setup.exe"
if (Test-Path $installer) {
    $size = (Get-Item $installer).Length
    Write-Host "安装包: $size 字节"
    Write-Host "开始安装 Obsidian..."
    Start-Process -FilePath $installer -ArgumentList "/S" -Wait
    Write-Host "安装完成！启动 Obsidian 并选择 Vault 目录："
    Write-Host "  C:\Users\WINDOWS\Documents\Codex\2026-05-29\obsidian-codex"
} else {
    Write-Host "安装包尚未下载完成，请等待 BITS 传输完成"
    Get-BitsTransfer | Format-Table
}
