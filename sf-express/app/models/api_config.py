"""
API配置模型 (ApiConfig Model)
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class ApiConfig(Base):
    """
    API配置模型
    存储快递100 API的认证参数和其他系统配置
    """
    __tablename__ = "api_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), nullable=False, unique=True, comment="配置键")
    config_value = Column(String(255), nullable=False, comment="配置值")
    description = Column(Text, nullable=True, comment="配置描述")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )

    def __repr__(self):
        return f"<ApiConfig(id={self.id}, config_key='{self.config_key}')>"