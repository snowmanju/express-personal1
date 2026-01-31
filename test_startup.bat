@echo off
chcp 65001 >nul
echo ========================================
echo 测试服务器启动
echo ========================================
echo.

echo 激活虚拟环境...
call venv\Scripts\activate
echo.

echo 尝试启动服务器...
echo 如果出现错误，请复制完整的错误信息
echo ========================================
echo.

python run.py

echo.
echo ========================================
echo 服务器已停止
echo.
echo 如果看到错误信息，请：
echo 1. 复制上面的完整错误信息
echo 2. 查看 服务器启动故障排查.md
echo 3. 或运行 fix_common_issues.bat 自动修复
echo ========================================
pause
