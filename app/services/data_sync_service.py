"""
数据同步服务 (Data Synchronization Service)
确保理货单变更实时更新查询逻辑，提供缓存失效和刷新机制
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import event
from threading import Lock
import weakref

from app.models.cargo_manifest import CargoManifest

logger = logging.getLogger(__name__)


class DataSyncService:
    """
    数据同步服务类
    
    提供以下功能：
    1. 理货单数据变更监听
    2. 缓存失效和刷新机制
    3. 查询服务实时同步通知
    4. 数据一致性保证
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataSyncService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化数据同步服务"""
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        
        # 缓存管理
        self._manifest_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=30)  # 缓存30分钟过期
        
        # 同步状态管理
        self._sync_listeners: Set[weakref.ref] = set()
        self._pending_sync_operations: List[Dict[str, Any]] = []
        self._sync_lock = Lock()
        
        # 统计信息
        self._sync_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'sync_operations': 0,
            'last_sync_time': None
        }
        
        # 注册数据库事件监听器
        self._register_db_event_listeners()
        
        self.logger.info("数据同步服务初始化完成")
    
    def _register_db_event_listeners(self):
        """注册数据库事件监听器"""
        try:
            # 监听理货单记录的增删改事件
            event.listen(CargoManifest, 'after_insert', self._on_manifest_inserted)
            event.listen(CargoManifest, 'after_update', self._on_manifest_updated)
            event.listen(CargoManifest, 'after_delete', self._on_manifest_deleted)
            
            self.logger.info("数据库事件监听器注册成功")
        except Exception as e:
            self.logger.error(f"注册数据库事件监听器失败: {str(e)}")
    
    def _on_manifest_inserted(self, mapper, connection, target):
        """理货单插入事件处理"""
        try:
            self._handle_manifest_change('insert', target)
        except Exception as e:
            self.logger.error(f"处理理货单插入事件失败: {str(e)}")
    
    def _on_manifest_updated(self, mapper, connection, target):
        """理货单更新事件处理"""
        try:
            self._handle_manifest_change('update', target)
        except Exception as e:
            self.logger.error(f"处理理货单更新事件失败: {str(e)}")
    
    def _on_manifest_deleted(self, mapper, connection, target):
        """理货单删除事件处理"""
        try:
            self._handle_manifest_change('delete', target)
        except Exception as e:
            self.logger.error(f"处理理货单删除事件失败: {str(e)}")
    
    def _handle_manifest_change(self, operation: str, manifest: CargoManifest):
        """处理理货单数据变更"""
        with self._sync_lock:
            try:
                tracking_number = manifest.tracking_number
                
                # 记录同步操作
                sync_operation = {
                    'operation': operation,
                    'tracking_number': tracking_number,
                    'package_number': getattr(manifest, 'package_number', None),
                    'timestamp': datetime.now(),
                    'manifest_id': getattr(manifest, 'id', None)
                }
                
                self._pending_sync_operations.append(sync_operation)
                self._sync_stats['sync_operations'] += 1
                
                # 立即处理缓存失效
                self._invalidate_cache_for_tracking_number(tracking_number)
                
                # 通知所有监听器
                self._notify_sync_listeners(sync_operation)
                
                self.logger.info(f"处理理货单{operation}事件: {tracking_number}")
                
            except Exception as e:
                self.logger.error(f"处理理货单变更失败: {str(e)}")
    
    def _invalidate_cache_for_tracking_number(self, tracking_number: str):
        """为指定快递单号失效缓存"""
        try:
            # 移除直接缓存
            if tracking_number in self._manifest_cache:
                del self._manifest_cache[tracking_number]
                self.logger.debug(f"失效缓存: {tracking_number}")
            
            # 移除时间戳
            if tracking_number in self._cache_timestamps:
                del self._cache_timestamps[tracking_number]
            
            # 清理过期缓存
            self._cleanup_expired_cache()
            
        except Exception as e:
            self.logger.error(f"失效缓存失败: {str(e)}")
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self._manifest_cache:
                    del self._manifest_cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
            
            if expired_keys:
                self.logger.debug(f"清理过期缓存: {len(expired_keys)}个条目")
                
        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {str(e)}")
    
    def _notify_sync_listeners(self, sync_operation: Dict[str, Any]):
        """通知同步监听器"""
        try:
            # 清理失效的弱引用
            dead_refs = set()
            for listener_ref in self._sync_listeners:
                listener = listener_ref()
                if listener is None:
                    dead_refs.add(listener_ref)
                else:
                    try:
                        # 异步通知监听器
                        if hasattr(listener, 'on_manifest_changed'):
                            asyncio.create_task(listener.on_manifest_changed(sync_operation))
                    except Exception as e:
                        self.logger.error(f"通知监听器失败: {str(e)}")
            
            # 移除失效的弱引用
            self._sync_listeners -= dead_refs
            
        except Exception as e:
            self.logger.error(f"通知同步监听器失败: {str(e)}")
    
    def register_sync_listener(self, listener):
        """注册同步监听器"""
        try:
            listener_ref = weakref.ref(listener)
            self._sync_listeners.add(listener_ref)
            self.logger.debug(f"注册同步监听器: {type(listener).__name__}")
        except Exception as e:
            self.logger.error(f"注册同步监听器失败: {str(e)}")
    
    def unregister_sync_listener(self, listener):
        """注销同步监听器"""
        try:
            # 查找并移除对应的弱引用
            to_remove = None
            for listener_ref in self._sync_listeners:
                if listener_ref() is listener:
                    to_remove = listener_ref
                    break
            
            if to_remove:
                self._sync_listeners.remove(to_remove)
                self.logger.debug(f"注销同步监听器: {type(listener).__name__}")
                
        except Exception as e:
            self.logger.error(f"注销同步监听器失败: {str(e)}")
    
    def get_cached_manifest(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """获取缓存的理货单信息"""
        try:
            # 检查缓存是否存在且未过期
            if tracking_number in self._manifest_cache:
                cache_time = self._cache_timestamps.get(tracking_number)
                if cache_time and datetime.now() - cache_time <= self._cache_ttl:
                    self._sync_stats['cache_hits'] += 1
                    return self._manifest_cache[tracking_number]
                else:
                    # 缓存过期，移除
                    self._invalidate_cache_for_tracking_number(tracking_number)
            
            self._sync_stats['cache_misses'] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"获取缓存理货单失败: {str(e)}")
            return None
    
    def cache_manifest(self, tracking_number: str, manifest_data: Dict[str, Any]):
        """缓存理货单信息"""
        try:
            self._manifest_cache[tracking_number] = manifest_data.copy()
            self._cache_timestamps[tracking_number] = datetime.now()
            self.logger.debug(f"缓存理货单: {tracking_number}")
        except Exception as e:
            self.logger.error(f"缓存理货单失败: {str(e)}")
    
    def invalidate_all_cache(self):
        """失效所有缓存"""
        try:
            with self._sync_lock:
                self._manifest_cache.clear()
                self._cache_timestamps.clear()
                self.logger.info("已失效所有缓存")
        except Exception as e:
            self.logger.error(f"失效所有缓存失败: {str(e)}")
    
    def force_sync_manifest(self, tracking_number: str, db: Session) -> Dict[str, Any]:
        """强制同步指定理货单"""
        try:
            # 失效缓存
            self._invalidate_cache_for_tracking_number(tracking_number)
            
            # 从数据库重新加载
            manifest = db.query(CargoManifest).filter(
                CargoManifest.tracking_number == tracking_number
            ).first()
            
            if manifest:
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
                
                # 更新缓存
                self.cache_manifest(tracking_number, manifest_data)
                
                self.logger.info(f"强制同步理货单成功: {tracking_number}")
                return {
                    'success': True,
                    'data': manifest_data
                }
            else:
                self.logger.info(f"强制同步理货单，未找到记录: {tracking_number}")
                return {
                    'success': False,
                    'error': '理货单不存在'
                }
                
        except Exception as e:
            self.logger.error(f"强制同步理货单失败: {str(e)}")
            return {
                'success': False,
                'error': f'同步失败: {str(e)}'
            }
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        try:
            with self._sync_lock:
                return {
                    'cache_size': len(self._manifest_cache),
                    'cache_hits': self._sync_stats['cache_hits'],
                    'cache_misses': self._sync_stats['cache_misses'],
                    'cache_hit_rate': (
                        self._sync_stats['cache_hits'] / 
                        (self._sync_stats['cache_hits'] + self._sync_stats['cache_misses'])
                        if (self._sync_stats['cache_hits'] + self._sync_stats['cache_misses']) > 0 
                        else 0
                    ),
                    'sync_operations': self._sync_stats['sync_operations'],
                    'active_listeners': len(self._sync_listeners),
                    'pending_operations': len(self._pending_sync_operations),
                    'last_sync_time': self._sync_stats['last_sync_time'].isoformat() if self._sync_stats['last_sync_time'] else None
                }
        except Exception as e:
            self.logger.error(f"获取同步统计信息失败: {str(e)}")
            return {}
    
    def get_pending_sync_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取待处理的同步操作"""
        try:
            with self._sync_lock:
                return self._pending_sync_operations[-limit:] if self._pending_sync_operations else []
        except Exception as e:
            self.logger.error(f"获取待处理同步操作失败: {str(e)}")
            return []
    
    def clear_pending_sync_operations(self):
        """清理待处理的同步操作"""
        try:
            with self._sync_lock:
                cleared_count = len(self._pending_sync_operations)
                self._pending_sync_operations.clear()
                self._sync_stats['last_sync_time'] = datetime.now()
                self.logger.info(f"清理待处理同步操作: {cleared_count}个")
        except Exception as e:
            self.logger.error(f"清理待处理同步操作失败: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            current_time = datetime.now()
            
            # 检查缓存状态
            cache_status = "healthy"
            if len(self._manifest_cache) > 10000:  # 缓存过大
                cache_status = "warning"
            
            # 检查同步状态
            sync_status = "healthy"
            if len(self._pending_sync_operations) > 1000:  # 待处理操作过多
                sync_status = "warning"
            
            return {
                'status': 'healthy' if cache_status == 'healthy' and sync_status == 'healthy' else 'warning',
                'timestamp': current_time.isoformat(),
                'cache_status': cache_status,
                'sync_status': sync_status,
                'statistics': self.get_sync_statistics()
            }
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {str(e)}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }


# 全局数据同步服务实例
data_sync_service = DataSyncService()