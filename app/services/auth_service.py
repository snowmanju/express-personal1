"""
认证服务 (Authentication Service)
提供用户认证、密码哈希、JWT令牌生成和验证功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.core.config_simple import settings
from app.models.admin_user import AdminUser
from app.core.database import get_db


class AuthService:
    """
    认证服务类
    处理用户认证、密码哈希、JWT令牌生成和验证
    """
    
    def __init__(self):
        # 密码哈希上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建JWT访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        
        # Use current UTC timestamp
        now = datetime.utcnow()
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        # Convert to UTC timestamp for JWT - use replace(tzinfo=timezone.utc) to ensure UTC
        from datetime import timezone
        expire_utc = expire.replace(tzinfo=timezone.utc)
        to_encode.update({"exp": int(expire_utc.timestamp())})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的数据，如果无效则返回None
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[AdminUser]:
        """
        认证用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            Optional[AdminUser]: 认证成功返回用户对象，否则返回None
        """
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        
        if not user:
            return None
            
        if not self.verify_password(password, user.password_hash):
            return None
            
        # 更新最后登录时间
        db.execute(
            update(AdminUser)
            .where(AdminUser.id == user.id)
            .values(last_login=datetime.utcnow())
        )
        db.commit()
        
        return user
    
    def get_current_user(self, db: Session, token: str) -> Optional[AdminUser]:
        """
        根据令牌获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT令牌
            
        Returns:
            Optional[AdminUser]: 用户对象，如果令牌无效则返回None
        """
        payload = self.verify_token(token)
        
        if payload is None:
            return None
            
        username = payload.get("sub")
        if username is None:
            return None
            
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        return user
    
    def create_user(self, db: Session, username: str, password: str) -> AdminUser:
        """
        创建新用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            AdminUser: 创建的用户对象
        """
        hashed_password = self.get_password_hash(password)
        
        user = AdminUser(
            username=username,
            password_hash=hashed_password
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user


# 创建全局认证服务实例
auth_service = AuthService()