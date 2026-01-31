#!/usr/bin/env python3
"""
快递查询网站 - 简化版本
Express Tracking Website - Simplified Version
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# 创建FastAPI应用
app = FastAPI(
    title="快递查询网站",
    description="Express Tracking Website",
    version="1.0.0"
)

# 挂载静态文件
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """首页 - 快递查询界面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>快递查询网站</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .search-box {
                margin-bottom: 20px;
            }
            input[type="text"] {
                width: 70%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                width: 25%;
                padding: 12px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                margin-left: 10px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                display: none;
            }
            .loading {
                text-align: center;
                color: #666;
            }
            .error {
                color: #dc3545;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
            }
            .success {
                color: #155724;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚚 快递查询网站</h1>
            <div class="search-box">
                <input type="text" id="trackingNumber" placeholder="请输入快递单号..." />
                <button onclick="searchTracking()">查询</button>
            </div>
            <div id="result" class="result"></div>
        </div>

        <script>
            async function searchTracking() {
                const trackingNumber = document.getElementById('trackingNumber').value.trim();
                const resultDiv = document.getElementById('result');
                
                if (!trackingNumber) {
                    showResult('请输入快递单号', 'error');
                    return;
                }
                
                // 显示加载状态
                showResult('正在查询中...', 'loading');
                
                try {
                    const response = await fetch('/api/tracking/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            tracking_number: trackingNumber
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showResult(`查询成功！快递单号: ${data.data.tracking_number}`, 'success');
                    } else {
                        showResult(`查询失败: ${data.message}`, 'error');
                    }
                } catch (error) {
                    showResult('网络错误，请稍后重试', 'error');
                }
            }
            
            function showResult(message, type) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = message;
                resultDiv.className = `result ${type}`;
                resultDiv.style.display = 'block';
            }
            
            // 回车键查询
            document.getElementById('trackingNumber').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchTracking();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/api/tracking/query")
async def query_tracking(request: Request):
    """快递查询API"""
    try:
        data = await request.json()
        tracking_number = data.get("tracking_number", "").strip()
        
        if not tracking_number:
            return JSONResponse({
                "success": False,
                "message": "快递单号不能为空"
            })
        
        # 模拟查询结果（实际项目中这里会调用快递100 API）
        return JSONResponse({
            "success": True,
            "data": {
                "tracking_number": tracking_number,
                "company": "顺丰速运",
                "status": "运输中",
                "tracks": [
                    {
                        "time": "2024-01-26 10:00:00",
                        "location": "北京分拣中心",
                        "description": "快件已发出"
                    },
                    {
                        "time": "2024-01-26 08:00:00", 
                        "location": "北京收件点",
                        "description": "快件已收件"
                    }
                ]
            },
            "message": "查询成功"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"查询失败: {str(e)}"
        })

@app.get("/admin/")
async def admin_page():
    """后台管理页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>后台管理 - 快递查询网站</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .info {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 后台管理系统</h1>
            <div class="info">
                <h3>系统状态</h3>
                <p>✅ 快递查询网站运行正常</p>
                <p>✅ API服务可用</p>
                <p>📝 这是简化版本，完整功能请参考项目文档</p>
            </div>
            <div class="info">
                <h3>功能说明</h3>
                <ul>
                    <li>前台查询: <a href="/">点击访问</a></li>
                    <li>API文档: <a href="/docs">点击访问</a></li>
                    <li>完整版本包含理货单管理、文件上传等功能</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "快递查询网站运行正常"}

@app.get("/docs")
async def get_docs():
    """API文档重定向"""
    return {"message": "API文档功能需要完整版本"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动快递查询网站...")
    print("📍 访问地址:")
    print("   - 前台查询: http://localhost:8000/")
    print("   - 后台管理: http://localhost:8000/admin/")
    print("   - 健康检查: http://localhost:8000/health")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)