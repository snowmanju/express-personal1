#!/usr/bin/env python3
"""
快递查询网站 - 调试版本（增强错误处理和日志）
Express Tracking Website - Debug Version with Enhanced Error Handling
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import hashlib
import time
import httpx
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="快递查询网站",
    description="Express Tracking Website with Enhanced Debug",
    version="2.1.0"
)

class Kuaidi100Client:
    """快递100 API客户端 - 调试增强版"""
    
    def __init__(self):
        # API配置
        self.api_url = "https://poll.kuaidi100.com/poll/query.do"
        self.customer = os.getenv("KUAIDI100_CUSTOMER", "3564B6CF145FA93724CE18C1FB149036")
        self.key = os.getenv("KUAIDI100_KEY", "fypLxFrg3636")
        self.secret = os.getenv("KUAIDI100_SECRET", "8fa1052ba57e4d9ca0427938a77e2e30")
        self.userid = os.getenv("KUAIDI100_USERID", "a1ffc21f3de94cf5bdd908faf3bbc81d")
        self.timeout = 30.0
        
        logger.info(f"快递100客户端初始化:")
        logger.info(f"  - API URL: {self.api_url}")
        logger.info(f"  - Customer: {self.customer}")
        logger.info(f"  - Key: {self.key}")
        
    def _generate_signature(self, param: str) -> str:
        """生成API签名"""
        sign_string = param + self.key + self.customer
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
        logger.debug(f"签名生成:")
        logger.debug(f"  - 参数: {param}")
        logger.debug(f"  - 签名字符串: {sign_string}")
        logger.debug(f"  - 签名结果: {signature}")
        return signature
    
    async def query_tracking(self, tracking_number: str, company_code: str = "auto") -> Dict[str, Any]:
        """查询快递信息 - 增强调试版"""
        try:
            logger.info(f"开始查询快递单号: {tracking_number}, 快递公司: {company_code}")
            
            # 构建查询参数
            param_data = {
                "com": company_code,
                "num": tracking_number
            }
            
            param = json.dumps(param_data, separators=(',', ':'), ensure_ascii=False)
            signature = self._generate_signature(param)
            
            # 构建请求数据
            request_data = {
                "customer": self.customer,
                "sign": signature,
                "param": param
            }
            
            logger.info(f"请求数据: {request_data}")
            
            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"发送HTTP请求到: {self.api_url}")
                response = await client.post(
                    self.api_url,
                    data=request_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                logger.info(f"HTTP响应状态码: {response.status_code}")
                logger.info(f"HTTP响应头: {dict(response.headers)}")
                
                if response.status_code != 200:
                    error_msg = f"HTTP请求失败，状态码: {response.status_code}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "tracking_number": tracking_number,
                        "debug_info": {
                            "status_code": response.status_code,
                            "response_text": response.text[:500]
                        }
                    }
                
                # 获取原始响应文本
                response_text = response.text
                logger.info(f"原始响应内容: {response_text}")
                
                # 解析响应
                try:
                    response_data = response.json()
                    logger.info(f"解析后的JSON数据: {response_data}")
                except json.JSONDecodeError as e:
                    error_msg = f"服务器响应格式错误: {str(e)}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "tracking_number": tracking_number,
                        "debug_info": {
                            "response_text": response_text[:500]
                        }
                    }
                
                # 检查API响应状态
                result_status = response_data.get('result')
                logger.info(f"API响应result字段: {result_status}")
                
                if not result_status:
                    error_msg = response_data.get('message', '查询失败')
                    return_code = response_data.get('returnCode', '')
                    
                    logger.error(f"API查询失败:")
                    logger.error(f"  - 错误消息: {error_msg}")
                    logger.error(f"  - 返回码: {return_code}")
                    logger.error(f"  - 完整响应: {response_data}")
                    
                    # 提供更详细的错误信息
                    detailed_error = f"API返回错误: {error_msg}"
                    if return_code:
                        detailed_error += f" (错误码: {return_code})"
                    
                    return {
                        "success": False,
                        "error": detailed_error,
                        "tracking_number": tracking_number,
                        "debug_info": {
                            "api_response": response_data,
                            "return_code": return_code,
                            "original_message": error_msg
                        }
                    }
                
                # 处理成功响应
                tracks = response_data.get("data", [])
                logger.info(f"获取到 {len(tracks)} 条物流轨迹")
                
                # 格式化物流轨迹
                formatted_tracks = []
                for i, track in enumerate(tracks):
                    formatted_track = {
                        "time": track.get("ftime", ""),
                        "location": track.get("areaName", ""),
                        "description": track.get("context", ""),
                        "status": track.get("status", "")
                    }
                    formatted_tracks.append(formatted_track)
                    logger.debug(f"轨迹 {i+1}: {formatted_track}")
                
                # 获取状态描述
                state_map = {
                    "0": "在途",
                    "1": "揽收", 
                    "2": "疑难",
                    "3": "已签收",
                    "4": "退签",
                    "5": "派件",
                    "6": "退回"
                }
                
                state = response_data.get("state", "0")
                status_text = state_map.get(str(state), f"未知状态({state})")
                
                result = {
                    "success": True,
                    "tracking_number": tracking_number,
                    "company_code": company_code,
                    "company_name": response_data.get("com", ""),
                    "status": status_text,
                    "state_code": state,
                    "tracks": formatted_tracks,
                    "query_time": int(time.time()),
                    "is_check": response_data.get("ischeck", "0") == "1",
                    "debug_info": {
                        "api_response": response_data
                    }
                }
                
                logger.info(f"查询成功: {tracking_number}, 状态: {status_text}, 轨迹数: {len(formatted_tracks)}")
                return result
                
        except httpx.TimeoutException as e:
            error_msg = f"网络请求超时: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "网络请求超时，请稍后重试",
                "tracking_number": tracking_number,
                "debug_info": {
                    "exception": str(e)
                }
            }
        except httpx.RequestError as e:
            error_msg = f"网络请求错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "网络连接失败，请检查网络后重试",
                "tracking_number": tracking_number,
                "debug_info": {
                    "exception": str(e)
                }
            }
        except Exception as e:
            error_msg = f"查询异常: {tracking_number}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": "系统异常，请稍后重试",
                "tracking_number": tracking_number,
                "debug_info": {
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            }

# 创建快递100客户端实例
kuaidi100_client = Kuaidi100Client()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """首页 - 快递查询界面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>快递查询网站 - 调试版本</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .search-box {
                margin-bottom: 30px;
                display: flex;
                gap: 10px;
            }
            input[type="text"] {
                flex: 1;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus {
                border-color: #667eea;
                outline: none;
            }
            select {
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                background: white;
            }
            button {
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .result {
                margin-top: 20px;
                display: none;
            }
            .loading {
                text-align: center;
                color: #666;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .error {
                color: #dc3545;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 15px;
                border-radius: 8px;
            }
            .debug-info {
                margin-top: 15px;
                padding: 10px;
                background: #f1f3f4;
                border-radius: 5px;
                font-size: 12px;
                color: #666;
                max-height: 200px;
                overflow-y: auto;
            }
            .debug-toggle {
                margin-top: 10px;
                padding: 5px 10px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                cursor: pointer;
            }
            .success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 8px;
                padding: 20px;
            }
            .tracking-info {
                margin-bottom: 20px;
                padding: 15px;
                background: #e3f2fd;
                border-radius: 8px;
            }
            .tracking-info h3 {
                margin: 0 0 10px 0;
                color: #1976d2;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                margin-left: 10px;
            }
            .status.delivered { background: #4caf50; }
            .status.in-transit { background: #2196f3; }
            .status.picked-up { background: #ff9800; }
            .status.problem { background: #f44336; }
            .status.returning { background: #9c27b0; }
            .status.delivering { background: #00bcd4; }
            .timeline {
                position: relative;
                padding-left: 30px;
            }
            .timeline::before {
                content: '';
                position: absolute;
                left: 15px;
                top: 0;
                bottom: 0;
                width: 2px;
                background: #ddd;
            }
            .timeline-item {
                position: relative;
                margin-bottom: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .timeline-item::before {
                content: '';
                position: absolute;
                left: -22px;
                top: 20px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #2196f3;
                border: 3px solid white;
                box-shadow: 0 0 0 2px #2196f3;
            }
            .timeline-item:first-child::before {
                background: #4caf50;
                box-shadow: 0 0 0 2px #4caf50;
            }
            .timeline-time {
                color: #666;
                font-size: 14px;
                margin-bottom: 5px;
            }
            .timeline-location {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            .timeline-description {
                color: #555;
                line-height: 1.4;
            }
            .tips {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚚 快递查询网站 (调试版)</h1>
            <div class="tips">
                🔧 <strong>调试版本：</strong>此版本包含详细的错误信息和调试日志，帮助诊断查询问题。
            </div>
            <div class="search-box">
                <input type="text" id="trackingNumber" placeholder="请输入快递单号..." value="YT8834090695021" />
                <select id="companyCode">
                    <option value="auto">自动识别</option>
                    <option value="yuantong" selected>圆通速递</option>
                    <option value="shunfeng">顺丰速运</option>
                    <option value="shentong">申通快递</option>
                    <option value="zhongtong">中通快递</option>
                    <option value="yunda">韵达速递</option>
                    <option value="ems">EMS</option>
                    <option value="jingdong">京东快递</option>
                    <option value="huitongkuaidi">百世快递</option>
                </select>
                <button id="searchBtn" onclick="searchTracking()">查询</button>
            </div>
            <div id="result" class="result"></div>
        </div>

        <script>
            async function searchTracking() {
                const trackingNumber = document.getElementById('trackingNumber').value.trim();
                const companyCode = document.getElementById('companyCode').value;
                const resultDiv = document.getElementById('result');
                const searchBtn = document.getElementById('searchBtn');
                
                if (!trackingNumber) {
                    showResult('请输入快递单号', 'error');
                    return;
                }
                
                // 禁用按钮，显示加载状态
                searchBtn.disabled = true;
                searchBtn.textContent = '查询中...';
                showResult('正在查询快递信息，请稍候...', 'loading');
                
                try {
                    const response = await fetch('/api/tracking/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            tracking_number: trackingNumber,
                            company_code: companyCode
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        showTrackingResult(data.data);
                    } else {
                        showErrorResult(data);
                    }
                } catch (error) {
                    showResult('网络错误，请检查网络连接后重试', 'error');
                } finally {
                    // 恢复按钮状态
                    searchBtn.disabled = false;
                    searchBtn.textContent = '查询';
                }
            }
            
            function showResult(message, type) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `<div class="${type}">${message}</div>`;
                resultDiv.style.display = 'block';
            }
            
            function showErrorResult(data) {
                const debugInfo = data.debug_info || {};
                let debugHtml = '';
                
                if (Object.keys(debugInfo).length > 0) {
                    debugHtml = `
                        <button class="debug-toggle" onclick="toggleDebug(this)">显示调试信息</button>
                        <div class="debug-info" style="display: none;">
                            <strong>调试信息：</strong><br>
                            <pre>${JSON.stringify(debugInfo, null, 2)}</pre>
                        </div>
                    `;
                }
                
                const html = `
                    <div class="error">
                        <strong>查询失败：</strong>${data.error || data.message}
                        <br><strong>快递单号：</strong>${data.tracking_number || '未知'}
                        ${debugHtml}
                    </div>
                `;
                
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = html;
                resultDiv.style.display = 'block';
            }
            
            function toggleDebug(button) {
                const debugDiv = button.nextElementSibling;
                if (debugDiv.style.display === 'none') {
                    debugDiv.style.display = 'block';
                    button.textContent = '隐藏调试信息';
                } else {
                    debugDiv.style.display = 'none';
                    button.textContent = '显示调试信息';
                }
            }
            
            function showTrackingResult(data) {
                const statusClass = getStatusClass(data.status);
                const tracks = data.tracks || [];
                
                let tracksHtml = '';
                if (tracks.length > 0) {
                    tracksHtml = '<div class="timeline">';
                    tracks.forEach(track => {
                        tracksHtml += `
                            <div class="timeline-item">
                                <div class="timeline-time">${track.time}</div>
                                <div class="timeline-location">${track.location}</div>
                                <div class="timeline-description">${track.description}</div>
                            </div>
                        `;
                    });
                    tracksHtml += '</div>';
                } else {
                    tracksHtml = '<div style="text-align: center; color: #666; padding: 20px;">暂无物流轨迹信息</div>';
                }
                
                const html = `
                    <div class="success">
                        <div class="tracking-info">
                            <h3>📦 快递信息</h3>
                            <p><strong>快递单号：</strong>${data.tracking_number}</p>
                            <p><strong>快递公司：</strong>${data.company_name || '未知'}</p>
                            <p><strong>当前状态：</strong><span class="status ${statusClass}">${data.status}</span></p>
                            <p><strong>查询时间：</strong>${new Date(data.query_time * 1000).toLocaleString()}</p>
                        </div>
                        <h3>🚛 物流轨迹</h3>
                        ${tracksHtml}
                    </div>
                `;
                
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = html;
                resultDiv.style.display = 'block';
            }
            
            function getStatusClass(status) {
                const statusMap = {
                    '已签收': 'delivered',
                    '在途': 'in-transit', 
                    '揽收': 'picked-up',
                    '疑难': 'problem',
                    '退签': 'returning',
                    '退回': 'returning',
                    '派件': 'delivering'
                };
                return statusMap[status] || 'in-transit';
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
    """快递查询API - 调试增强版"""
    try:
        data = await request.json()
        tracking_number = data.get("tracking_number", "").strip()
        company_code = data.get("company_code", "auto")
        
        logger.info(f"收到查询请求: 单号={tracking_number}, 公司={company_code}")
        
        if not tracking_number:
            return JSONResponse({
                "success": False,
                "error": "快递单号不能为空"
            })
        
        # 调用快递100 API查询
        result = await kuaidi100_client.query_tracking(tracking_number, company_code)
        
        if result["success"]:
            logger.info(f"查询成功返回结果")
            return JSONResponse({
                "success": True,
                "data": result,
                "message": "查询成功"
            })
        else:
            logger.error(f"查询失败: {result}")
            return JSONResponse({
                "success": False,
                "error": result.get("error", "查询失败"),
                "tracking_number": tracking_number,
                "debug_info": result.get("debug_info", {})
            })
        
    except Exception as e:
        logger.error(f"API查询异常: {str(e)}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": "系统异常，请稍后重试",
            "debug_info": {
                "exception": str(e),
                "exception_type": type(e).__name__
            }
        })

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "message": "快递查询网站运行正常 (调试版)",
        "api_integration": "快递100 API已集成",
        "debug_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动快递查询网站（调试版）...")
    print("📍 访问地址: http://localhost:8000/")
    print("🔧 调试功能:")
    print("   - 详细错误日志")
    print("   - API响应调试信息")
    print("   - 前端调试面板")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")