"""
应用程序启动脚本
Application Startup Script
"""

import uvicorn
from app.core.config_simple import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )