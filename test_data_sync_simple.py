"""
简单的数据同步测试
Simple Data Synchronization Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_sync_service import data_sync_service


def test_data_sync_service_basic():
    """测试数据同步服务基本功能"""
    print("测试数据同步服务基本功能...")
    
    # 测试单例模式
    service1 = data_sync_service
    from app.services.data_sync_service import DataSyncService
    service2 = DataSyncService()
    
    assert service1 is service2, "数据同步服务应该是单例"
    print("✓ 单例模式测试通过")
    
    # 测试统计信息
    stats = service1.get_sync_statistics()
    assert isinstance(stats, dict), "统计信息应该是字典"
    assert 'cache_size' in stats, "统计信息应该包含缓存大小"
    assert 'sync_operations' in stats, "统计信息应该包含同步操作数"
    print("✓ 统计信息测试通过")
    
    # 测试缓存功能
    test_data = {
        'tracking_number': 'TEST001',
        'package_number': 'PKG001'
    }
    
    # 缓存数据
    service1.cache_manifest('TEST001', test_data)
    
    # 获取缓存数据
    cached = service1.get_cached_manifest('TEST001')
    assert cached is not None, "应该能获取到缓存数据"
    assert cached['tracking_number'] == 'TEST001', "缓存数据应该正确"
    print("✓ 缓存功能测试通过")
    
    # 测试缓存失效
    service1.invalidate_all_cache()
    cached_after = service1.get_cached_manifest('TEST001')
    assert cached_after is None, "缓存失效后应该获取不到数据"
    print("✓ 缓存失效测试通过")
    
    print("✅ 数据同步服务基本功能测试全部通过！")


def test_sync_health_check():
    """测试同步服务健康检查"""
    print("\n测试同步服务健康检查...")
    
    import asyncio
    
    async def run_health_check():
        health = await data_sync_service.health_check()
        assert isinstance(health, dict), "健康检查结果应该是字典"
        assert 'status' in health, "健康检查应该包含状态"
        assert 'timestamp' in health, "健康检查应该包含时间戳"
        print("✓ 健康检查测试通过")
    
    asyncio.run(run_health_check())


if __name__ == "__main__":
    print("开始数据同步服务测试...")
    
    try:
        test_data_sync_service_basic()
        test_sync_health_check()
        print("\n🎉 所有测试通过！数据同步机制实现成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)