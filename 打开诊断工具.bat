@echo off
chcp 65001 >nul
echo ========================================
echo   登录问题诊断工具
echo ========================================
echo.
echo 正在打开诊断工具...
echo.
echo 诊断工具将在浏览器中打开
echo URL: http://localhost:8000/diagnose_login_issue.html
echo.
echo 使用说明:
echo 1. 点击"测试API连接"检查后端服务
echo 2. 点击"测试登录流程"模拟登录过程
echo 3. 点击"测试手动访问仪表板"验证Token
echo.
echo ========================================
echo.

start http://localhost:8000/diagnose_login_issue.html

echo 诊断工具已在浏览器中打开
echo.
echo 如果浏览器没有自动打开，请手动访问:
echo http://localhost:8000/diagnose_login_issue.html
echo.
pause
