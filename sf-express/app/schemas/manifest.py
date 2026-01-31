"""
理货单相关的Pydantic模型 (Manifest Pydantic Models)
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from decimal import Decimal


class ManifestBase(BaseModel):
    """理货单基础模型"""
    tracking_number: str = Field(..., max_length=50, description="快递单号")
    manifest_date: date = Field(..., description="理货日期")
    transport_code: str = Field(..., max_length=20, description="运输代码")
    customer_code: str = Field(..., max_length=20, description="客户代码")
    goods_code: str = Field(..., max_length=20, description="货物代码")
    package_number: Optional[str] = Field(None, max_length=50, description="集包单号")
    weight: Optional[Decimal] = Field(None, ge=0, le=999999.999, description="重量")
    length: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="长度")
    width: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="宽度")
    height: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="高度")
    special_fee: Optional[Decimal] = Field(None, ge=0, le=99999999.99, description="特殊费用")

    @validator('tracking_number')
    def validate_tracking_number(cls, v):
        """验证快递单号格式"""
        import re
        if not re.match(r'^[A-Za-z0-9]+$', v.strip()):
            raise ValueError('快递单号只能包含字母和数字')
        return v.strip()

    @validator('transport_code', 'customer_code', 'goods_code', 'package_number')
    def validate_string_fields(cls, v):
        """验证字符串字段"""
        if v is not None:
            return v.strip()
        return v


class ManifestCreateRequest(ManifestBase):
    """创建理货单请求模型"""
    pass


class ManifestUpdateRequest(BaseModel):
    """更新理货单请求模型"""
    tracking_number: Optional[str] = Field(None, max_length=50, description="快递单号")
    manifest_date: Optional[date] = Field(None, description="理货日期")
    transport_code: Optional[str] = Field(None, max_length=20, description="运输代码")
    customer_code: Optional[str] = Field(None, max_length=20, description="客户代码")
    goods_code: Optional[str] = Field(None, max_length=20, description="货物代码")
    package_number: Optional[str] = Field(None, max_length=50, description="集包单号")
    weight: Optional[Decimal] = Field(None, ge=0, le=999999.999, description="重量")
    length: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="长度")
    width: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="宽度")
    height: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="高度")
    special_fee: Optional[Decimal] = Field(None, ge=0, le=99999999.99, description="特殊费用")

    @validator('tracking_number')
    def validate_tracking_number(cls, v):
        """验证快递单号格式"""
        if v is not None:
            import re
            if not re.match(r'^[A-Za-z0-9]+$', v.strip()):
                raise ValueError('快递单号只能包含字母和数字')
            return v.strip()
        return v

    @validator('transport_code', 'customer_code', 'goods_code', 'package_number')
    def validate_string_fields(cls, v):
        """验证字符串字段"""
        if v is not None:
            return v.strip()
        return v


class ManifestData(ManifestBase):
    """理货单数据模型"""
    id: int = Field(..., description="理货单ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class ManifestResponse(BaseModel):
    """理货单响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="理货单数据")
    message: Optional[str] = Field(None, description="响应消息")


class PaginationInfo(BaseModel):
    """分页信息模型"""
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页记录数")
    total_count: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class ManifestListResponse(BaseModel):
    """理货单列表响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: List[Dict[str, Any]] = Field(..., description="理货单列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    search_query: Optional[str] = Field(None, description="搜索关键词")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class ManifestSearchRequest(BaseModel):
    """理货单搜索请求模型"""
    search_query: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页记录数")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    preview_data: List[Dict[str, Any]] = Field(default_factory=list, description="预览数据")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计信息")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    upload_result: Optional[Dict[str, Any]] = Field(None, description="上传处理结果")


class ManifestDeleteResponse(BaseModel):
    """理货单删除响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="删除的数据信息")
    message: Optional[str] = Field(None, description="响应消息")


class ManifestStatisticsResponse(BaseModel):
    """理货单统计响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Dict[str, Any] = Field(..., description="统计数据")


class BatchDeleteRequest(BaseModel):
    """批量删除请求模型"""
    manifest_ids: List[int] = Field(..., min_items=1, description="要删除的理货单ID列表")

    @validator('manifest_ids')
    def validate_manifest_ids(cls, v):
        """验证ID列表"""
        if not v:
            raise ValueError('至少需要指定一个理货单ID')
        # 去重
        return list(set(v))