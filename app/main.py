"""
FastAPI应用程序主入口点
Express Tracking Website Main Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config_simple import settings
from app.core.database import engine, Base
from app.core.session_middleware import SessionTimeoutMiddleware
from app.api.v1.api import api_router
from app.services.data_sync_service import data_sync_service
import logging
import os

# 配置日志
if os.getenv("ENVIRONMENT") == "production":
    from app.core.logging_config import setup_logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_dir="logs",
        enable_json_logging=True,
        enable_file_logging=True
    )
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="快递查询网站 - 提供快递单号查询和理货单管理功能",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加会话超时中间件
app.add_middleware(SessionTimeoutMiddleware)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 挂载管理后台静态文件
app.mount("/admin", StaticFiles(directory="static/admin", html=True), name="admin")

# 挂载客户端静态文件
app.mount("/customer", StaticFiles(directory="static/customer", html=True), name="customer")

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("快递查询网站启动中...")
    
    # 初始化数据同步服务
    try:
        # 数据同步服务已经是单例，这里只是确保它被初始化
        sync_stats = data_sync_service.get_sync_statistics()
        logger.info(f"数据同步服务初始化完成: {sync_stats}")
    except Exception as e:
        logger.error(f"数据同步服务初始化失败: {str(e)}")
    
    logger.info("快递查询网站启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("快递查询网站关闭中...")
    
    # 清理数据同步服务资源
    try:
        data_sync_service.clear_pending_sync_operations()
        logger.info("数据同步服务资源清理完成")
    except Exception as e:
        logger.error(f"数据同步服务资源清理失败: {str(e)}")
    
    logger.info("快递查询网站关闭完成")

@app.get("/")
async def root():
    """根路径，返回前台查询页面"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index_tech.html")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 包含数据同步服务的健康状态
        sync_health = await data_sync_service.health_check()
        return {
            "status": "healthy",
            "sync_service": sync_health
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "degraded",
            "error": str(e)
        }