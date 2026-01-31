"""
认证和会话管理API端点 (Authentication and Session Management API)
"""

from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.services.auth_service import auth_service
from app.services.session_service import session_service
from app.models.admin_user import AdminUser
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserInfo,
    CreateUserRequest,
    UserResponse,
    ChangePasswordRequest
)
from app.core.config_simple import settings


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    管理员登录
    
    Args:
        login_data: 登录请求数据
        db: 数据库会话
        
    Returns:
        LoginResponse: 登录响应，包含访问令牌和用户信息
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    # 认证用户
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # 构建用户信息
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        last_login=user.last_login
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info=user_info
    )


@router.post("/logout")
async def logout(
    current_user: AdminUser = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    管理员注销
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict[str, Any]: 注销结果
    """
    # 由于JWT是无状态的，注销主要是客户端删除令牌
    # 这里返回成功响应，指示客户端清除令牌
    return {
        "success": True,
        "message": "注销成功",
        "should_clear_token": True
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AdminUser = Depends(get_current_active_user)
) -> UserResponse:
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/session/status")
async def get_session_status(
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取会话状态
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 会话状态信息
    """
    # 从请求头获取令牌（这里简化处理，实际应该从依赖中获取）
    # 在实际实现中，可以通过修改依赖来传递令牌
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_authenticated": True,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@router.post("/session/refresh")
async def refresh_session(
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    刷新会话令牌
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 新的令牌信息
    """
    # 生成新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = auth_service.create_access_token(
        data={"sub": current_user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "message": "令牌刷新成功"
    }


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    修改密码
    
    Args:
        password_data: 密码修改请求数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 修改结果
        
    Raises:
        HTTPException: 当前密码错误时抛出400错误
    """
    # 验证当前密码
    if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 生成新密码哈希
    new_password_hash = auth_service.get_password_hash(password_data.new_password)
    
    # 更新密码
    current_user.password_hash = new_password_hash
    db.commit()
    
    return {
        "success": True,
        "message": "密码修改成功"
    }


@router.post("/create-user", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: AdminUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    创建新用户（仅限管理员）
    
    Args:
        user_data: 用户创建请求数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        UserResponse: 创建的用户信息
        
    Raises:
        HTTPException: 用户名已存在时抛出400错误
    """
    # 检查用户名是否已存在
    existing_user = db.query(AdminUser).filter(AdminUser.username == user_data.username).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    new_user = auth_service.create_user(db, user_data.username, user_data.password)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        created_at=new_user.created_at,
        last_login=new_user.last_login
    )