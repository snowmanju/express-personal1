"""
理货单管理API端点 (Manifest Management API)
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
import os

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.services.manifest_service import ManifestService
from app.models.admin_user import AdminUser
from app.schemas.manifest import (
    ManifestResponse,
    ManifestListResponse,
    ManifestCreateRequest,
    ManifestUpdateRequest,
    ManifestSearchRequest,
    FileUploadResponse,
    ManifestDeleteResponse,
    ManifestStatisticsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_manifest_file(
    file: UploadFile = File(...),
    preview_only: bool = Form(False),
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """
    上传理货单文件
    
    Args:
        file: 上传的文件（CSV或Excel格式）
        preview_only: 是否仅预览，不保存到数据库
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        FileUploadResponse: 上传结果
        
    Raises:
        HTTPException: 文件格式不支持或处理失败时抛出400错误
    """
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 开始上传文件: {file.filename}, "
                   f"大小: {len(file_content)} bytes, 预览模式: {preview_only}")
        
        # 导入CSV处理组件
        from app.services.file_validator import FileValidator
        from app.services.csv_processor import CSVProcessor
        from app.services.data_validator import DataValidator
        from app.services.manifest_storage import ManifestStorage
        
        # 1. 文件验证
        file_validator = FileValidator()
        is_valid, validation_errors = file_validator.validate(file_content, file.filename)
        
        if not is_valid:
            logger.warning(f"文件验证失败: {', '.join(validation_errors)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_errors[0] if validation_errors else "文件验证失败"
            )
        
        # 2. 初始化处理组件
        csv_processor = CSVProcessor()
        data_validator = DataValidator()
        manifest_storage = ManifestStorage(db)
        
        # 3. 处理文件
        result = csv_processor.process_file(
            file_content=file_content,
            filename=file.filename,
            preview_only=preview_only,
            data_validator=data_validator,
            manifest_storage=manifest_storage
        )
        
        # 4. 检查处理结果
        if not result.success:
            logger.error(f"文件处理失败: {', '.join(result.errors)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.errors[0] if result.errors else "文件处理失败"
            )
        
        # 5. 构建响应
        if preview_only:
            # 预览模式：返回详细的行数据
            preview_data_list = []
            if result.preview_data:
                for preview_row in result.preview_data:
                    preview_data_list.append({
                        'row_number': preview_row.row_number,
                        'data': preview_row.data,
                        'valid': preview_row.valid,
                        'errors': preview_row.errors
                    })
            
            statistics = {
                'total_rows': result.statistics.total_rows,
                'valid_rows': result.statistics.valid_rows,
                'invalid_rows': result.statistics.invalid_rows,
                'preview_rows': len(preview_data_list)
            }
            
            logger.info(f"预览模式处理完成: {statistics}")
            
            return FileUploadResponse(
                success=True,
                message="文件预览成功",
                preview_data=preview_data_list,
                statistics=statistics,
                errors=[]
            )
        else:
            # 保存模式：返回处理统计信息
            statistics = {
                'total_rows': result.statistics.total_rows,
                'valid_rows': result.statistics.valid_rows,
                'invalid_rows': result.statistics.invalid_rows,
                'inserted': result.statistics.inserted,
                'updated': result.statistics.updated,
                'skipped': result.statistics.skipped
            }
            
            logger.info(f"用户 {current_user.username} 上传理货单文件成功: {file.filename}, "
                       f"统计: {statistics}")
            
            return FileUploadResponse(
                success=True,
                message=f"文件上传处理成功。插入 {statistics['inserted']} 条，更新 {statistics['updated']} 条",
                preview_data=[],
                statistics=statistics,
                errors=[]
            )
            
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录系统错误
        logger.error(f"文件上传处理失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


@router.get("/search", response_model=ManifestListResponse)
async def search_manifests(
    q: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    transport_code: Optional[str] = Query(None, description="运输代码过滤"),
    customer_code: Optional[str] = Query(None, description="客户代码过滤"),
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestListResponse:
    """
    搜索理货单记录
    
    Args:
        q: 搜索关键词（支持快递单号、集包单号等）
        page: 页码
        limit: 每页记录数
        sort_by: 排序字段
        sort_order: 排序方向
        transport_code: 运输代码过滤
        customer_code: 客户代码过滤
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestListResponse: 搜索结果
    """
    try:
        # 构建过滤条件
        filters = {}
        if transport_code:
            filters['transport_code'] = transport_code
        if customer_code:
            filters['customer_code'] = customer_code
        
        # 初始化理货单服务
        manifest_service = ManifestService(db)
        
        # 执行搜索
        result = manifest_service.search_manifests(
            search_query=q,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', '搜索失败')
            )
        
        return ManifestListResponse(
            success=True,
            data=result['data'],
            pagination=result['pagination'],
            search_query=result.get('search_query'),
            filters=result.get('filters')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/{manifest_id}", response_model=ManifestResponse)
async def get_manifest(
    manifest_id: int,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestResponse:
    """
    获取理货单详情
    
    Args:
        manifest_id: 理货单ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestResponse: 理货单详情
        
    Raises:
        HTTPException: 理货单不存在时抛出404错误
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.get_manifest_by_id(manifest_id)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', '理货单不存在')
            )
        
        return ManifestResponse(
            success=True,
            data=result['data']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取理货单详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/", response_model=ManifestResponse)
async def create_manifest(
    manifest_data: ManifestCreateRequest,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestResponse:
    """
    创建新的理货单记录
    
    Args:
        manifest_data: 理货单数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestResponse: 创建结果
        
    Raises:
        HTTPException: 数据验证失败或创建失败时抛出400错误
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.create_manifest(manifest_data.dict())
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('errors', ['创建失败'])
            )
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 创建理货单: {result['data']['tracking_number']}")
        
        return ManifestResponse(
            success=True,
            data=result['data'],
            message=result.get('message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.put("/{manifest_id}", response_model=ManifestResponse)
async def update_manifest(
    manifest_id: int,
    manifest_data: ManifestUpdateRequest,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestResponse:
    """
    更新理货单记录
    
    Args:
        manifest_id: 理货单ID
        manifest_data: 更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestResponse: 更新结果
        
    Raises:
        HTTPException: 理货单不存在或更新失败时抛出相应错误
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.update_manifest(manifest_id, manifest_data.dict(exclude_unset=True))
        
        if not result['success']:
            if '理货单不存在' in result.get('errors', [''])[0]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="理货单不存在"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get('errors', ['更新失败'])
                )
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 更新理货单: {result['data']['tracking_number']}")
        
        return ManifestResponse(
            success=True,
            data=result['data'],
            message=result.get('message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete("/{manifest_id}", response_model=ManifestDeleteResponse)
async def delete_manifest(
    manifest_id: int,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestDeleteResponse:
    """
    删除理货单记录
    
    Args:
        manifest_id: 理货单ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestDeleteResponse: 删除结果
        
    Raises:
        HTTPException: 理货单不存在或删除失败时抛出相应错误
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.delete_manifest(manifest_id, current_user.username)
        
        if not result['success']:
            if '理货单不存在' in result.get('error', ''):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="理货单不存在"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get('error', '删除失败')
                )
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 删除理货单: {result['data']['tracking_number']}")
        
        return ManifestDeleteResponse(
            success=True,
            data=result['data'],
            message=result.get('message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.delete("/batch", response_model=ManifestDeleteResponse)
async def batch_delete_manifests(
    manifest_ids: List[int],
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestDeleteResponse:
    """
    批量删除理货单记录
    
    Args:
        manifest_ids: 理货单ID列表
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestDeleteResponse: 删除结果
        
    Raises:
        HTTPException: 删除失败时抛出相应错误
    """
    try:
        if not manifest_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未指定要删除的记录"
            )
        
        manifest_service = ManifestService(db)
        result = manifest_service.batch_delete_manifests(manifest_ids, current_user.username)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', '批量删除失败')
            )
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 批量删除理货单: {len(manifest_ids)}条记录")
        
        return ManifestDeleteResponse(
            success=True,
            data=result['data'],
            message=result.get('message')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除失败: {str(e)}"
        )


@router.get("/statistics/overview", response_model=ManifestStatisticsResponse)
async def get_manifest_statistics(
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestStatisticsResponse:
    """
    获取理货单统计信息
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestStatisticsResponse: 统计信息
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.get_statistics()
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', '获取统计信息失败')
            )
        
        return ManifestStatisticsResponse(
            success=True,
            data=result['data']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/tracking/{tracking_number}", response_model=ManifestResponse)
async def get_manifest_by_tracking_number(
    tracking_number: str,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ManifestResponse:
    """
    根据快递单号获取理货单
    
    Args:
        tracking_number: 快递单号
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ManifestResponse: 理货单信息
        
    Raises:
        HTTPException: 理货单不存在时抛出404错误
    """
    try:
        manifest_service = ManifestService(db)
        result = manifest_service.get_manifest_by_tracking_number(tracking_number)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', '未找到对应的理货单')
            )
        
        return ManifestResponse(
            success=True,
            data=result['data']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据快递单号获取理货单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )



@router.get("/template/download")
async def download_template(
    current_user: AdminUser = Depends(get_current_active_user)
) -> FileResponse:
    """
    下载理货单CSV模板文件
    
    Args:
        current_user: 当前用户
        
    Returns:
        FileResponse: CSV模板文件
        
    Raises:
        HTTPException: 模板文件不存在时抛出404错误
    """
    try:
        # 模板文件路径
        template_path = os.path.join("static", "templates", "manifest_upload_template.csv")
        
        # 检查文件是否存在
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板文件不存在"
            )
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 下载理货单模板")
        
        # 返回文件响应
        return FileResponse(
            path=template_path,
            media_type="text/csv",
            filename="manifest_upload_template.csv",
            headers={
                "Content-Disposition": "attachment; filename=manifest_upload_template.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载模板文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )
