# Set UTF-8 encoding for PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

Write-Host "UTF-8 encoding has been successfully set" -ForegroundColor Green
Write-Host "Current directory: $PWD" -ForegroundColor Cyan
Write-Host "Test Cyrillic: Проверка кириллицы" -ForegroundColor Yellow 