"""
清单存储组件 (ManifestStorage)
负责处理清单数据的数据库操作，包括批量插入、更新和时间戳管理
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from dataclasses import dataclass
import pandas as pd
import logging

from app.models.cargo_manifest import CargoManifest

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class StorageResult:
    """存储结果数据类"""
    success: bool
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ManifestRecord:
    """清单记录数据类"""
    tracking_number: str
    manifest_date: Optional[str] = None
    transport_code: Optional[str] = None
    customer_code: Optional[str] = None
    goods_code: Optional[str] = None
    package_number: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None


class ManifestStorage:
    """
    清单存储器类
    处理清单数据的数据库操作
    """
    
    def __init__(self, db: Session):
        """
        初始化清单存储器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def check_duplicate_tracking_numbers(self, tracking_numbers: List[str]) -> List[str]:
        """
        检查重复的快递单号
        
        Args:
            tracking_numbers: 快递单号列表
            
        Returns:
            List[str]: 数据库中已存在的快递单号
        """
        try:
            existing_records = self.db.query(CargoManifest.tracking_number).filter(
                CargoManifest.tracking_number.in_(tracking_numbers)
            ).all()
            
            return [record.tracking_number for record in existing_records]
        except SQLAlchemyError as e:
            # 如果查询失败，返回空列表
            return []
    
    def insert_new_records(self, records: List[ManifestRecord]) -> int:
        """
        批量插入新记录（优化批量操作）
        
        Args:
            records: 清单记录列表
            
        Returns:
            int: 成功插入的记录数
        """
        inserted_count = 0
        current_time = datetime.now()
        
        # 批量大小
        BATCH_SIZE = 500
        
        try:
            # 分批处理记录
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                batch_objects = []
                
                for record in batch:
                    try:
                        # 创建新的CargoManifest实例
                        manifest_data = {
                            'tracking_number': record.tracking_number,
                            'created_at': current_time,
                            'updated_at': current_time
                        }
                        
                        # 添加可选字段
                        if record.manifest_date:
                            # 将日期字符串转换为date对象
                            try:
                                manifest_data['manifest_date'] = datetime.strptime(record.manifest_date, '%Y-%m-%d').date()
                            except (ValueError, TypeError):
                                # 如果转换失败，尝试其他格式或跳过
                                try:
                                    manifest_data['manifest_date'] = datetime.fromisoformat(record.manifest_date).date()
                                except:
                                    logger.warning(f"无法转换日期格式: {record.manifest_date}")
                                    pass
                        if record.transport_code:
                            manifest_data['transport_code'] = record.transport_code
                        if record.customer_code:
                            manifest_data['customer_code'] = record.customer_code
                        if record.goods_code:
                            manifest_data['goods_code'] = record.goods_code
                        if record.package_number:
                            manifest_data['package_number'] = record.package_number
                        if record.length is not None:
                            manifest_data['length'] = record.length
                        if record.width is not None:
                            manifest_data['width'] = record.width
                        if record.height is not None:
                            manifest_data['height'] = record.height
                        if record.weight is not None:
                            manifest_data['weight'] = record.weight
                        
                        new_manifest = CargoManifest(**manifest_data)
                        batch_objects.append(new_manifest)
                        
                    except Exception as e:
                        # 单条记录创建失败，记录错误但继续处理其他记录
                        logger.error(f"创建记录失败 (快递单号: {record.tracking_number}): {str(e)}")
                        continue
                
                # 批量添加到会话
                if batch_objects:
                    self.db.bulk_save_objects(batch_objects)
                    inserted_count += len(batch_objects)
                    logger.info(f"批次 {i//BATCH_SIZE + 1}: 准备插入 {len(batch_objects)} 条记录")
            
            logger.info(f"成功准备插入{inserted_count}条记录")
            return inserted_count
            
        except SQLAlchemyError as e:
            # 如果出错，不提交任何记录
            logger.error(f"批量插入操作失败: {str(e)}")
            return 0
    
    def update_existing_records(self, records: List[ManifestRecord]) -> int:
        """
        批量更新现有记录（优化批量操作）
        
        Args:
            records: 清单记录列表
            
        Returns:
            int: 成功更新的记录数
        """
        updated_count = 0
        current_time = datetime.now()
        
        # 批量大小
        BATCH_SIZE = 500
        
        try:
            # 分批处理记录
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                tracking_numbers = [r.tracking_number for r in batch]
                
                # 批量查询现有记录
                existing_records = self.db.query(CargoManifest).filter(
                    CargoManifest.tracking_number.in_(tracking_numbers)
                ).all()
                
                # 创建快速查找字典
                existing_dict = {r.tracking_number: r for r in existing_records}
                
                for record in batch:
                    try:
                        existing = existing_dict.get(record.tracking_number)
                        
                        if existing:
                            # 更新字段
                            if record.manifest_date:
                                # 将日期字符串转换为date对象
                                try:
                                    existing.manifest_date = datetime.strptime(record.manifest_date, '%Y-%m-%d').date()
                                except (ValueError, TypeError):
                                    try:
                                        existing.manifest_date = datetime.fromisoformat(record.manifest_date).date()
                                    except:
                                        logger.warning(f"无法转换日期格式: {record.manifest_date}")
                                        pass
                            if record.transport_code:
                                existing.transport_code = record.transport_code
                            if record.customer_code:
                                existing.customer_code = record.customer_code
                            if record.goods_code:
                                existing.goods_code = record.goods_code
                            if record.package_number:
                                existing.package_number = record.package_number
                            if record.length is not None:
                                existing.length = record.length
                            if record.width is not None:
                                existing.width = record.width
                            if record.height is not None:
                                existing.height = record.height
                            if record.weight is not None:
                                existing.weight = record.weight
                            
                            # 更新时间戳
                            existing.updated_at = current_time
                            updated_count += 1
                        else:
                            logger.warning(f"未找到要更新的记录 (快递单号: {record.tracking_number})")
                            
                    except Exception as e:
                        # 单条记录更新失败，记录错误但继续处理其他记录
                        logger.error(f"更新记录失败 (快递单号: {record.tracking_number}): {str(e)}")
                        continue
                
                logger.info(f"批次 {i//BATCH_SIZE + 1}: 准备更新 {len([r for r in batch if r.tracking_number in existing_dict])} 条记录")
            
            logger.info(f"成功准备更新{updated_count}条记录")
            return updated_count
            
        except SQLAlchemyError as e:
            logger.error(f"批量更新操作失败: {str(e)}")
            return 0
    
    def save_manifest_records(self, records: List[ManifestRecord]) -> StorageResult:
        """
        保存清单记录（插入新记录或更新现有记录）
        
        Args:
            records: 清单记录列表
            
        Returns:
            StorageResult: 存储结果
        """
        result = StorageResult(success=False)
        
        if not records:
            result.success = True
            logger.info("没有记录需要保存")
            return result
        
        try:
            logger.info(f"开始保存{len(records)}条记录")
            
            # 获取所有快递单号
            tracking_numbers = [record.tracking_number for record in records]
            
            # 检查哪些快递单号已存在
            existing_tracking_numbers = set(self.check_duplicate_tracking_numbers(tracking_numbers))
            logger.info(f"发现{len(existing_tracking_numbers)}个已存在的快递单号")
            
            # 分离新记录和需要更新的记录
            new_records = []
            update_records = []
            
            for record in records:
                if record.tracking_number in existing_tracking_numbers:
                    update_records.append(record)
                else:
                    new_records.append(record)
            
            logger.info(f"新记录: {len(new_records)}, 更新记录: {len(update_records)}")
            
            # 插入新记录
            if new_records:
                inserted = self.insert_new_records(new_records)
                result.inserted = inserted
                logger.info(f"准备插入{inserted}条新记录")
            
            # 更新现有记录
            if update_records:
                updated = self.update_existing_records(update_records)
                result.updated = updated
                logger.info(f"准备更新{updated}条现有记录")
            
            # 提交事务
            self.db.commit()
            result.success = True
            logger.info(f"数据库事务提交成功: 插入={result.inserted}, 更新={result.updated}")
            
        except SQLAlchemyError as e:
            # 回滚事务
            self.db.rollback()
            error_msg = f"数据库操作失败: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            error_msg = f"存储操作失败: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
        
        return result
    
    def create_manifest_record_from_dict(self, data: Dict[str, Any]) -> ManifestRecord:
        """
        从字典创建ManifestRecord实例
        
        Args:
            data: 数据字典
            
        Returns:
            ManifestRecord: 清单记录实例
        """
        return ManifestRecord(
            tracking_number=str(data.get('快递单号', '')).strip(),
            manifest_date=str(data.get('理货日期', '')).strip() if pd.notna(data.get('理货日期')) else None,
            transport_code=str(data.get('运输代码', '')).strip() if pd.notna(data.get('运输代码')) else None,
            customer_code=str(data.get('客户代码', '')).strip() if pd.notna(data.get('客户代码')) else None,
            goods_code=str(data.get('货物代码', '')).strip() if pd.notna(data.get('货物代码')) else None,
            package_number=str(data.get('集包单号', '')).strip() if pd.notna(data.get('集包单号')) else None,
            length=float(data.get('长度')) if pd.notna(data.get('长度')) and str(data.get('长度')).strip() != '' else None,
            width=float(data.get('宽度')) if pd.notna(data.get('宽度')) and str(data.get('宽度')).strip() != '' else None,
            height=float(data.get('高度')) if pd.notna(data.get('高度')) and str(data.get('高度')).strip() != '' else None,
            weight=float(data.get('重量')) if pd.notna(data.get('重量')) and str(data.get('重量')).strip() != '' else None
        )