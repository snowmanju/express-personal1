"""
理货单管理服务基础测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from app.services.manifest_service import ManifestService


class TestManifestServiceBasic:
    """理货单服务基础测试类"""
    
    def test_validate_manifest_data_success(self):
        """测试数据验证成功"""
        service = ManifestService()
        
        valid_data = {
            'tracking_number': 'TEST123456789',
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
        
        errors = service.validate_manifest_data(valid_data)
        assert len(errors) == 0
    
    def test_validate_manifest_data_missing_required(self):
        """测试数据验证缺少必需字段"""
        service = ManifestService()
        
        incomplete_data = {
            'tracking_number': 'TEST123'
            # 缺少其他必需字段
        }
        
        errors = service.validate_manifest_data(incomplete_data)
        assert len(errors) > 0
        assert any('不能为空' in error for error in errors)
    
    def test_validate_manifest_data_invalid_tracking_number(self):
        """测试快递单号格式验证"""
        service = ManifestService()
        
        invalid_data = {
            'tracking_number': 'TEST@123',  # 包含非法字符
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001'
        }
        
        errors = service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('只能包含字母和数字' in error for error in errors)
    
    def test_validate_manifest_data_invalid_date(self):
        """测试日期格式验证"""
        service = ManifestService()
        
        invalid_data = {
            'tracking_number': 'TEST123',
            'manifest_date': 'invalid-date',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001'
        }
        
        errors = service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('日期格式不正确' in error for error in errors)
    
    def test_validate_manifest_data_invalid_number(self):
        """测试数值格式验证"""
        service = ManifestService()
        
        invalid_data = {
            'tracking_number': 'TEST123',
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001',
            'weight': 'invalid_number'
        }
        
        errors = service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('必须是有效数字' in error for error in errors)
    
    def test_validate_manifest_data_field_length(self):
        """测试字段长度验证"""
        service = ManifestService()
        
        invalid_data = {
            'tracking_number': 'A' * 51,  # 超过50字符限制
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001'
        }
        
        errors = service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('长度不能超过' in error for error in errors)
    
    def test_validate_manifest_data_numeric_range(self):
        """测试数值范围验证"""
        service = ManifestService()
        
        invalid_data = {
            'tracking_number': 'TEST123',
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001',
            'weight': '-1.0'  # 负数
        }
        
        errors = service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('不能小于' in error for error in errors)
    
    def test_service_initialization_without_db(self):
        """测试服务初始化（无数据库）"""
        service = ManifestService()
        assert service.db is None
    
    def test_service_initialization_with_db(self):
        """测试服务初始化（有数据库）"""
        # 模拟数据库会话
        mock_db = "mock_session"
        service = ManifestService(db=mock_db)
        assert service.db == mock_db
    
    def test_search_manifests_without_db_raises_error(self):
        """测试无数据库会话时搜索抛出错误"""
        service = ManifestService()
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.search_manifests()
    
    def test_get_manifest_by_id_without_db_raises_error(self):
        """测试无数据库会话时根据ID获取抛出错误"""
        service = ManifestService()
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.get_manifest_by_id(1)
    
    def test_create_manifest_without_db_raises_error(self):
        """测试无数据库会话时创建抛出错误"""
        service = ManifestService()
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.create_manifest({})
    
    def test_update_manifest_without_db_raises_error(self):
        """测试无数据库会话时更新抛出错误"""
        service = ManifestService()
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.update_manifest(1, {})
    
    def test_delete_manifest_without_db_raises_error(self):
        """测试无数据库会话时删除抛出错误"""
        service = ManifestService()
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.delete_manifest(1)


if __name__ == '__main__':
    pytest.main([__file__])