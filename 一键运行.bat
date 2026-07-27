@echo off
chcp 65001 >nul
title TIA SCL Pipeline
setlocal

echo ============================================
echo  TIA SCL One-Click Pipeline v2.0
echo  Export -^> Comment -^> Import
echo ============================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tia_pipeline.ps1" -Mode full
if %errorlevel% neq 0 ( echo FAIL & pause & exit /b 1 )

echo.
echo === ALL DONE! ===
pause
