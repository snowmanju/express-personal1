"""
API v1 路由聚合
API v1 Router Aggregation
"""

from fastapi import APIRouter
from app.api.v1 import tracking, auth, manifest, sync, health

# 创建API路由器
api_router = APIRouter()

# 包含快递查询相关路由
api_router.include_router(tracking.router, prefix="/tracking", tags=["tracking"])

# 包含认证相关路由
api_router.include_router(auth.router, prefix="/admin", tags=["admin", "auth"])

# 包含理货单管理相关路由
api_router.include_router(manifest.router, prefix="/admin/manifest", tags=["admin", "manifest"])

# 包含数据同步管理相关路由
api_router.include_router(sync.router, prefix="/admin/sync", tags=["admin", "sync"])

# 包含健康检查相关路由
api_router.include_router(health.router, tags=["health"])

@api_router.get("/")
async def api_info():
    """API信息端点"""
    return {
        "message": "快递查询网站 API v1",
        "endpoints": {
            "tracking": "/tracking - 快递查询相关接口",
            "admin": "/admin - 后台管理和认证相关接口",
            "manifest": "/admin/manifest - 理货单管理相关接口",
            "sync": "/admin/sync - 数据同步管理相关接口",
            "health": "/health - 健康检查和监控相关接口"
        }
    }