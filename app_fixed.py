#!/usr/bin/env python3
"""
快递查询网站 - 修复版本（正确处理快递100 API响应）
Express Tracking Website - Fixed Version with Correct API Response Handling
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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="快递查询网站",
    description="Express Tracking Website - Fixed Version",
    version="2.2.0"
)

class Kuaidi100Client:
    """快递100 API客户端 - 修复版"""
    
    def __init__(self):
        # API配置
        self.api_url = "https://poll.kuaidi100.com/poll/query.do"
        self.customer = os.getenv("KUAIDI100_CUSTOMER", "3564B6CF145FA93724CE18C1FB149036")
        self.key = os.getenv("KUAIDI100_KEY", "fypLxFrg3636")
        self.secret = os.getenv("KUAIDI100_SECRET", "8fa1052ba57e4d9ca0427938a77e2e30")
        self.userid = os.getenv("KUAIDI100_USERID", "a1ffc21f3de94cf5bdd908faf3bbc81d")
        self.timeout = 30.0
        
    def _generate_signature(self, param: str) -> str:
        """生成API签名"""
        sign_string = param + self.key + self.customer
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
    
    async def query_tracking(self, tracking_number: str, company_code: str = "auto") -> Dict[str, Any]:
        """查询快递信息 - 修复版本"""
        try:
            logger.info(f"查询快递单号: {tracking_number}, 快递公司: {company_code}")
            
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
            
            # 发送请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    data=request_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP请求失败，状态码: {response.status_code}",
                        "tracking_number": tracking_number
                    }
                
                # 解析响应
                try:
                    response_data = response.json()
                    logger.info(f"API响应: {response_data}")
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "服务器响应格式错误",
                        "tracking_number": tracking_number
                    }
                
                # 🔧 修复：正确检查API响应状态
                # 快递100 API成功时返回 status="200"，而不是 result=true
                api_status = response_data.get("status", "")
                
                if api_status != "200":
                    # 查询失败的情况
                    error_msg = response_data.get('message', '查询失败')
                    logger.error(f"API查询失败: status={api_status}, message={error_msg}")
                    
                    # 提供更友好的错误消息
                    if "不存在" in error_msg or "过期" in error_msg:
                        friendly_msg = "快递单号不存在或已过期"
                    elif "签名" in error_msg:
                        friendly_msg = "API配置错误"
                    elif "参数" in error_msg:
                        friendly_msg = "查询参数错误"
                    else:
                        friendly_msg = f"查询失败: {error_msg}"
                    
                    return {
                        "success": False,
                        "error": friendly_msg,
                        "tracking_number": tracking_number
                    }
                
                # 🎉 成功情况：status="200" 表示查询成功
                tracks = response_data.get("data", [])
                logger.info(f"查询成功，获取到 {len(tracks)} 条物流轨迹")
                
                # 格式化物流轨迹
                formatted_tracks = []
                for track in tracks:
                    # 提取地点信息（从context中解析）
                    context = track.get("context", "")
                    location = ""
                    
                    # 尝试从描述中提取地点信息
                    if "】" in context and "【" in context:
                        try:
                            location = context.split("【")[1].split("】")[0]
                        except:
                            location = "未知地点"
                    else:
                        location = "处理中"
                    
                    formatted_track = {
                        "time": track.get("ftime", track.get("time", "")),
                        "location": location,
                        "description": context,
                        "status": track.get("status", "")
                    }
                    formatted_tracks.append(formatted_track)
                
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
                status_text = state_map.get(str(state), f"状态{state}")
                
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
                    "api_message": response_data.get("message", "")
                }
                
                logger.info(f"查询成功: {tracking_number}, 状态: {status_text}, 轨迹数: {len(formatted_tracks)}")
                return result
                
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "网络请求超时，请稍后重试",
                "tracking_number": tracking_number
            }
        except Exception as e:
            logger.error(f"查询异常: {tracking_number}, 错误: {str(e)}")
            return {
                "success": False,
                "error": "系统异常，请稍后重试",
                "tracking_number": tracking_number
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
        <title>快递查询网站 - 修复版本</title>
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
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚚 快递查询网站 (修复版)</h1>
            <div class="tips">
                ✅ <strong>问题已修复：</strong>现在可以正确显示真实的快递物流轨迹信息了！
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
                        showResult(`查询失败: ${data.error || data.message}`, 'error');
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
                            <p><strong>快递公司：</strong>${data.company_name || '圆通速递'}</p>
                            <p><strong>当前状态：</strong><span class="status ${statusClass}">${data.status}</span></p>
                            <p><strong>查询时间：</strong>${new Date(data.query_time * 1000).toLocaleString()}</p>
                        </div>
                        <h3>🚛 物流轨迹 (${tracks.length}条记录)</h3>
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
    """快递查询API - 修复版本"""
    try:
        data = await request.json()
        tracking_number = data.get("tracking_number", "").strip()
        company_code = data.get("company_code", "auto")
        
        if not tracking_number:
            return JSONResponse({
                "success": False,
                "error": "快递单号不能为空"
            })
        
        # 调用快递100 API查询
        result = await kuaidi100_client.query_tracking(tracking_number, company_code)
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "data": result,
                "message": "查询成功"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "查询失败"),
                "tracking_number": tracking_number
            })
        
    except Exception as e:
        logger.error(f"API查询异常: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": "系统异常，请稍后重试"
        })

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "message": "快递查询网站运行正常 (修复版)",
        "api_integration": "快递100 API已修复",
        "version": "2.2.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动快递查询网站（修复版）...")
    print("📍 访问地址: http://localhost:8002/")
    print("✅ 修复内容:")
    print("   - 正确处理快递100 API响应格式")
    print("   - 修复status字段检查逻辑")
    print("   - 优化物流轨迹显示")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8002)