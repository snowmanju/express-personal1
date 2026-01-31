"""
理货单管理服务 (ManifestService)
提供理货单的搜索、编辑、删除功能，支持增量更新逻辑
集成数据同步服务，确保变更实时更新查询逻辑
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import logging
from app.models.cargo_manifest import CargoManifest
from app.core.database import get_db
from app.services.data_sync_service import data_sync_service


class ManifestService:
    """
    理货单管理服务类
    提供理货单数据的CRUD操作和搜索功能
    """
    
    def __init__(self, db: Session = None):
        """初始化理货单管理服务"""
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # 注册为数据同步监听器
        if hasattr(data_sync_service, 'register_sync_listener'):
            data_sync_service.register_sync_listener(self)
    
    async def on_manifest_changed(self, sync_operation: Dict[str, Any]):
        """
        处理理货单数据变更通知
        
        Args:
            sync_operation: 同步操作信息
        """
        try:
            operation = sync_operation.get('operation')
            tracking_number = sync_operation.get('tracking_number')
            
            self.logger.info(f"理货单服务收到变更通知: {operation} - {tracking_number}")
            
            # 这里可以添加额外的业务逻辑处理
            # 例如：更新相关统计信息、发送通知等
            
        except Exception as e:
            self.logger.error(f"处理理货单变更通知失败: {str(e)}")

    def search_manifests(
        self, 
        search_query: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        搜索理货单记录
        
        Args:
            search_query: 搜索关键词（支持快递单号、集包单号搜索）
            page: 页码（从1开始）
            limit: 每页记录数
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            filters: 额外过滤条件
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            # 构建基础查询
            query = self.db.query(CargoManifest)
            
            # 应用搜索条件
            if search_query and search_query.strip():
                search_term = f"%{search_query.strip()}%"
                query = query.filter(
                    or_(
                        CargoManifest.tracking_number.like(search_term),
                        CargoManifest.package_number.like(search_term),
                        CargoManifest.customer_code.like(search_term),
                        CargoManifest.transport_code.like(search_term),
                        CargoManifest.goods_code.like(search_term)
                    )
                )
            
            # 应用额外过滤条件
            if filters:
                for field, value in filters.items():
                    if hasattr(CargoManifest, field) and value is not None:
                        if isinstance(value, str) and value.strip():
                            query = query.filter(getattr(CargoManifest, field) == value.strip())
                        elif not isinstance(value, str):
                            query = query.filter(getattr(CargoManifest, field) == value)
            
            # 获取总记录数
            total_count = query.count()
            
            # 应用排序
            if hasattr(CargoManifest, sort_by):
                sort_column = getattr(CargoManifest, sort_by)
                if sort_order.lower() == 'desc':
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                # 默认按创建时间倒序
                query = query.order_by(desc(CargoManifest.created_at))
            
            # 应用分页
            offset = (page - 1) * limit
            manifests = query.offset(offset).limit(limit).all()
            
            # 转换为字典格式
            manifest_list = []
            for manifest in manifests:
                manifest_dict = {
                    'id': manifest.id,
                    'tracking_number': manifest.tracking_number,
                    'manifest_date': manifest.manifest_date.isoformat() if manifest.manifest_date else None,
                    'transport_code': manifest.transport_code,
                    'customer_code': manifest.customer_code,
                    'goods_code': manifest.goods_code,
                    'package_number': manifest.package_number,
                    'weight': float(manifest.weight) if manifest.weight else None,
                    'length': float(manifest.length) if manifest.length else None,
                    'width': float(manifest.width) if manifest.width else None,
                    'height': float(manifest.height) if manifest.height else None,
                    'special_fee': float(manifest.special_fee) if manifest.special_fee else None,
                    'created_at': manifest.created_at.isoformat() if manifest.created_at else None,
                    'updated_at': manifest.updated_at.isoformat() if manifest.updated_at else None
                }
                manifest_list.append(manifest_dict)
            
            # 计算分页信息
            total_pages = (total_count + limit - 1) // limit
            
            return {
                'success': True,
                'data': manifest_list,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'search_query': search_query,
                'filters': filters
            }
            
        except Exception as e:
            self.logger.error(f"搜索理货单失败: {str(e)}")
            return {
                'success': False,
                'error': f"搜索失败: {str(e)}",
                'data': [],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }

    def get_manifest_by_id(self, manifest_id: int) -> Dict[str, Any]:
        """
        根据ID获取理货单详情
        
        Args:
            manifest_id: 理货单ID
            
        Returns:
            Dict[str, Any]: 理货单详情
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            manifest = self.db.query(CargoManifest).filter(CargoManifest.id == manifest_id).first()
            
            if not manifest:
                return {
                    'success': False,
                    'error': '理货单不存在',
                    'data': None
                }
            
            manifest_dict = {
                'id': manifest.id,
                'tracking_number': manifest.tracking_number,
                'manifest_date': manifest.manifest_date.isoformat() if manifest.manifest_date else None,
                'transport_code': manifest.transport_code,
                'customer_code': manifest.customer_code,
                'goods_code': manifest.goods_code,
                'package_number': manifest.package_number,
                'weight': float(manifest.weight) if manifest.weight else None,
                'length': float(manifest.length) if manifest.length else None,
                'width': float(manifest.width) if manifest.width else None,
                'height': float(manifest.height) if manifest.height else None,
                'special_fee': float(manifest.special_fee) if manifest.special_fee else None,
                'created_at': manifest.created_at.isoformat() if manifest.created_at else None,
                'updated_at': manifest.updated_at.isoformat() if manifest.updated_at else None
            }
            
            return {
                'success': True,
                'data': manifest_dict
            }
            
        except Exception as e:
            self.logger.error(f"获取理货单详情失败: {str(e)}")
            return {
                'success': False,
                'error': f"获取失败: {str(e)}",
                'data': None
            }

    def get_manifest_by_tracking_number(self, tracking_number: str) -> Dict[str, Any]:
        """
        根据快递单号获取理货单
        
        Args:
            tracking_number: 快递单号
            
        Returns:
            Dict[str, Any]: 理货单信息
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            manifest = self.db.query(CargoManifest).filter(
                CargoManifest.tracking_number == tracking_number.strip()
            ).first()
            
            if not manifest:
                return {
                    'success': False,
                    'error': '未找到对应的理货单',
                    'data': None
                }
            
            manifest_dict = {
                'id': manifest.id,
                'tracking_number': manifest.tracking_number,
                'manifest_date': manifest.manifest_date.isoformat() if manifest.manifest_date else None,
                'transport_code': manifest.transport_code,
                'customer_code': manifest.customer_code,
                'goods_code': manifest.goods_code,
                'package_number': manifest.package_number,
                'weight': float(manifest.weight) if manifest.weight else None,
                'length': float(manifest.length) if manifest.length else None,
                'width': float(manifest.width) if manifest.width else None,
                'height': float(manifest.height) if manifest.height else None,
                'special_fee': float(manifest.special_fee) if manifest.special_fee else None,
                'created_at': manifest.created_at.isoformat() if manifest.created_at else None,
                'updated_at': manifest.updated_at.isoformat() if manifest.updated_at else None
            }
            
            return {
                'success': True,
                'data': manifest_dict
            }
            
        except Exception as e:
            self.logger.error(f"根据快递单号获取理货单失败: {str(e)}")
            return {
                'success': False,
                'error': f"查询失败: {str(e)}",
                'data': None
            }

    def validate_manifest_data(self, data: Dict[str, Any]) -> List[str]:
        """
        验证理货单数据
        
        Args:
            data: 理货单数据
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        # 必需字段验证
        required_fields = {
            'tracking_number': '快递单号',
            'manifest_date': '理货日期',
            'transport_code': '运输代码',
            'customer_code': '客户代码',
            'goods_code': '货物代码'
        }
        
        for field, field_name in required_fields.items():
            if field not in data or not data[field] or str(data[field]).strip() == '':
                errors.append(f"{field_name}不能为空")
        
        # 字段长度验证
        string_fields = {
            'tracking_number': ('快递单号', 50),
            'transport_code': ('运输代码', 20),
            'customer_code': ('客户代码', 20),
            'goods_code': ('货物代码', 20),
            'package_number': ('集包单号', 50)
        }
        
        for field, (field_name, max_length) in string_fields.items():
            if field in data and data[field] and len(str(data[field]).strip()) > max_length:
                errors.append(f"{field_name}长度不能超过{max_length}个字符")
        
        # 快递单号格式验证
        if 'tracking_number' in data and data['tracking_number']:
            import re
            if not re.match(r'^[A-Za-z0-9]+$', str(data['tracking_number']).strip()):
                errors.append("快递单号只能包含字母和数字")
        
        # 日期验证
        if 'manifest_date' in data and data['manifest_date']:
            try:
                if isinstance(data['manifest_date'], str):
                    datetime.strptime(data['manifest_date'], '%Y-%m-%d')
                elif not isinstance(data['manifest_date'], (date, datetime)):
                    errors.append("理货日期格式不正确")
            except ValueError:
                errors.append("理货日期格式不正确，应为YYYY-MM-DD")
        
        # 数值字段验证
        numeric_fields = {
            'weight': ('重量', 0, 999999.999),
            'length': ('长度', 0, 999999.99),
            'width': ('宽度', 0, 999999.99),
            'height': ('高度', 0, 999999.99),
            'special_fee': ('特殊费用', 0, 99999999.99)
        }
        
        for field, (field_name, min_val, max_val) in numeric_fields.items():
            if field in data and data[field] is not None and str(data[field]).strip() != '':
                try:
                    value = Decimal(str(data[field]))
                    if value < min_val:
                        errors.append(f"{field_name}不能小于{min_val}")
                    if value > max_val:
                        errors.append(f"{field_name}不能大于{max_val}")
                except (InvalidOperation, ValueError):
                    errors.append(f"{field_name}必须是有效数字")
        
        return errors

    def create_manifest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的理货单记录
        
        Args:
            data: 理货单数据
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            # 验证数据
            errors = self.validate_manifest_data(data)
            if errors:
                return {
                    'success': False,
                    'errors': errors,
                    'data': None
                }
            
            # 检查快递单号是否已存在
            existing = self.db.query(CargoManifest).filter(
                CargoManifest.tracking_number == data['tracking_number'].strip()
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'errors': ['快递单号已存在'],
                    'data': None
                }
            
            # 准备数据
            manifest_data = {}
            for field in ['tracking_number', 'transport_code', 'customer_code', 'goods_code', 'package_number']:
                if field in data and data[field] is not None:
                    manifest_data[field] = str(data[field]).strip()
            
            # 处理日期
            if 'manifest_date' in data and data['manifest_date']:
                if isinstance(data['manifest_date'], str):
                    manifest_data['manifest_date'] = datetime.strptime(data['manifest_date'], '%Y-%m-%d').date()
                elif isinstance(data['manifest_date'], datetime):
                    manifest_data['manifest_date'] = data['manifest_date'].date()
                elif isinstance(data['manifest_date'], date):
                    manifest_data['manifest_date'] = data['manifest_date']
            
            # 处理数值字段
            for field in ['weight', 'length', 'width', 'height', 'special_fee']:
                if field in data and data[field] is not None and str(data[field]).strip() != '':
                    manifest_data[field] = Decimal(str(data[field]))
            
            # 创建记录
            new_manifest = CargoManifest(**manifest_data)
            self.db.add(new_manifest)
            self.db.commit()
            
            # 刷新对象以获取生成的ID
            self.db.refresh(new_manifest)
            
            # 手动触发同步通知（确保实时性）
            try:
                data_sync_service._handle_manifest_change('insert', new_manifest)
            except Exception as sync_e:
                self.logger.warning(f"手动触发同步通知失败: {str(sync_e)}")
            
            self.logger.info(f"创建理货单成功: {new_manifest.tracking_number}")
            
            return {
                'success': True,
                'data': {
                    'id': new_manifest.id,
                    'tracking_number': new_manifest.tracking_number
                },
                'message': '理货单创建成功'
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"创建理货单失败: {str(e)}")
            return {
                'success': False,
                'errors': [f"创建失败: {str(e)}"],
                'data': None
            }

    def update_manifest(self, manifest_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新理货单记录
        
        Args:
            manifest_id: 理货单ID
            data: 更新数据
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            # 获取现有记录
            manifest = self.db.query(CargoManifest).filter(CargoManifest.id == manifest_id).first()
            
            if not manifest:
                return {
                    'success': False,
                    'errors': ['理货单不存在'],
                    'data': None
                }
            
            # 验证数据
            errors = self.validate_manifest_data(data)
            if errors:
                return {
                    'success': False,
                    'errors': errors,
                    'data': None
                }
            
            # 检查快递单号是否与其他记录冲突
            if 'tracking_number' in data and data['tracking_number'].strip() != manifest.tracking_number:
                existing = self.db.query(CargoManifest).filter(
                    and_(
                        CargoManifest.tracking_number == data['tracking_number'].strip(),
                        CargoManifest.id != manifest_id
                    )
                ).first()
                
                if existing:
                    return {
                        'success': False,
                        'errors': ['快递单号已被其他记录使用'],
                        'data': None
                    }
            
            # 记录更新前的状态
            old_tracking_number = manifest.tracking_number
            
            # 更新字段
            for field in ['tracking_number', 'transport_code', 'customer_code', 'goods_code', 'package_number']:
                if field in data and data[field] is not None:
                    setattr(manifest, field, str(data[field]).strip())
            
            # 处理日期
            if 'manifest_date' in data and data['manifest_date']:
                if isinstance(data['manifest_date'], str):
                    manifest.manifest_date = datetime.strptime(data['manifest_date'], '%Y-%m-%d').date()
                elif isinstance(data['manifest_date'], datetime):
                    manifest.manifest_date = data['manifest_date'].date()
                elif isinstance(data['manifest_date'], date):
                    manifest.manifest_date = data['manifest_date']
            
            # 处理数值字段
            for field in ['weight', 'length', 'width', 'height', 'special_fee']:
                if field in data:
                    if data[field] is not None and str(data[field]).strip() != '':
                        setattr(manifest, field, Decimal(str(data[field])))
                    else:
                        setattr(manifest, field, None)
            
            # 提交更新
            self.db.commit()
            
            # 手动触发同步通知（确保实时性）
            try:
                data_sync_service._handle_manifest_change('update', manifest)
            except Exception as sync_e:
                self.logger.warning(f"手动触发同步通知失败: {str(sync_e)}")
            
            self.logger.info(f"更新理货单成功: {old_tracking_number} -> {manifest.tracking_number}")
            
            return {
                'success': True,
                'data': {
                    'id': manifest.id,
                    'tracking_number': manifest.tracking_number
                },
                'message': '理货单更新成功'
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"更新理货单失败: {str(e)}")
            return {
                'success': False,
                'errors': [f"更新失败: {str(e)}"],
                'data': None
            }

    def delete_manifest(self, manifest_id: int, operator: str = None) -> Dict[str, Any]:
        """
        删除理货单记录
        
        Args:
            manifest_id: 理货单ID
            operator: 操作员（用于日志记录）
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            # 获取要删除的记录
            manifest = self.db.query(CargoManifest).filter(CargoManifest.id == manifest_id).first()
            
            if not manifest:
                return {
                    'success': False,
                    'error': '理货单不存在',
                    'data': None
                }
            
            # 记录删除信息
            tracking_number = manifest.tracking_number
            
            # 手动触发同步通知（在删除前）
            try:
                data_sync_service._handle_manifest_change('delete', manifest)
            except Exception as sync_e:
                self.logger.warning(f"手动触发同步通知失败: {str(sync_e)}")
            
            # 执行删除
            self.db.delete(manifest)
            self.db.commit()
            
            # 记录操作日志
            log_message = f"删除理货单: {tracking_number}"
            if operator:
                log_message += f" (操作员: {operator})"
            self.logger.info(log_message)
            
            return {
                'success': True,
                'data': {
                    'id': manifest_id,
                    'tracking_number': tracking_number
                },
                'message': '理货单删除成功'
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"删除理货单失败: {str(e)}")
            return {
                'success': False,
                'error': f"删除失败: {str(e)}",
                'data': None
            }

    def batch_delete_manifests(self, manifest_ids: List[int], operator: str = None) -> Dict[str, Any]:
        """
        批量删除理货单记录
        
        Args:
            manifest_ids: 理货单ID列表
            operator: 操作员（用于日志记录）
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        if not manifest_ids:
            return {
                'success': False,
                'error': '未指定要删除的记录',
                'data': None
            }
        
        try:
            # 获取要删除的记录
            manifests = self.db.query(CargoManifest).filter(
                CargoManifest.id.in_(manifest_ids)
            ).all()
            
            if not manifests:
                return {
                    'success': False,
                    'error': '未找到要删除的记录',
                    'data': None
                }
            
            # 记录删除信息
            deleted_tracking_numbers = [m.tracking_number for m in manifests]
            deleted_count = len(manifests)
            
            # 手动触发同步通知（在删除前）
            try:
                for manifest in manifests:
                    data_sync_service._handle_manifest_change('delete', manifest)
            except Exception as sync_e:
                self.logger.warning(f"手动触发批量同步通知失败: {str(sync_e)}")
            
            # 执行批量删除
            self.db.query(CargoManifest).filter(
                CargoManifest.id.in_(manifest_ids)
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            # 记录操作日志
            log_message = f"批量删除理货单: {deleted_count}条记录 ({', '.join(deleted_tracking_numbers)})"
            if operator:
                log_message += f" (操作员: {operator})"
            self.logger.info(log_message)
            
            return {
                'success': True,
                'data': {
                    'deleted_count': deleted_count,
                    'deleted_ids': manifest_ids,
                    'deleted_tracking_numbers': deleted_tracking_numbers
                },
                'message': f'成功删除{deleted_count}条理货单记录'
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"批量删除理货单失败: {str(e)}")
            return {
                'success': False,
                'error': f"批量删除失败: {str(e)}",
                'data': None
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取理货单统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        try:
            # 总记录数
            total_count = self.db.query(CargoManifest).count()
            
            # 有集包单号的记录数
            with_package_count = self.db.query(CargoManifest).filter(
                CargoManifest.package_number.isnot(None),
                CargoManifest.package_number != ''
            ).count()
            
            # 无集包单号的记录数
            without_package_count = total_count - with_package_count
            
            # 最近7天新增记录数
            from datetime import datetime, timedelta
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_count = self.db.query(CargoManifest).filter(
                CargoManifest.created_at >= seven_days_ago
            ).count()
            
            return {
                'success': True,
                'data': {
                    'total_count': total_count,
                    'with_package_count': with_package_count,
                    'without_package_count': without_package_count,
                    'recent_count': recent_count,
                    'package_rate': round(with_package_count / total_count * 100, 2) if total_count > 0 else 0,
                    'sync_statistics': data_sync_service.get_sync_statistics()
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {
                'success': False,
                'error': f"获取统计信息失败: {str(e)}",
                'data': None
            }