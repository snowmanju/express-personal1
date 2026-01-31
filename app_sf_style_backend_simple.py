#!/usr/bin/env python3
"""
快递查询网站 - 顺丰风格版本 + 简化后台管理系统
Express Tracking Website - SF Style Version with Simplified Backend Management
"""

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import os
import json
import hashlib
import time
import httpx
import asyncio
from pathlib import Path
import logging
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="快递查询网站",
    description="Express Tracking Website - SF Style with Simplified Backend",
    version="4.1.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTTP Bearer token scheme
security = HTTPBearer()

# 简化的配置
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 简化的用户存储（生产环境应使用数据库）
ADMIN_USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),  # 默认密码：admin123
        "created_at": datetime.now(),
        "last_login": None
    }
}

# 简化的理货单存储（生产环境应使用数据库）
MANIFESTS = []

class Kuaidi100Client:
    """快递100 API客户端"""
    
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
        """查询快递信息"""
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
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "服务器响应格式错误",
                        "tracking_number": tracking_number
                    }
                
                # 检查API响应状态
                api_status = response_data.get("status", "")
                
                if api_status != "200":
                    error_msg = response_data.get('message', '查询失败')
                    return {
                        "success": False,
                        "error": f"查询失败: {error_msg}",
                        "tracking_number": tracking_number
                    }
                
                # 处理成功响应
                tracks = response_data.get("data", [])
                
                # 格式化物流轨迹
                formatted_tracks = []
                for track in tracks:
                    # 提取地点信息
                    context = track.get("context", "")
                    location = ""
                    
                    if "】" in context and "【" in context:
                        try:
                            location = context.split("【")[1].split("】")[0]
                        except:
                            location = "处理中"
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
                    "is_check": response_data.get("ischeck", "0") == "1"
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

# 认证相关函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.JWTError:
        return None

def get_current_user(token: str):
    """根据令牌获取当前用户"""
    username = verify_token(token)
    if username is None:
        return None
    user = ADMIN_USERS.get(username)
    return user

