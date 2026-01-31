"""
理货单模型 (CargoManifest Model)
"""

from sqlalchemy import Column, BigInteger, Integer, String, Date, DECIMAL, TIMESTAMP, Index
from sqlalchemy.sql import func
from app.core.database import Base


class CargoManifest(Base):
    """
    理货单模型
    包含快递单号、集包单号、货物信息等数据记录
    """
    __tablename__ = "cargo_manifest"

    # 使用Integer而不是BigInteger以确保SQLite的autoincrement正常工作
    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_number = Column(String(50), nullable=False, unique=True, comment="快递单号")
    manifest_date = Column(Date, nullable=False, comment="理货日期")
    transport_code = Column(String(20), nullable=False, comment="运输代码")
    customer_code = Column(String(20), nullable=False, comment="客户代码")
    goods_code = Column(String(20), nullable=False, comment="货物代码")
    package_number = Column(String(50), nullable=True, comment="集包单号")
    weight = Column(DECIMAL(10, 3), nullable=True, comment="重量")
    length = Column(DECIMAL(8, 2), nullable=True, comment="长度")
    width = Column(DECIMAL(8, 2), nullable=True, comment="宽度")
    height = Column(DECIMAL(8, 2), nullable=True, comment="高度")
    special_fee = Column(DECIMAL(10, 2), nullable=True, comment="特殊费用")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )

    # 创建索引
    __table_args__ = (
        Index('idx_tracking_number', 'tracking_number'),
        Index('idx_package_number', 'package_number'),
    )

    def __repr__(self):
        return f"<CargoManifest(id={self.id}, tracking_number='{self.tracking_number}', package_number='{self.package_number}')>"