"""
认证依赖和中间件 (Authentication Dependencies and Middleware)
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.models.admin_user import AdminUser


# HTTP Bearer 认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    获取当前认证用户的依赖函数
    
    Args:
        credentials: HTTP Bearer 凭据
        db: 数据库会话
        
    Returns:
        AdminUser: 当前用户
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception:
        raise credentials_exception


def get_current_active_user(
    current_user: AdminUser = Depends(get_current_user)
) -> AdminUser:
    """
    获取当前活跃用户的依赖函数
    
    Args:
        current_user: 当前用户
        
    Returns:
        AdminUser: 当前活跃用户
        
    Raises:
        HTTPException: 用户不活跃时抛出400错误
    """
    # 这里可以添加用户状态检查逻辑
    # 例如检查用户是否被禁用等
    return current_user


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[AdminUser]:
    """
    可选认证依赖函数
    用于不强制要求认证的端点
    
    Args:
        credentials: 可选的HTTP Bearer 凭据
        db: 数据库会话
        
    Returns:
        Optional[AdminUser]: 用户对象或None
    """
    if credentials is None:
        return None
        
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(db, token)
        return user
    except Exception:
        return None