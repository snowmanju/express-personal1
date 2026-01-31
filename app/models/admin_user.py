"""
管理员用户模型 (AdminUser Model)
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class AdminUser(Base):
    """
    管理员用户模型
    用于后台管理系统的用户认证和会话管理
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    last_login = Column(TIMESTAMP, nullable=True, comment="最后登录时间")

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}')>"