"""
数据同步集成测试
测试理货单变更时的实时同步机制
"""

import pytest
import asyncio
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.cargo_manifest import CargoManifest
from app.services.data_sync_service import data_sync_service
from app.services.intelligent_query_service import IntelligentQueryService
from app.services.manifest_service import ManifestService


class TestDataSyncIntegration:
    """数据同步集成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 清理缓存和待处理操作
        data_sync_service.invalidate_all_cache()
        data_sync_service.clear_pending_sync_operations()
    
    def test_manifest_creation_sync(self):
        """测试理货单创建时的同步机制"""
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建理货单服务
            manifest_service = ManifestService(db)
            
            # 准备测试数据
            test_data = {
                'tracking_number': 'TEST_SYNC_001',
                'manifest_date': '2024-01-01',
                'transport_code': 'TC001',
                'customer_code': 'CC001',
                'goods_code': 'GC001',
                'package_number': 'PKG_SYNC_001',
                'weight': 1.5
            }
            
            # 获取创建前的同步统计
            before_stats = data_sync_service.get_sync_statistics()
            
            # 创建理货单
            result = manifest_service.create_manifest(test_data)
            
            # 验证创建成功
            assert result['success'] is True
            assert result['data']['tracking_number'] == 'TEST_SYNC_001'
            
            # 验证同步操作被记录
            after_stats = data_sync_service.get_sync_statistics()
            assert after_stats['sync_operations'] > before_stats['sync_operations']
            
            # 验证缓存中有数据
            cached_data = data_sync_service.get_cached_manifest('TEST_SYNC_001')
            assert cached_data is not None
            assert cached_data['tracking_number'] == 'TEST_SYNC_001'
            assert cached_data['package_number'] == 'PKG_SYNC_001'
            
            print("✓ 理货单创建同步测试通过")
            
        finally:
            # 清理测试数据
            try:
                db.query(CargoManifest).filter(
                    CargoManifest.tracking_number == 'TEST_SYNC_001'
                ).delete()
                db.commit()
            except:
                pass
            db.close()
    
    def test_manifest_update_sync(self):
        """测试理货单更新时的同步机制"""
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建理货单服务
            manifest_service = ManifestService(db)
            
            # 先创建一个理货单
            test_data = {
                'tracking_number': 'TEST_SYNC_002',
                'manifest_date': '2024-01-01',
                'transport_code': 'TC002',
                'customer_code': 'CC002',
                'goods_code': 'GC002',
                'package_number': 'PKG_SYNC_002',
                'weight': 2.0
            }
            
            create_result = manifest_service.create_manifest(test_data)
            assert create_result['success'] is True
            manifest_id = create_result['data']['id']
            
            # 等待一下确保创建操作完成
            import time
            time.sleep(0.1)
            
            # 获取更新前的同步统计
            before_stats = data_sync_service.get_sync_statistics()
            
            # 更新理货单
            update_data = {
                'package_number': 'PKG_SYNC_002_UPDATED',
                'weight': 2.5
            }
            
            update_result = manifest_service.update_manifest(manifest_id, update_data)
            
            # 验证更新成功
            assert update_result['success'] is True
            
            # 验证同步操作被记录
            after_stats = data_sync_service.get_sync_statistics()
            assert after_stats['sync_operations'] > before_stats['sync_operations']
            
            # 验证缓存被失效（应该重新从数据库加载）
            # 强制同步以确保缓存更新
            sync_result = data_sync_service.force_sync_manifest('TEST_SYNC_002', db)
            assert sync_result['success'] is True
            
            cached_data = data_sync_service.get_cached_manifest('TEST_SYNC_002')
            assert cached_data is not None
            assert cached_data['package_number'] == 'PKG_SYNC_002_UPDATED'
            
            print("✓ 理货单更新同步测试通过")
            
        finally:
            # 清理测试数据
            try:
                db.query(CargoManifest).filter(
                    CargoManifest.tracking_number == 'TEST_SYNC_002'
                ).delete()
                db.commit()
            except:
                pass
            db.close()
    
    def test_intelligent_query_cache_integration(self):
        """测试智能查询服务与缓存的集成"""
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 创建理货单服务和智能查询服务
            manifest_service = ManifestService(db)
            query_service = IntelligentQueryService(db)
            
            # 创建测试理货单
            test_data = {
                'tracking_number': 'TEST_SYNC_003',
                'manifest_date': '2024-01-01',
                'transport_code': 'TC003',
                'customer_code': 'CC003',
                'goods_code': 'GC003',
                'package_number': 'PKG_SYNC_003',
                'weight': 3.0
            }
            
            create_result = manifest_service.create_manifest(test_data)
            assert create_result['success'] is True
            
            # 等待同步完成
            import time
            time.sleep(0.1)
            
            # 第一次查询（应该从数据库加载并缓存）
            before_stats = data_sync_service.get_sync_statistics()
            manifest = asyncio.run(query_service._find_manifest_by_tracking_number('TEST_SYNC_003'))
            
            assert manifest is not None
            assert manifest.tracking_number == 'TEST_SYNC_003'
            assert manifest.package_number == 'PKG_SYNC_003'
            
            # 第二次查询（应该从缓存加载）
            manifest2 = asyncio.run(query_service._find_manifest_by_tracking_number('TEST_SYNC_003'))
            after_stats = data_sync_service.get_sync_statistics()
            
            assert manifest2 is not None
            assert manifest2.tracking_number == 'TEST_SYNC_003'
            
            # 验证缓存命中率提高
            assert after_stats['cache_hits'] > before_stats['cache_hits']
            
            print("✓ 智能查询缓存集成测试通过")
            
        finally:
            # 清理测试数据
            try:
                db.query(CargoManifest).filter(
                    CargoManifest.tracking_number == 'TEST_SYNC_003'
                ).delete()
                db.commit()
            except:
                pass
            db.close()
    
    def test_sync_statistics(self):
        """测试同步统计信息"""
        # 获取同步统计信息
        stats = data_sync_service.get_sync_statistics()
        
        # 验证统计信息结构
        assert 'cache_size' in stats
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert 'cache_hit_rate' in stats
        assert 'sync_operations' in stats
        assert 'active_listeners' in stats
        assert 'pending_operations' in stats
        
        # 验证缓存命中率计算
        if stats['cache_hits'] + stats['cache_misses'] > 0:
            expected_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
            assert abs(stats['cache_hit_rate'] - expected_rate) < 0.01
        
        print("✓ 同步统计信息测试通过")
    
    def test_cache_invalidation(self):
        """测试缓存失效机制"""
        # 手动添加一些测试缓存
        test_data = {
            'tracking_number': 'TEST_CACHE_001',
            'package_number': 'PKG_CACHE_001'
        }
        
        data_sync_service.cache_manifest('TEST_CACHE_001', test_data)
        
        # 验证缓存存在
        cached = data_sync_service.get_cached_manifest('TEST_CACHE_001')
        assert cached is not None
        assert cached['tracking_number'] == 'TEST_CACHE_001'
        
        # 失效所有缓存
        data_sync_service.invalidate_all_cache()
        
        # 验证缓存被清空
        cached_after = data_sync_service.get_cached_manifest('TEST_CACHE_001')
        assert cached_after is None
        
        # 验证统计信息更新
        stats = data_sync_service.get_sync_statistics()
        assert stats['cache_size'] == 0
        
        print("✓ 缓存失效机制测试通过")


def run_sync_tests():
    """运行数据同步测试"""
    print("开始数据同步集成测试...")
    
    test_instance = TestDataSyncIntegration()
    
    try:
        test_instance.setup_method()
        test_instance.test_manifest_creation_sync()
        
        test_instance.setup_method()
        test_instance.test_manifest_update_sync()
        
        test_instance.setup_method()
        asyncio.run(test_instance.test_intelligent_query_cache_integration())
        
        test_instance.setup_method()
        test_instance.test_sync_statistics()
        
        test_instance.setup_method()
        test_instance.test_cache_invalidation()
        
        print("\n✅ 所有数据同步集成测试通过！")
        
    except Exception as e:
        print(f"\n❌ 数据同步集成测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    run_sync_tests()