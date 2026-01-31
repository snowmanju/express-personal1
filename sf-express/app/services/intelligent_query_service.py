"""
智能查询服务 (Intelligent Query Service)
实现快递单号智能判断和查询逻辑
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.cargo_manifest import CargoManifest
from app.services.kuaidi100_client import Kuaidi100Client, Kuaidi100APIError
from app.services.input_validator import validate_tracking_number, validate_and_clean_input
from app.services.data_sync_service import data_sync_service

logger = logging.getLogger(__name__)


class IntelligentQueryService:
    """
    智能查询服务类
    
    提供快递单号的智能判断功能：
    1. 检查快递单号是否存在集包单号关联
    2. 根据判断结果选择使用集包单号或原单号进行查询
    3. 集成快递100 API调用并返回标准化结果
    4. 集成数据同步服务，支持缓存和实时更新
    """
    
    def __init__(self, db_session: Session):
        """
        初始化智能查询服务
        
        Args:
            db_session: 数据库会话对象
        """
        self.db_session = db_session
        self.kuaidi100_client = Kuaidi100Client()
        
        # 注册为数据同步监听器
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
            
            logger.info(f"收到理货单变更通知: {operation} - {tracking_number}")
            
            # 根据操作类型处理
            if operation in ['insert', 'update']:
                # 预加载到缓存
                await self._preload_manifest_to_cache(tracking_number)
            elif operation == 'delete':
                # 缓存已在数据同步服务中失效，这里记录日志
                logger.info(f"理货单删除，缓存已失效: {tracking_number}")
                
        except Exception as e:
            logger.error(f"处理理货单变更通知失败: {str(e)}")
    
    async def _preload_manifest_to_cache(self, tracking_number: str):
        """
        预加载理货单到缓存
        
        Args:
            tracking_number: 快递单号
        """
        try:
            # 强制从数据库同步最新数据
            sync_result = data_sync_service.force_sync_manifest(tracking_number, self.db_session)
            if sync_result.get('success'):
                logger.debug(f"预加载理货单到缓存成功: {tracking_number}")
            else:
                logger.warning(f"预加载理货单到缓存失败: {tracking_number}")
        except Exception as e:
            logger.error(f"预加载理货单到缓存异常: {str(e)}")
        
    async def query_tracking(self, tracking_number: str, company_code: str = "auto", phone: Optional[str] = None) -> Dict[str, Any]:
        """
        智能查询快递信息
        
        实现智能判断逻辑：
        1. 首先验证和清理输入的快递单号
        2. 查询理货单表检查是否存在集包单号关联
        3. 如果存在集包单号，使用集包单号调用API
        4. 如果不存在集包单号，使用原单号调用API
        5. 返回标准化的查询结果，包含查询策略信息
        
        Args:
            tracking_number: 快递单号
            company_code: 快递公司编码，默认为"auto"自动识别
            phone: 手机号后四位（可选）
            
        Returns:
            包含快递信息和查询策略的字典
        """
        logger.info(f"开始智能查询快递单号: {tracking_number}")
        
        try:
            # 步骤1: 输入验证和清理
            validation_result = validate_tracking_number(tracking_number)
            if not validation_result.is_valid:
                logger.warning(f"快递单号验证失败: {tracking_number}, 错误: {validation_result.errors}")
                return {
                    "success": False,
                    "original_tracking_number": tracking_number,
                    "query_tracking_number": tracking_number,
                    "query_type": "original",
                    "has_package_association": False,
                    "manifest_info": None,
                    "tracking_info": None,
                    "error": f"输入验证失败: {'; '.join(validation_result.errors)}",
                    "query_time": None
                }
            
            # 使用清理后的快递单号
            cleaned_tracking_number = validation_result.cleaned_value
            logger.info(f"快递单号验证通过: {cleaned_tracking_number}")
            
            # 验证可选的手机号参数
            if phone:
                phone_validation = validate_and_clean_input(phone, "手机号")
                if not phone_validation.is_valid:
                    logger.warning(f"手机号验证失败: {phone}, 错误: {phone_validation.errors}")
                    return {
                        "success": False,
                        "original_tracking_number": tracking_number,
                        "query_tracking_number": cleaned_tracking_number,
                        "query_type": "original",
                        "has_package_association": False,
                        "manifest_info": None,
                        "tracking_info": None,
                        "error": f"手机号验证失败: {'; '.join(phone_validation.errors)}",
                        "query_time": None
                    }
                phone = phone_validation.cleaned_value
            
            # 步骤2: 查询理货单表检查集包单号关联
            manifest = await self._find_manifest_by_tracking_number(cleaned_tracking_number)
            
            # 步骤3: 根据查询结果决定查询策略
            if manifest and manifest.package_number:
                # 存在集包单号，使用集包单号查询
                query_number = manifest.package_number
                query_type = "package"
                logger.info(f"找到集包单号关联: {cleaned_tracking_number} -> {query_number}")
            else:
                # 不存在集包单号，使用原单号查询
                query_number = cleaned_tracking_number
                query_type = "original"
                logger.info(f"未找到集包单号关联，使用原单号查询: {cleaned_tracking_number}")
            
            # 步骤4: 调用快递100 API
            api_result = await self.kuaidi100_client.query_tracking(
                tracking_number=query_number,
                company_code=company_code,
                phone=phone
            )
            
            # 步骤5: 构建标准化响应结果
            tracking_info = None
            if api_result.get("success") and api_result.get("raw_response"):
                raw = api_result["raw_response"]
                tracking_info = {
                    "com": api_result.get("company_code", ""),
                    "company": api_result.get("company_name", ""),
                    "state": raw.get("state", ""),
                    "data": raw.get("data", []),
                    "nu": raw.get("nu", query_number),
                    "ischeck": raw.get("ischeck", "0"),
                    "condition": raw.get("condition", ""),
                    "status": raw.get("status", "200")
                }
            
            result = {
                "success": api_result.get("success", False),
                "original_tracking_number": tracking_number,
                "cleaned_tracking_number": cleaned_tracking_number,
                "query_tracking_number": query_number,
                "query_type": query_type,
                "has_package_association": manifest is not None and manifest.package_number is not None,
                "manifest_info": self._format_manifest_info(manifest) if manifest else None,
                "tracking_info": tracking_info,
                "error": api_result.get("error") if not api_result.get("success") else None,
                "query_time": api_result.get("query_time")
            }
            
            if result["success"]:
                logger.info(f"智能查询成功: {cleaned_tracking_number}, 查询类型: {query_type}, 状态: {result['tracking_info']['status']}")
            else:
                logger.warning(f"智能查询失败: {cleaned_tracking_number}, 错误: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"智能查询发生异常: {tracking_number}, 异常: {str(e)}")
            
            # 返回异常结果，确保不暴露系统内部错误
            return {
                "success": False,
                "original_tracking_number": tracking_number,
                "query_tracking_number": tracking_number,
                "query_type": "original",
                "has_package_association": False,
                "manifest_info": None,
                "tracking_info": None,
                "error": "系统异常，请稍后重试",
                "query_time": None
            }
    
    async def _find_manifest_by_tracking_number(self, tracking_number: str) -> Optional[CargoManifest]:
        """
        根据快递单号查询理货单记录（支持缓存）
        
        Args:
            tracking_number: 快递单号
            
        Returns:
            理货单记录对象，如果不存在则返回None
        """
        try:
            # 首先尝试从缓存获取
            cached_manifest = data_sync_service.get_cached_manifest(tracking_number)
            if cached_manifest:
                logger.debug(f"从缓存获取理货单记录: {tracking_number}")
                # 将缓存数据转换为模型对象（简化版，仅包含查询需要的字段）
                if cached_manifest.get('package_number'):
                    # 创建一个简化的对象来模拟CargoManifest
                    class CachedManifest:
                        def __init__(self, data):
                            self.id = data.get('id')
                            self.tracking_number = data.get('tracking_number')
                            self.package_number = data.get('package_number')
                            self.manifest_date = data.get('manifest_date')
                            self.transport_code = data.get('transport_code')
                            self.customer_code = data.get('customer_code')
                            self.goods_code = data.get('goods_code')
                            self.weight = data.get('weight')
                            self.length = data.get('dimensions', {}).get('length')
                            self.width = data.get('dimensions', {}).get('width')
                            self.height = data.get('dimensions', {}).get('height')
                            self.special_fee = data.get('special_fee')
                            self.created_at = data.get('created_at')
                            self.updated_at = data.get('updated_at')
                    
                    return CachedManifest(cached_manifest)
                else:
                    return None
            
            # 缓存未命中，从数据库查询
            manifest = self.db_session.query(CargoManifest).filter(
                CargoManifest.tracking_number == tracking_number
            ).first()
            
            if manifest:
                logger.debug(f"从数据库获取理货单记录: {tracking_number} -> {manifest.package_number}")
                
                # 将查询结果缓存
                manifest_data = {
                    'id': manifest.id,
                    'tracking_number': manifest.tracking_number,
                    'package_number': manifest.package_number,
                    'manifest_date': manifest.manifest_date.isoformat() if manifest.manifest_date else None,
                    'transport_code': manifest.transport_code,
                    'customer_code': manifest.customer_code,
                    'goods_code': manifest.goods_code,
                    'weight': float(manifest.weight) if manifest.weight else None,
                    'dimensions': {
                        'length': float(manifest.length) if manifest.length else None,
                        'width': float(manifest.width) if manifest.width else None,
                        'height': float(manifest.height) if manifest.height else None
                    },
                    'special_fee': float(manifest.special_fee) if manifest.special_fee else None,
                    'created_at': manifest.created_at.isoformat() if manifest.created_at else None,
                    'updated_at': manifest.updated_at.isoformat() if manifest.updated_at else None
                }
                data_sync_service.cache_manifest(tracking_number, manifest_data)
            else:
                logger.debug(f"未找到理货单记录: {tracking_number}")
                # 缓存空结果（避免重复查询）
                data_sync_service.cache_manifest(tracking_number, {'not_found': True})
            
            return manifest
            
        except Exception as e:
            logger.error(f"查询理货单记录失败: {tracking_number}, 异常: {str(e)}")
            # 数据库查询失败时返回None，使用原单号查询
            return None
    
    def _format_manifest_info(self, manifest: CargoManifest) -> Dict[str, Any]:
        """
        格式化理货单信息
        
        Args:
            manifest: 理货单记录对象
            
        Returns:
            格式化后的理货单信息字典
        """
        if not manifest:
            return None
        
        return {
            "id": manifest.id,
            "tracking_number": manifest.tracking_number,
            "package_number": manifest.package_number,
            "manifest_date": manifest.manifest_date.isoformat() if manifest.manifest_date else None,
            "transport_code": manifest.transport_code,
            "customer_code": manifest.customer_code,
            "goods_code": manifest.goods_code,
            "weight": float(manifest.weight) if manifest.weight else None,
            "dimensions": {
                "length": float(manifest.length) if manifest.length else None,
                "width": float(manifest.width) if manifest.width else None,
                "height": float(manifest.height) if manifest.height else None
            },
            "special_fee": float(manifest.special_fee) if manifest.special_fee else None,
            "created_at": manifest.created_at.isoformat() if manifest.created_at else None,
            "updated_at": manifest.updated_at.isoformat() if manifest.updated_at else None
        }
    
    async def batch_intelligent_query(self, tracking_numbers: list[str], company_code: str = "auto") -> Dict[str, Any]:
        """
        批量智能查询快递信息
        
        Args:
            tracking_numbers: 快递单号列表
            company_code: 快递公司编码
            
        Returns:
            包含所有查询结果的字典
        """
        logger.info(f"开始批量智能查询，单号数量: {len(tracking_numbers)}")
        
        # 验证输入参数
        if not tracking_numbers:
            return {
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "results": [],
                "error": "快递单号列表不能为空"
            }
        
        # 限制批量查询数量
        if len(tracking_numbers) > 100:
            return {
                "total": len(tracking_numbers),
                "success_count": 0,
                "failed_count": len(tracking_numbers),
                "results": [],
                "error": "批量查询数量不能超过100个"
            }
        
        results = []
        success_count = 0
        failed_count = 0
        
        for tracking_number in tracking_numbers:
            try:
                result = await self.query_tracking(tracking_number, company_code)
                results.append(result)
                
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"批量查询中单号 {tracking_number} 失败: {str(e)}")
                results.append({
                    "success": False,
                    "original_tracking_number": tracking_number,
                    "query_tracking_number": tracking_number,
                    "query_type": "original",
                    "has_package_association": False,
                    "manifest_info": None,
                    "tracking_info": None,
                    "error": "查询异常",
                    "query_time": None
                })
                failed_count += 1
        
        batch_result = {
            "total": len(tracking_numbers),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }
        
        logger.info(f"批量智能查询完成，成功: {success_count}, 失败: {failed_count}")
        return batch_result
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """
        获取查询统计信息
        
        Returns:
            包含理货单统计信息和同步状态的字典
        """
        try:
            # 统计理货单总数
            total_manifests = self.db_session.query(CargoManifest).count()
            
            # 统计有集包单号的记录数
            with_package = self.db_session.query(CargoManifest).filter(
                CargoManifest.package_number.isnot(None),
                CargoManifest.package_number != ""
            ).count()
            
            # 统计无集包单号的记录数
            without_package = total_manifests - with_package
            
            # 获取数据同步统计信息
            sync_stats = data_sync_service.get_sync_statistics()
            
            return {
                "total_manifests": total_manifests,
                "with_package_number": with_package,
                "without_package_number": without_package,
                "package_association_rate": round(with_package / total_manifests * 100, 2) if total_manifests > 0 else 0,
                "sync_statistics": sync_stats
            }
            
        except Exception as e:
            logger.error(f"获取查询统计信息失败: {str(e)}")
            return {
                "total_manifests": 0,
                "with_package_number": 0,
                "without_package_number": 0,
                "package_association_rate": 0,
                "sync_statistics": {},
                "error": "统计信息获取失败"
            }