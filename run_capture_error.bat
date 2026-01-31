@echo off
chcp 65001 >nul
echo 正在捕获错误信息...
echo.

call venv\Scripts\activate
python capture_error.py

echo.
echo ========================================
echo 如果看到错误，请复制上面的所有内容
echo ========================================
pause
