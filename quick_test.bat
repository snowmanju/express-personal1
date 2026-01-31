@echo off
chcp 65001 >nul
echo ========================================
echo 快递追踪系统快速测试
echo ========================================
echo.

echo [1/6] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ 错误: Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✓ Python环境正常
echo.

echo [2/6] 激活虚拟环境...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate
    echo ✓ 虚拟环境已激活
) else (
    echo ❌ 错误: 虚拟环境不存在
    echo 请先运行: python -m venv venv
    pause
    exit /b 1
)
echo.

echo [3/6] 检查关键依赖包...
python -c "import fastapi, pandas, sqlalchemy" 2>nul
if errorlevel 1 (
    echo ❌ 错误: 缺少必要的依赖包
    echo 运行安装命令: pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✓ 依赖包检查通过
echo.

echo [4/6] 检查数据库连接...
python -c "from app.core.database import engine; engine.connect()" 2>nul
if errorlevel 1 (
    echo ⚠ 警告: 数据库连接失败
    echo 请确保MySQL服务正在运行
    echo 命令: net start MySQL
) else (
    echo ✓ 数据库连接正常
)
echo.

echo [5/6] 运行单元测试...
echo 测试文件验证器...
python -m pytest test_file_validator_unit.py -v --tb=short -q
if errorlevel 1 (
    echo ❌ 文件验证器测试失败
) else (
    echo ✓ 文件验证器测试通过
)

echo.
echo 测试模板下载...
python -m pytest test_template_download.py -v --tb=short -q
if errorlevel 1 (
    echo ❌ 模板下载测试失败
) else (
    echo ✓ 模板下载测试通过
)
echo.

echo [6/6] 测试总结
echo ========================================
echo ✓ 环境检查完成
echo ✓ 单元测试完成
echo.
echo 下一步操作:
echo 1. 启动服务器: python run.py
echo 2. 访问管理后台: http://localhost:8000/admin/login.html
echo 3. 使用账户登录: admin / admin123
echo 4. 测试文件上传功能
echo.
echo 详细测试步骤请查看: 平台测试指南.md
echo ========================================
pause