# Authentication dependency
async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = security):
    """获取当前认证用户"""
    try:
        token = credentials.credentials
        user = get_current_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# ==================== 前台页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """首页 - 顺丰风格设计"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>快递查询网站 - 专业快递服务</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
            }
            
            /* 顶部导航栏 */
            .header {
                background: #fff;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
            }
            
            .nav-container {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 20px;
                height: 70px;
            }
            
            .logo {
                font-size: 28px;
                font-weight: bold;
                color: #ff6600;
                text-decoration: none;
            }
            
            .nav-menu {
                display: flex;
                list-style: none;
                gap: 30px;
            }
            
            .nav-menu a {
                text-decoration: none;
                color: #333;
                font-weight: 500;
                transition: color 0.3s;
            }
            
            .nav-menu a:hover {
                color: #ff6600;
            }
            
            .user-actions {
                display: flex;
                gap: 15px;
            }
            
            .login-btn, .register-btn {
                padding: 8px 20px;
                border-radius: 20px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s;
            }
            
            .login-btn {
                color: #ff6600;
                border: 1px solid #ff6600;
                background: transparent;
            }
            
            .login-btn:hover {
                background: #ff6600;
                color: white;
            }
            
            .register-btn {
                background: #ff6600;
                color: white;
                border: 1px solid #ff6600;
            }
            
            .register-btn:hover {
                background: #e55a00;
            }
            
            /* Banner区域 */
            .banner {
                background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
                color: white;
                padding: 120px 0 80px;
                text-align: center;
                margin-top: 70px;
            }
            
            .banner-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            .banner h1 {
                font-size: 48px;
                font-weight: 700;
                margin-bottom: 20px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .banner p {
                font-size: 20px;
                margin-bottom: 40px;
                opacity: 0.9;
            }
            
            /* 快递查询区域 */
            .tracking-section {
                background: white;
                margin: -40px auto 0;
                max-width: 800px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                padding: 40px;
                position: relative;
                z-index: 10;
            }
            
            .tracking-title {
                text-align: center;
                font-size: 24px;
                font-weight: 600;
                color: #333;
                margin-bottom: 30px;
            }
            
            .tracking-form {
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .tracking-input {
                flex: 1;
                padding: 15px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            .tracking-input:focus {
                outline: none;
                border-color: #ff6600;
            }
            
            .company-select {
                padding: 15px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                background: white;
                min-width: 150px;
            }
            
            .tracking-btn {
                padding: 15px 30px;
                background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                min-width: 120px;
            }
            
            .tracking-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255, 102, 0, 0.3);
            }
            
            .tracking-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .tracking-tips {
                text-align: center;
                color: #666;
                font-size: 14px;
                margin-top: 15px;
            }
            
            /* 查询结果区域 */
            .result-section {
                max-width: 1200px;
                margin: 40px auto;
                padding: 0 20px;
                display: none;
            }
            
            .result-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .result-header {
                background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
                color: white;
                padding: 25px;
            }
            
            .result-header h3 {
                font-size: 20px;
                margin-bottom: 15px;
            }
            
            .result-info {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .info-item {
                display: flex;
                flex-direction: column;
            }
            
            .info-label {
                font-size: 12px;
                opacity: 0.8;
                margin-bottom: 5px;
            }
            
            .info-value {
                font-size: 16px;
                font-weight: 600;
            }
            
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
            }
            
            .status-delivered { background: #4caf50; color: white; }
            .status-in-transit { background: #2196f3; color: white; }
            .status-picked-up { background: #ff9800; color: white; }
            .status-problem { background: #f44336; color: white; }
            .status-returning { background: #9c27b0; color: white; }
            .status-delivering { background: #00bcd4; color: white; }
            
            .timeline-section {
                padding: 30px;
            }
            
            .timeline-title {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 25px;
                color: #333;
            }
            
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
                background: #e0e0e0;
            }
            
            .timeline-item {
                position: relative;
                margin-bottom: 25px;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #ff6600;
            }
            
            .timeline-item::before {
                content: '';
                position: absolute;
                left: -22px;
                top: 25px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #ff6600;
                border: 3px solid white;
                box-shadow: 0 0 0 2px #ff6600;
            }
            
            .timeline-item:first-child::before {
                background: #4caf50;
                box-shadow: 0 0 0 2px #4caf50;
            }
            
            .timeline-time {
                color: #ff6600;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            
            .timeline-location {
                font-weight: 600;
                color: #333;
                margin-bottom: 8px;
            }
            
            .timeline-description {
                color: #666;
                line-height: 1.5;
            }
            
            /* 服务介绍区域 */
            .services-section {
                max-width: 1200px;
                margin: 80px auto;
                padding: 0 20px;
            }
            
            .section-title {
                text-align: center;
                font-size: 32px;
                font-weight: 700;
                color: #333;
                margin-bottom: 50px;
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
            }
            
            .service-card {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.3s;
            }
            
            .service-card:hover {
                transform: translateY(-5px);
            }
            
            .service-icon {
                font-size: 48px;
                color: #ff6600;
                margin-bottom: 20px;
            }
            
            .service-title {
                font-size: 20px;
                font-weight: 600;
                color: #333;
                margin-bottom: 15px;
            }
            
            .service-description {
                color: #666;
                line-height: 1.6;
            }
            
            /* 页脚 */
            .footer {
                background: #333;
                color: white;
                padding: 50px 0 30px;
                margin-top: 80px;
            }
            
            .footer-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 40px;
            }
            
            .footer-section h4 {
                font-size: 18px;
                margin-bottom: 20px;
                color: #ff6600;
            }
            
            .footer-section ul {
                list-style: none;
            }
            
            .footer-section ul li {
                margin-bottom: 10px;
            }
            
            .footer-section ul li a {
                color: #ccc;
                text-decoration: none;
                transition: color 0.3s;
            }
            
            .footer-section ul li a:hover {
                color: #ff6600;
            }
            
            .footer-bottom {
                text-align: center;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid #555;
                color: #999;
            }
            
            /* 响应式设计 */
            @media (max-width: 768px) {
                .nav-menu {
                    display: none;
                }
                
                .banner h1 {
                    font-size: 32px;
                }
                
                .banner p {
                    font-size: 16px;
                }
                
                .tracking-form {
                    flex-direction: column;
                }
                
                .result-info {
                    grid-template-columns: 1fr;
                }
            }
            
            /* 加载和错误状态 */
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            
            .error {
                background: #fff5f5;
                border: 1px solid #fed7d7;
                color: #c53030;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            
            .loading-spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #ff6600;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <!-- 顶部导航栏 -->
        <header class="header">
            <div class="nav-container">
                <a href="/" class="logo">🚚 快递查询</a>
                <nav>
                    <ul class="nav-menu">
                        <li><a href="#home">首页</a></li>
                        <li><a href="#tracking">快递查询</a></li>
                        <li><a href="#services">服务介绍</a></li>
                        <li><a href="#about">关于我们</a></li>
                        <li><a href="#contact">联系我们</a></li>
                    </ul>
                </nav>
                <div class="user-actions">
                    <a href="/static/admin/login.html" class="login-btn">用户登录</a>
                    <a href="/static/admin/login.html" class="register-btn">管理后台</a>
                </div>
            </div>
        </header>

        <!-- Banner区域 -->
        <section class="banner" id="home">
            <div class="banner-content">
                <h1>专业快递查询服务</h1>
                <p>快速、准确、实时的物流轨迹查询，支持全国主要快递公司</p>
            </div>
        </section>

        <!-- 快递查询区域 -->
        <section class="tracking-section" id="tracking">
            <h2 class="tracking-title">快递单号查询</h2>
            <div class="tracking-form">
                <input type="text" class="tracking-input" id="trackingNumber" placeholder="请输入快递单号..." />
                <select class="company-select" id="companyCode">
                    <option value="auto">自动识别</option>
                    <option value="shunfeng">顺丰速运</option>
                    <option value="yuantong">圆通速递</option>
                    <option value="shentong">申通快递</option>
                    <option value="zhongtong">中通快递</option>
                    <option value="yunda">韵达速递</option>
                    <option value="ems">EMS</option>
                    <option value="jingdong">京东快递</option>
                    <option value="huitongkuaidi">百世快递</option>
                </select>
                <button class="tracking-btn" id="searchBtn" onclick="searchTracking()">查询</button>
            </div>
            <div class="tracking-tips">
                支持顺丰、圆通、申通、中通、韵达等主流快递公司查询
            </div>
        </section>

        <!-- 查询结果区域 -->
        <section class="result-section" id="result">
            <!-- 查询结果将在这里动态显示 -->
        </section>

        <!-- 服务介绍区域 -->
        <section class="services-section" id="services">
            <h2 class="section-title">我们的服务</h2>
            <div class="services-grid">
                <div class="service-card">
                    <div class="service-icon">🔍</div>
                    <h3 class="service-title">实时查询</h3>
                    <p class="service-description">提供实时的快递物流轨迹查询，让您随时掌握包裹动态</p>
                </div>
                <div class="service-card">
                    <div class="service-icon">🚀</div>
                    <h3 class="service-title">快速响应</h3>
                    <p class="service-description">毫秒级响应速度，快速获取最新的物流信息</p>
                </div>
                <div class="service-card">
                    <div class="service-icon">🛡️</div>
                    <h3 class="service-title">安全可靠</h3>
                    <p class="service-description">采用加密传输，保护您的查询信息安全</p>
                </div>
                <div class="service-card">
                    <div class="service-icon">📱</div>
                    <h3 class="service-title">多端支持</h3>
                    <p class="service-description">支持电脑、手机、平板等多种设备访问</p>
                </div>
                <div class="service-card">
                    <div class="service-icon">🌐</div>
                    <h3 class="service-title">全网覆盖</h3>
                    <p class="service-description">支持国内主流快递公司，覆盖全国物流网络</p>
                </div>
                <div class="service-card">
                    <div class="service-icon">💬</div>
                    <h3 class="service-title">客服支持</h3>
                    <p class="service-description">7×24小时在线客服，随时为您解答疑问</p>
                </div>
            </div>
        </section>

        <!-- 页脚 -->
        <footer class="footer">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>快递查询</h4>
                    <ul>
                        <li><a href="#tracking">单号查询</a></li>
                        <li><a href="#services">服务介绍</a></li>
                        <li><a href="#about">关于我们</a></li>
                        <li><a href="#contact">联系我们</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4>快递公司</h4>
                    <ul>
                        <li><a href="#">顺丰速运</a></li>
                        <li><a href="#">圆通速递</a></li>
                        <li><a href="#">申通快递</a></li>
                        <li><a href="#">中通快递</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4>帮助中心</h4>
                    <ul>
                        <li><a href="#">使用指南</a></li>
                        <li><a href="#">常见问题</a></li>
                        <li><a href="#">意见反馈</a></li>
                        <li><a href="#">隐私政策</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4>联系方式</h4>
                    <ul>
                        <li>客服热线：400-888-8888</li>
                        <li>邮箱：service@express.com</li>
                        <li>地址：北京市朝阳区xxx路xxx号</li>
                        <li>工作时间：7×24小时</li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 快递查询网站. 保留所有权利.</p>
            </div>
        </footer>

        <script>
            async function searchTracking() {
                const trackingNumber = document.getElementById('trackingNumber').value.trim();
                const companyCode = document.getElementById('companyCode').value;
                const resultSection = document.getElementById('result');
                const searchBtn = document.getElementById('searchBtn');
                
                if (!trackingNumber) {
                    showError('请输入快递单号');
                    return;
                }
                
                // 禁用按钮，显示加载状态
                searchBtn.disabled = true;
                searchBtn.innerHTML = '<span class="loading-spinner"></span>查询中...';
                
                // 显示加载状态
                showLoading();
                
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
                        showError(data.error || '查询失败，请稍后重试');
                    }
                } catch (error) {
                    showError('网络错误，请检查网络连接后重试');
                } finally {
                    // 恢复按钮状态
                    searchBtn.disabled = false;
                    searchBtn.innerHTML = '查询';
                }
            }
            
            function showLoading() {
                const resultSection = document.getElementById('result');
                resultSection.innerHTML = `
                    <div class="result-card">
                        <div class="loading">
                            <div class="loading-spinner"></div>
                            正在查询快递信息，请稍候...
                        </div>
                    </div>
                `;
                resultSection.style.display = 'block';
                resultSection.scrollIntoView({ behavior: 'smooth' });
            }
            
            function showError(message) {
                const resultSection = document.getElementById('result');
                resultSection.innerHTML = `
                    <div class="result-card">
                        <div class="error">
                            ❌ 查询失败!<br>错误信息: ${message}
                        </div>
                    </div>
                `;
                resultSection.style.display = 'block';
                resultSection.scrollIntoView({ behavior: 'smooth' });
            }
            
            function showTrackingResult(data) {
                const statusClass = getStatusClass(data.status);
                const tracks = data.tracks || [];
                
                let timelineHtml = '';
                if (tracks.length > 0) {
                    tracks.forEach(track => {
                        timelineHtml += `
                            <div class="timeline-item">
                                <div class="timeline-time">${track.time}</div>
                                <div class="timeline-location">${track.location}</div>
                                <div class="timeline-description">${track.description}</div>
                            </div>
                        `;
                    });
                } else {
                    timelineHtml = '<div class="loading">暂无物流轨迹信息</div>';
                }
                
                const html = `
                    <div class="result-card">
                        <div class="result-header">
                            <h3>📦 快递信息</h3>
                            <div class="result-info">
                                <div class="info-item">
                                    <div class="info-label">快递单号</div>
                                    <div class="info-value">${data.tracking_number}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">快递公司</div>
                                    <div class="info-value">${data.company_name || '未知'}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">当前状态</div>
                                    <div class="info-value">
                                        <span class="status-badge ${statusClass}">${data.status}</span>
                                    </div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">查询时间</div>
                                    <div class="info-value">${new Date(data.query_time * 1000).toLocaleString()}</div>
                                </div>
                            </div>
                        </div>
                        <div class="timeline-section">
                            <h3 class="timeline-title">🚛 物流轨迹 (${tracks.length}条记录)</h3>
                            <div class="timeline">
                                ${timelineHtml}
                            </div>
                        </div>
                    </div>
                `;
                
                const resultSection = document.getElementById('result');
                resultSection.innerHTML = html;
                resultSection.style.display = 'block';
                resultSection.scrollIntoView({ behavior: 'smooth' });
            }
            
            function getStatusClass(status) {
                const statusMap = {
                    '已签收': 'status-delivered',
                    '在途': 'status-in-transit', 
                    '揽收': 'status-picked-up',
                    '疑难': 'status-problem',
                    '退签': 'status-returning',
                    '退回': 'status-returning',
                    '派件': 'status-delivering'
                };
                return statusMap[status] || 'status-in-transit';
            }
            
            // 回车键查询
            document.getElementById('trackingNumber').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchTracking();
                }
            });
            
            // 平滑滚动
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth'
                        });
                    }
                });
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

