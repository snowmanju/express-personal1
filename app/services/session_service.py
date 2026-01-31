"""
会话管理服务 (Session Management Service)
处理用户会话超时、自动注销和重定向功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config_simple import settings
from app.services.auth_service import auth_service
from app.models.admin_user import AdminUser


class SessionService:
    """
    会话管理服务类
    处理会话超时、自动注销和会话状态管理
    """
    
    def __init__(self):
        self.session_timeout_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def is_session_valid(self, token: str) -> bool:
        """
        检查会话是否有效
        
        Args:
            token: JWT令牌
            
        Returns:
            bool: 会话是否有效
        """
        payload = auth_service.verify_token(token)
        
        if payload is None:
            return False
            
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp is None:
            return False
            
        # 将时间戳转换为datetime对象进行比较 (确保使用UTC)
        from datetime import timezone
        expiration_time = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
        current_time = datetime.utcnow()
        
        return current_time < expiration_time
    
    def get_session_remaining_time(self, token: str) -> Optional[int]:
        """
        获取会话剩余时间（秒）
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[int]: 剩余时间（秒），如果会话无效则返回None
        """
        payload = auth_service.verify_token(token)
        
        if payload is None:
            return None
            
        exp = payload.get("exp")
        if exp is None:
            return None
            
        from datetime import timezone
        expiration_time = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
        current_time = datetime.utcnow()
        
        if current_time >= expiration_time:
            return 0
            
        remaining_seconds = int((expiration_time - current_time).total_seconds())
        return max(0, remaining_seconds)
    
    def refresh_session(self, db: Session, token: str) -> Optional[str]:
        """
        刷新会话令牌
        
        Args:
            db: 数据库会话
            token: 当前JWT令牌
            
        Returns:
            Optional[str]: 新的JWT令牌，如果刷新失败则返回None
        """
        user = auth_service.get_current_user(db, token)
        
        if user is None:
            return None
            
        # 检查当前令牌是否还有效
        if not self.is_session_valid(token):
            return None
            
        # 生成新的令牌
        access_token_expires = timedelta(minutes=self.session_timeout_minutes)
        new_token = auth_service.create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return new_token
    
    def invalidate_session(self, token: str) -> bool:
        """
        使会话无效（注销）
        
        注意：由于JWT是无状态的，这里主要是提供接口
        实际的令牌失效需要通过客户端删除令牌或使用黑名单机制
        
        Args:
            token: JWT令牌
            
        Returns:
            bool: 操作是否成功
        """
        # 验证令牌格式是否正确
        payload = auth_service.verify_token(token)
        return payload is not None
    
    def create_session_info(self, user: AdminUser, token: str) -> Dict[str, Any]:
        """
        创建会话信息
        
        Args:
            user: 用户对象
            token: JWT令牌
            
        Returns:
            Dict[str, Any]: 会话信息
        """
        remaining_time = self.get_session_remaining_time(token)
        
        return {
            "user_id": user.id,
            "username": user.username,
            "token": token,
            "expires_in": remaining_time,
            "is_valid": remaining_time is not None and remaining_time > 0,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    def check_session_timeout_warning(self, token: str, warning_minutes: int = 5) -> Dict[str, Any]:
        """
        检查会话是否即将超时
        
        Args:
            token: JWT令牌
            warning_minutes: 警告提前时间（分钟）
            
        Returns:
            Dict[str, Any]: 超时警告信息
        """
        remaining_time = self.get_session_remaining_time(token)
        
        if remaining_time is None:
            return {
                "should_warn": False,
                "should_logout": True,
                "remaining_seconds": 0,
                "message": "会话已过期，请重新登录"
            }
        
        warning_seconds = warning_minutes * 60
        
        if remaining_time <= 0:
            return {
                "should_warn": False,
                "should_logout": True,
                "remaining_seconds": 0,
                "message": "会话已过期，请重新登录"
            }
        elif remaining_time <= warning_seconds:
            return {
                "should_warn": True,
                "should_logout": False,
                "remaining_seconds": remaining_time,
                "message": f"会话将在 {remaining_time} 秒后过期，请及时保存工作"
            }
        else:
            return {
                "should_warn": False,
                "should_logout": False,
                "remaining_seconds": remaining_time,
                "message": "会话正常"
            }


# 创建全局会话服务实例
session_service = SessionService()