"""
认证相关的Pydantic模型 (Authentication Schemas)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间(秒)")
    user_info: "UserInfo" = Field(..., description="用户信息")


class UserInfo(BaseModel):
    """用户信息模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT令牌载荷模型"""
    sub: Optional[str] = None  # subject (username)
    exp: Optional[int] = None  # expiration time


class CreateUserRequest(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码，至少6位")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    created_at: datetime = Field(..., description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码，至少6位")


# 更新前向引用
LoginResponse.model_rebuild()