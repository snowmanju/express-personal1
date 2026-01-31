@echo off
chcp 65001 >nul
echo ========================================
echo 自动修复常见启动问题
echo ========================================
echo.

echo [1/6] 激活虚拟环境...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate
    echo ✓ 虚拟环境已激活
) else (
    echo ✗ 虚拟环境不存在
    echo 创建虚拟环境: python -m venv venv
    pause
    exit /b 1
)
echo.

echo [2/6] 更新pip...
python -m pip install --upgrade pip --quiet
echo ✓ pip已更新
echo.

echo [3/6] 检查并安装依赖...
echo 这可能需要几分钟...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ⚠ 依赖安装可能有问题
) else (
    echo ✓ 依赖已安装
)
echo.

echo [4/6] 检查MySQL服务...
net start | findstr /i "MySQL" >nul
if errorlevel 1 (
    echo ⚠ MySQL服务未运行
    echo 尝试启动MySQL...
    net start MySQL 2>nul
    if errorlevel 1 (
        echo ✗ 无法启动MySQL服务
        echo 请手动启动MySQL服务
        echo 方法1: 在服务管理器中启动
        echo 方法2: 命令行运行 net start MySQL
    ) else (
        echo ✓ MySQL服务已启动
    )
) else (
    echo ✓ MySQL服务正在运行
)
echo.

echo [5/6] 检查数据库...
echo 请输入MySQL root密码（如果需要）:
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS express_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
if errorlevel 1 (
    echo ⚠ 无法创建数据库（可能已存在或密码错误）
) else (
    echo ✓ 数据库检查完成
)
echo.

echo [6/6] 检查端口占用...
netstat -ano | findstr ":8000" >nul
if errorlevel 1 (
    echo ✓ 端口8000可用
) else (
    echo ⚠ 端口8000被占用
    echo 查看占用进程: netstat -ano | findstr :8000
    echo 结束进程: taskkill /PID <进程ID> /F
)
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 下一步:
echo 1. 运行: python run.py
echo 2. 如果还有问题，查看: 服务器启动故障排查.md
echo.
pause
