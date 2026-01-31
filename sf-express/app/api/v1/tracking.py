"""
快递查询API端点
Tracking Query API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.input_validator import validate_tracking_number, validate_and_clean_input
from app.services.intelligent_query_service import IntelligentQueryService
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class TrackingQueryRequest(BaseModel):
    """快递查询请求模型"""
    tracking_number: str
    company_code: Optional[str] = "auto"
    phone: Optional[str] = None


class TrackingQueryResponse(BaseModel):
    """快递查询响应模型"""
    success: bool
    original_tracking_number: str
    cleaned_tracking_number: Optional[str] = None
    query_tracking_number: str
    query_type: str
    has_package_association: bool
    manifest_info: Optional[dict] = None
    tracking_info: Optional[dict] = None
    error: Optional[str] = None
    query_time: Optional[int] = None


class BatchTrackingQueryRequest(BaseModel):
    """批量快递查询请求模型"""
    tracking_numbers: List[str]
    company_code: Optional[str] = "auto"


@router.post("/query", response_model=TrackingQueryResponse)
async def query_tracking(
    request: TrackingQueryRequest,
    db: Session = Depends(get_db)
):
    """
    快递单号查询接口
    
    实现输入验证和智能查询功能：
    1. 验证快递单号格式和安全性
    2. 智能判断是否使用集包单号
    3. 调用快递100 API获取信息
    
    Args:
        request: 查询请求参数
        db: 数据库会话
        
    Returns:
        查询结果
        
    Raises:
        HTTPException: 当输入验证失败或系统错误时
    """
    logger.info(f"收到快递查询请求: {request.tracking_number}")
    
    try:
        # 输入验证在IntelligentQueryService中已经集成
        # 这里展示如何在API层面进行额外的验证
        
        # 验证公司编码（如果提供）
        if request.company_code and request.company_code != "auto":
            company_validation = validate_and_clean_input(request.company_code, "快递公司编码")
            if not company_validation.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"快递公司编码验证失败: {'; '.join(company_validation.errors)}"
                )
            request.company_code = company_validation.cleaned_value
        
        # 创建智能查询服务并执行查询
        query_service = IntelligentQueryService(db)
        result = await query_service.query_tracking(
            tracking_number=request.tracking_number,
            company_code=request.company_code,
            phone=request.phone
        )
        
        # 记录查询结果
        if result.get("success"):
            logger.info(f"查询成功: {request.tracking_number}")
        else:
            logger.warning(f"查询失败: {request.tracking_number}, 错误: {result.get('error')}")
        
        return TrackingQueryResponse(**result)
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"查询接口异常: {request.tracking_number}, 异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="系统内部错误，请稍后重试"
        )


@router.post("/batch-query")
async def batch_query_tracking(
    request: BatchTrackingQueryRequest,
    db: Session = Depends(get_db)
):
    """
    批量快递单号查询接口
    
    Args:
        request: 批量查询请求参数
        db: 数据库会话
        
    Returns:
        批量查询结果
        
    Raises:
        HTTPException: 当输入验证失败或系统错误时
    """
    logger.info(f"收到批量查询请求，单号数量: {len(request.tracking_numbers)}")
    
    try:
        # 验证批量查询限制
        if not request.tracking_numbers:
            raise HTTPException(
                status_code=400,
                detail="快递单号列表不能为空"
            )
        
        if len(request.tracking_numbers) > 100:
            raise HTTPException(
                status_code=400,
                detail="批量查询数量不能超过100个"
            )
        
        # 预验证所有快递单号
        invalid_numbers = []
        for tracking_number in request.tracking_numbers:
            validation_result = validate_tracking_number(tracking_number)
            if not validation_result.is_valid:
                invalid_numbers.append({
                    "tracking_number": tracking_number,
                    "errors": validation_result.errors
                })
        
        # 如果有无效单号，返回验证错误
        if invalid_numbers:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "部分快递单号验证失败",
                    "invalid_numbers": invalid_numbers
                }
            )
        
        # 执行批量查询
        query_service = IntelligentQueryService(db)
        result = await query_service.batch_intelligent_query(
            tracking_numbers=request.tracking_numbers,
            company_code=request.company_code
        )
        
        logger.info(f"批量查询完成，成功: {result['success_count']}, 失败: {result['failed_count']}")
        return result
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"批量查询接口异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="系统内部错误，请稍后重试"
        )


@router.get("/validate/{tracking_number}")
async def validate_tracking_number_endpoint(tracking_number: str):
    """
    快递单号验证接口
    
    仅验证快递单号格式，不执行实际查询
    
    Args:
        tracking_number: 要验证的快递单号
        
    Returns:
        验证结果
    """
    logger.info(f"收到单号验证请求: {tracking_number}")
    
    try:
        validation_result = validate_tracking_number(tracking_number)
        
        response = {
            "tracking_number": tracking_number,
            "is_valid": validation_result.is_valid,
            "cleaned_value": validation_result.cleaned_value,
            "errors": validation_result.errors
        }
        
        logger.info(f"单号验证完成: {tracking_number}, 有效: {validation_result.is_valid}")
        return response
        
    except Exception as e:
        logger.error(f"单号验证异常: {tracking_number}, 异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="验证服务异常"
        )