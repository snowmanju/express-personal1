"""
理货单管理服务集成测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.cargo_manifest import CargoManifest
from app.services.manifest_service import ManifestService


def test_manifest_service_integration():
    """测试理货单服务集成功能"""
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建服务实例
        service = ManifestService(db=db)
        
        # 测试数据
        test_data = {
            'tracking_number': 'INTEGRATION_TEST_001',
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001',
            'package_number': 'PKG001',
            'weight': '1.5',
            'length': '10.0',
            'width': '8.0',
            'height': '5.0',
            'special_fee': '15.50'
        }
        
        # 清理可能存在的测试数据
        existing = db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'INTEGRATION_TEST_001'
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # 测试创建理货单
        create_result = service.create_manifest(test_data)
        assert create_result['success'] is True, f"创建失败: {create_result.get('errors', [])}"
        
        manifest_id = create_result['data']['id']
        
        # 测试根据ID获取理货单
        get_result = service.get_manifest_by_id(manifest_id)
        assert get_result['success'] is True
        assert get_result['data']['tracking_number'] == 'INTEGRATION_TEST_001'
        
        # 测试根据快递单号获取理货单
        get_by_tracking_result = service.get_manifest_by_tracking_number('INTEGRATION_TEST_001')
        assert get_by_tracking_result['success'] is True
        assert get_by_tracking_result['data']['tracking_number'] == 'INTEGRATION_TEST_001'
        
        # 测试搜索理货单
        search_result = service.search_manifests(search_query='INTEGRATION_TEST')
        assert search_result['success'] is True
        assert len(search_result['data']) >= 1
        
        # 测试更新理货单
        update_data = test_data.copy()
        update_data['transport_code'] = 'T002'
        update_result = service.update_manifest(manifest_id, update_data)
        assert update_result['success'] is True
        
        # 验证更新结果
        updated_manifest = service.get_manifest_by_id(manifest_id)
        assert updated_manifest['data']['transport_code'] == 'T002'
        
        # 测试删除理货单
        delete_result = service.delete_manifest(manifest_id, operator='test_user')
        assert delete_result['success'] is True
        
        # 验证已删除
        deleted_manifest = service.get_manifest_by_id(manifest_id)
        assert deleted_manifest['success'] is False
        
        print("✓ 理货单管理服务集成测试通过")
        
    except Exception as e:
        print(f"✗ 理货单管理服务集成测试失败: {str(e)}")
        raise
    finally:
        # 清理测试数据
        try:
            existing = db.query(CargoManifest).filter(
                CargoManifest.tracking_number == 'INTEGRATION_TEST_001'
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
        except:
            pass
        db.close()


if __name__ == '__main__':
    test_manifest_service_integration()