# ==================== 管理后台API路由 ====================

@app.post("/api/v1/admin/auth/login")
async def admin_login(request: Request):
    """管理员登录"""
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")
        
        # 检查用户是否存在
        user = ADMIN_USERS.get(username)
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 验证密码
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 更新最后登录时间
        user["last_login"] = datetime.now()
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        return JSONResponse({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_info": {
                "id": user["id"],
                "username": user["username"],
                "last_login": user["last_login"].isoformat() if user["last_login"] else None
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败")

@app.get("/api/v1/admin/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_admin_user)):
    """获取当前用户信息"""
    return JSONResponse({
        "id": current_user["id"],
        "username": current_user["username"],
        "created_at": current_user["created_at"].isoformat() if current_user["created_at"] else None,
        "last_login": current_user["last_login"].isoformat() if current_user["last_login"] else None
    })

@app.post("/api/v1/admin/manifest/upload")
async def upload_manifest_file(
    file: UploadFile = File(...),
    preview_only: bool = Form(False),
    current_user: dict = Depends(get_current_admin_user)
):
    """上传理货单文件（简化版本）"""
    try:
        # 验证文件大小（限制为10MB）
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
        
        # 简化的文件处理逻辑
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传CSV或Excel文件")
        
        # 模拟处理结果
        result = {
            "success": True,
            "message": "文件上传成功" if not preview_only else "文件预览成功",
            "statistics": {
                "total_rows": 100,
                "valid_rows": 95,
                "invalid_rows": 5,
                "inserted": 95 if not preview_only else 0,
                "updated": 0,
                "skipped": 5
            },
            "preview_data": [
                {
                    "row_number": 2,
                    "data": {
                        "快递单号": "YT1234567890",
                        "理货日期": "2024-01-26",
                        "运输代码": "SF001",
                        "客户代码": "CUST001",
                        "货物代码": "GOODS001"
                    },
                    "valid": True,
                    "errors": []
                }
            ] if preview_only else []
        }
        
        # 记录操作日志
        logger.info(f"用户 {current_user['username']} 上传理货单文件: {file.filename}")
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.get("/api/v1/admin/manifest/search")
async def search_manifests(
    q: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    transport_code: Optional[str] = Query(None, description="运输代码过滤"),
    customer_code: Optional[str] = Query(None, description="客户代码过滤"),
    current_user: dict = Depends(get_current_admin_user)
):
    """搜索理货单记录（简化版本）"""
    try:
        # 模拟搜索结果
        mock_manifests = [
            {
                "id": 1,
                "tracking_number": "YT1234567890",
                "package_number": "PKG001",
                "manifest_date": "2024-01-26",
                "transport_code": "SF001",
                "customer_code": "CUST001",
                "goods_code": "GOODS001",
                "weight": 1.5,
                "length": 20.0,
                "width": 15.0,
                "height": 10.0,
                "special_fee": 0.0,
                "created_at": "2024-01-26T10:00:00",
                "updated_at": "2024-01-26T10:00:00"
            },
            {
                "id": 2,
                "tracking_number": "ZT9876543210",
                "package_number": "PKG002",
                "manifest_date": "2024-01-26",
                "transport_code": "ZT001",
                "customer_code": "CUST002",
                "goods_code": "GOODS002",
                "weight": 2.0,
                "length": 25.0,
                "width": 20.0,
                "height": 15.0,
                "special_fee": 5.0,
                "created_at": "2024-01-26T11:00:00",
                "updated_at": "2024-01-26T11:00:00"
            }
        ]
        
        # 简单的过滤逻辑
        filtered_manifests = mock_manifests
        if q:
            filtered_manifests = [m for m in filtered_manifests if q.lower() in m["tracking_number"].lower()]
        if transport_code:
            filtered_manifests = [m for m in filtered_manifests if m["transport_code"] == transport_code]
        if customer_code:
            filtered_manifests = [m for m in filtered_manifests if m["customer_code"] == customer_code]
        
        # 分页
        total_count = len(filtered_manifests)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_manifests = filtered_manifests[start_idx:end_idx]
        
        result = {
            "success": True,
            "data": page_manifests,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": end_idx < total_count,
                "has_prev": page > 1
            },
            "search_query": q,
            "filters": {
                "transport_code": transport_code,
                "customer_code": customer_code
            }
        }
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"搜索理货单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/api/v1/admin/manifest/statistics")
async def get_manifest_statistics(current_user: dict = Depends(get_current_admin_user)):
    """获取理货单统计信息（简化版本）"""
    try:
        # 模拟统计数据
        result = {
            "success": True,
            "data": {
                "total_count": 1250,
                "recent_count": 45,
                "unique_customers": 25,
                "unique_transports": 8,
                "with_package_count": 1100,
                "without_package_count": 150,
                "package_rate": 88.0
            }
        }
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.get("/api/v1/admin/manifest/{manifest_id}")
async def get_manifest(
    manifest_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取理货单详情（简化版本）"""
    try:
        # 模拟理货单数据
        mock_manifest = {
            "id": manifest_id,
            "tracking_number": "YT1234567890",
            "package_number": "PKG001",
            "manifest_date": "2024-01-26",
            "transport_code": "SF001",
            "customer_code": "CUST001",
            "goods_code": "GOODS001",
            "weight": 1.5,
            "length": 20.0,
            "width": 15.0,
            "height": 10.0,
            "special_fee": 0.0,
            "created_at": "2024-01-26T10:00:00",
            "updated_at": "2024-01-26T10:00:00"
        }
        
        result = {
            "success": True,
            "data": mock_manifest
        }
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"获取理货单详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@app.put("/api/v1/admin/manifest/{manifest_id}")
async def update_manifest(
    manifest_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user)
):
    """更新理货单记录（简化版本）"""
    try:
        data = await request.json()
        
        # 模拟更新逻辑
        result = {
            "success": True,
            "data": {
                "id": manifest_id,
                "tracking_number": data.get("tracking_number", "YT1234567890")
            },
            "message": "理货单更新成功"
        }
        
        # 记录操作日志
        logger.info(f"用户 {current_user['username']} 更新理货单: {manifest_id}")
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"更新理货单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@app.delete("/api/v1/admin/manifest/{manifest_id}")
async def delete_manifest(
    manifest_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除理货单记录（简化版本）"""
    try:
        # 模拟删除逻辑
        result = {
            "success": True,
            "data": {
                "id": manifest_id,
                "tracking_number": "YT1234567890"
            },
            "message": "理货单删除成功"
        }
        
        # 记录操作日志
        logger.info(f"用户 {current_user['username']} 删除理货单: {manifest_id}")
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"删除理货单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.delete("/api/v1/admin/manifest/batch")
async def batch_delete_manifests(
    request: Request,
    current_user: dict = Depends(get_current_admin_user)
):
    """批量删除理货单记录（简化版本）"""
    try:
        data = await request.json()
        manifest_ids = data.get("manifest_ids", [])
        
        if not manifest_ids:
            raise HTTPException(status_code=400, detail="未指定要删除的记录")
        
        # 模拟批量删除逻辑
        result = {
            "success": True,
            "data": {
                "deleted_count": len(manifest_ids),
                "deleted_ids": manifest_ids,
                "deleted_tracking_numbers": [f"YT{i}" for i in manifest_ids]
            },
            "message": f"成功删除{len(manifest_ids)}条理货单记录"
        }
        
        # 记录操作日志
        logger.info(f"用户 {current_user['username']} 批量删除理货单: {len(manifest_ids)}条记录")
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除理货单失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")

# ==================== 管理后台页面路由 ====================

@app.get("/admin/", response_class=HTMLResponse)
async def admin_login_page():
    """管理后台登录页面"""
    return FileResponse("static/admin/login.html")

@app.get("/admin/dashboard.html", response_class=HTMLResponse)
async def admin_dashboard_page():
    """管理后台仪表板页面"""
    return FileResponse("static/admin/dashboard.html")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "message": "快递查询网站运行正常 (顺丰风格版 + 简化后台)",
        "api_integration": "快递100 API已集成",
        "backend_features": "简化版认证、文件上传、理货单管理已集成",
        "admin_credentials": "用户名: admin, 密码: admin123",
        "version": "4.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动快递查询网站（顺丰风格版 + 简化后台管理系统）...")
    print("📍 访问地址: http://localhost:8005/")
    print("✨ 新特性:")
    print("   - 参考顺丰官网设计风格")
    print("   - 专业的Banner和导航栏")
    print("   - 完整的服务介绍页面")
    print("   - 用户登录和管理后台链接")
    print("   - 响应式设计支持移动端")
    print("   - 简化版后台管理系统:")
    print("     * 管理员认证和会话管理")
    print("     * 理货单文件上传（模拟）")
    print("     * 理货单搜索、编辑、删除（模拟）")
    print("     * 数据统计和预览功能（模拟）")
    print("   - 管理后台地址: http://localhost:8005/static/admin/login.html")
    print("   - 默认管理员账号: admin / admin123")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8005)