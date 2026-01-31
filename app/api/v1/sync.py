"""
数据同步管理API端点 (Data Synchronization Management API)
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.services.data_sync_service import data_sync_service
from app.services.intelligent_query_service import IntelligentQueryService
from app.models.admin_user import AdminUser

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/statistics")
async def get_sync_statistics(
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取数据同步统计信息
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        同步统计信息
    """
    try:
        # 获取同步服务统计信息
        sync_stats = data_sync_service.get_sync_statistics()
        
        # 获取查询服务统计信息
        query_service = IntelligentQueryService(db)
        query_stats = query_service.get_query_statistics()
        
        return {
            "success": True,
            "data": {
                "sync_service": sync_stats,
                "query_service": query_stats,
                "timestamp": data_sync_service._sync_stats.get('last_sync_time')
            }
        }
        
    except Exception as e:
        logger.error(f"获取同步统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/pending-operations")
async def get_pending_sync_operations(
    limit: int = Query(100, ge=1, le=1000, description="返回记录数限制"),
    current_user: AdminUser = Depends(get_current_active_user)
):
    """
    获取待处理的同步操作
    
    Args:
        limit: 返回记录数限制
        current_user: 当前用户
        
    Returns:
        待处理的同步操作列表
    """
    try:
        pending_operations = data_sync_service.get_pending_sync_operations(limit)
        
        return {
            "success": True,
            "data": {
                "operations": pending_operations,
                "count": len(pending_operations)
            }
        }
        
    except Exception as e:
        logger.error(f"获取待处理同步操作失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/clear-pending-operations")
async def clear_pending_sync_operations(
    current_user: AdminUser = Depends(get_current_active_user)
):
    """
    清理待处理的同步操作
    
    Args:
        current_user: 当前用户
        
    Returns:
        清理结果
    """
    try:
        # 获取清理前的数量
        before_count = len(data_sync_service.get_pending_sync_operations())
        
        # 执行清理
        data_sync_service.clear_pending_sync_operations()
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 清理待处理同步操作: {before_count}个")
        
        return {
            "success": True,
            "data": {
                "cleared_count": before_count,
                "message": f"成功清理{before_count}个待处理同步操作"
            }
        }
        
    except Exception as e:
        logger.error(f"清理待处理同步操作失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}"
        )


@router.post("/invalidate-cache")
async def invalidate_all_cache(
    current_user: AdminUser = Depends(get_current_active_user)
):
    """
    失效所有缓存
    
    Args:
        current_user: 当前用户
        
    Returns:
        失效结果
    """
    try:
        # 获取失效前的缓存大小
        before_stats = data_sync_service.get_sync_statistics()
        cache_size = before_stats.get('cache_size', 0)
        
        # 执行缓存失效
        data_sync_service.invalidate_all_cache()
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 失效所有缓存: {cache_size}个条目")
        
        return {
            "success": True,
            "data": {
                "invalidated_count": cache_size,
                "message": f"成功失效{cache_size}个缓存条目"
            }
        }
        
    except Exception as e:
        logger.error(f"失效缓存失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"失效缓存失败: {str(e)}"
        )


@router.post("/force-sync/{tracking_number}")
async def force_sync_manifest(
    tracking_number: str,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    强制同步指定理货单
    
    Args:
        tracking_number: 快递单号
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        同步结果
    """
    try:
        # 执行强制同步
        sync_result = data_sync_service.force_sync_manifest(tracking_number, db)
        
        # 记录操作日志
        if sync_result.get('success'):
            logger.info(f"用户 {current_user.username} 强制同步理货单成功: {tracking_number}")
        else:
            logger.warning(f"用户 {current_user.username} 强制同步理货单失败: {tracking_number}")
        
        return {
            "success": sync_result.get('success', False),
            "data": sync_result.get('data'),
            "error": sync_result.get('error'),
            "tracking_number": tracking_number
        }
        
    except Exception as e:
        logger.error(f"强制同步理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"强制同步失败: {str(e)}"
        )


@router.get("/health")
async def sync_health_check(
    current_user: AdminUser = Depends(get_current_active_user)
):
    """
    数据同步服务健康检查
    
    Args:
        current_user: 当前用户
        
    Returns:
        健康检查结果
    """
    try:
        health_result = await data_sync_service.health_check()
        
        return {
            "success": True,
            "data": health_result
        }
        
    except Exception as e:
        logger.error(f"同步服务健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )


@router.get("/cache/{tracking_number}")
async def get_cached_manifest(
    tracking_number: str,
    current_user: AdminUser = Depends(get_current_active_user)
):
    """
    获取缓存的理货单信息
    
    Args:
        tracking_number: 快递单号
        current_user: 当前用户
        
    Returns:
        缓存的理货单信息
    """
    try:
        cached_data = data_sync_service.get_cached_manifest(tracking_number)
        
        if cached_data:
            return {
                "success": True,
                "data": cached_data,
                "cached": True,
                "tracking_number": tracking_number
            }
        else:
            return {
                "success": False,
                "data": None,
                "cached": False,
                "tracking_number": tracking_number,
                "message": "缓存中未找到该理货单"
            }
        
    except Exception as e:
        logger.error(f"获取缓存理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缓存失败: {str(e)}"
        )