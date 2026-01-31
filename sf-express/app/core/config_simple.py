"""
简化配置文件 - 不依赖外部库
Simplified Configuration - No External Dependencies
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Settings:
    """应用程序设置类"""
    
    # 项目基本信息
    PROJECT_NAME: str = "快递查询网站"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:password@localhost:3306/express_tracking"
    )
    
    # 快递100 API配置
    KUAIDI100_KEY: str = os.getenv("KUAIDI100_KEY", "fypLxFrg3636")
    KUAIDI100_CUSTOMER: str = os.getenv("KUAIDI100_CUSTOMER", "3564B6CF145FA93724CE18C1FB149036")
    KUAIDI100_SECRET: str = os.getenv("KUAIDI100_SECRET", "8fa1052ba57e4d9ca0427938a77e2e30")
    KUAIDI100_USERID: str = os.getenv("KUAIDI100_USERID", "a1ffc21f3de94cf5bdd908faf3bbc81d")
    KUAIDI100_API_URL: str = "https://poll.kuaidi100.com/poll/query.do"
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    UPLOAD_DIR: str = "uploads"
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# 创建全局设置实例
settings = Settings()