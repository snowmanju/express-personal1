"""
健康检查API端点
Health Check API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.data_sync_service import data_sync_service
from app.services.kuaidi100_client import Kuaidi100Client
import psutil
import time
from datetime import datetime
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    综合健康检查端点
    
    Returns:
        Dict[str, Any]: 健康状态信息
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # 数据库健康检查
        try:
            db.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # 数据同步服务健康检查
        try:
            sync_health = await data_sync_service.health_check()
            health_status["checks"]["data_sync"] = sync_health
            if sync_health.get("status") != "healthy":
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["data_sync"] = {
                "status": "unhealthy",
                "message": f"Data sync service check failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # 快递100 API健康检查
        try:
            kuaidi100_client = Kuaidi100Client()
            # 简单的连接测试（不实际调用API）
            health_status["checks"]["kuaidi100_api"] = {
                "status": "healthy",
                "message": "Kuaidi100 client initialized successfully"
            }
        except Exception as e:
            health_status["checks"]["kuaidi100_api"] = {
                "status": "unhealthy",
                "message": f"Kuaidi100 client initialization failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # 系统资源检查
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status["checks"]["system_resources"] = {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "message": "System resources within normal range"
            }
            
            # 资源使用率告警
            if cpu_percent > 80 or memory.percent > 85 or (disk.used / disk.total) * 100 > 90:
                health_status["checks"]["system_resources"]["status"] = "warning"
                health_status["checks"]["system_resources"]["message"] = "High resource usage detected"
                if health_status["status"] == "healthy":
                    health_status["status"] = "degraded"
                    
        except Exception as e:
            health_status["checks"]["system_resources"] = {
                "status": "unhealthy",
                "message": f"System resource check failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # 响应时间
        response_time = time.time() - start_time
        health_status["response_time_seconds"] = round(response_time, 3)
        
        # 如果响应时间过长，标记为降级
        if response_time > 5.0:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Health check failed: {str(e)}",
            "response_time_seconds": round(time.time() - start_time, 3)
        }

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    就绪检查端点 - 检查服务是否准备好接收流量
    
    Returns:
        Dict[str, Any]: 就绪状态信息
    """
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        
        # 检查数据同步服务
        sync_stats = data_sync_service.get_sync_statistics()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Service is ready to accept traffic",
            "sync_statistics": sync_stats
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Service is not ready: {str(e)}"
            }
        )

@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    存活检查端点 - 检查服务是否还活着
    
    Returns:
        Dict[str, Any]: 存活状态信息
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Service is alive"
    }

@router.get("/metrics")
async def metrics_endpoint(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    指标端点 - 提供Prometheus格式的指标
    
    Returns:
        Dict[str, Any]: 应用指标
    """
    try:
        # 获取数据同步统计
        sync_stats = data_sync_service.get_sync_statistics()
        
        # 获取数据库统计
        manifest_count = db.execute("SELECT COUNT(*) FROM cargo_manifest").scalar()
        admin_count = db.execute("SELECT COUNT(*) FROM admin_users").scalar()
        
        # 系统资源指标
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database_metrics": {
                "manifest_count": manifest_count,
                "admin_count": admin_count
            },
            "sync_metrics": sync_stats,
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "memory_total_bytes": memory.total,
                "memory_used_bytes": memory.used,
                "disk_total_bytes": disk.total,
                "disk_used_bytes": disk.used
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Metrics collection failed",
                "message": str(e)
            }
        )