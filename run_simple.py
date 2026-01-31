#!/usr/bin/env python3
"""
快递查询网站启动脚本 - 简化版
Express Tracking Website Startup Script - Simplified Version
"""

import uvicorn
import os
from pathlib import Path

# 设置环境变量
os.environ.setdefault("DATABASE_URL", "sqlite:///./express_tracking.db")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production")
os.environ.setdefault("KUAIDI100_KEY", "fypLxFrg3636")
os.environ.setdefault("KUAIDI100_CUSTOMER", "3564B6CF145FA93724CE18C1FB149036")
os.environ.setdefault("KUAIDI100_SECRET", "8fa1052ba57e4d9ca0427938a77e2e30")
os.environ.setdefault("KUAIDI100_USERID", "a1ffc21f3de94cf5bdd908faf3bbc81d")

if __name__ == "__main__":
    print("🚀 启动快递查询网站...")
    print("📍 访问地址:")
    print("   - 前台查询: http://localhost:8000/")
    print("   - 后台管理: http://localhost:8000/admin/")
    print("   - API文档: http://localhost:8000/docs")
    print("   - 健康检查: http://localhost:8000/health")
    print()
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )