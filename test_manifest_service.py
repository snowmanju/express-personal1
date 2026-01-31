"""
理货单管理服务测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine, Integer, String, Date, DECIMAL, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column
from app.services.manifest_service import ManifestService

# 创建测试专用的Base和模型
TestBase = declarative_base()

class TestCargoManifest(TestBase):
    """测试用理货单模型"""
    __tablename__ = "cargo_manifest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_number = Column(String(50), nullable=False, unique=True)
    manifest_date = Column(Date, nullable=False)
    transport_code = Column(String(20), nullable=False)
    customer_code = Column(String(20), nullable=False)
    goods_code = Column(String(20), nullable=False)
    package_number = Column(String(50), nullable=True)
    weight = Column(DECIMAL(10, 3), nullable=True)
    length = Column(DECIMAL(8, 2), nullable=True)
    width = Column(DECIMAL(8, 2), nullable=True)
    height = Column(DECIMAL(8, 2), nullable=True)
    special_fee = Column(DECIMAL(10, 2), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # 替换原始模型
    import app.models.cargo_manifest
    original_model = app.models.cargo_manifest.CargoManifest
    app.models.cargo_manifest.CargoManifest = TestCargoManifest
    
    yield session
    
    # 恢复原始模型
    app.models.cargo_manifest.CargoManifest = original_model
    session.close()


@pytest.fixture
def manifest_service(db_session):
    """创建理货单服务实例"""
    return ManifestService(db=db_session)


@pytest.fixture
def sample_manifest_data():
    """示例理货单数据"""
    return {
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


class TestManifestService:
    """理货单服务测试类"""
    
    def test_create_manifest_success(self, manifest_service, sample_manifest_data):
        """测试成功创建理货单"""
        result = manifest_service.create_manifest(sample_manifest_data)
        
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['tracking_number'] == 'TEST123456789'
        assert 'message' in result
    
    def test_create_manifest_duplicate_tracking_number(self, manifest_service, sample_manifest_data):
        """测试创建重复快递单号的理货单"""
        # 先创建一个理货单
        manifest_service.create_manifest(sample_manifest_data)
        
        # 尝试创建相同快递单号的理货单
        result = manifest_service.create_manifest(sample_manifest_data)
        
        assert result['success'] is False
        assert '快递单号已存在' in result['errors']
    
    def test_create_manifest_missing_required_fields(self, manifest_service):
        """测试缺少必需字段时创建理货单"""
        incomplete_data = {
            'tracking_number': 'TEST123',
            # 缺少其他必需字段
        }
        
        result = manifest_service.create_manifest(incomplete_data)
        
        assert result['success'] is False
        assert len(result['errors']) > 0
    
    def test_get_manifest_by_id_success(self, manifest_service, sample_manifest_data):
        """测试根据ID获取理货单成功"""
        # 先创建理货单
        create_result = manifest_service.create_manifest(sample_manifest_data)
        manifest_id = create_result['data']['id']
        
        # 获取理货单
        result = manifest_service.get_manifest_by_id(manifest_id)
        
        assert result['success'] is True
        assert result['data']['tracking_number'] == 'TEST123456789'
        assert result['data']['transport_code'] == 'T001'
    
    def test_get_manifest_by_id_not_found(self, manifest_service):
        """测试获取不存在的理货单"""
        result = manifest_service.get_manifest_by_id(99999)
        
        assert result['success'] is False
        assert '理货单不存在' in result['error']
    
    def test_get_manifest_by_tracking_number_success(self, manifest_service, sample_manifest_data):
        """测试根据快递单号获取理货单成功"""
        # 先创建理货单
        manifest_service.create_manifest(sample_manifest_data)
        
        # 根据快递单号获取
        result = manifest_service.get_manifest_by_tracking_number('TEST123456789')
        
        assert result['success'] is True
        assert result['data']['tracking_number'] == 'TEST123456789'
    
    def test_get_manifest_by_tracking_number_not_found(self, manifest_service):
        """测试获取不存在的快递单号"""
        result = manifest_service.get_manifest_by_tracking_number('NOTEXIST')
        
        assert result['success'] is False
        assert '未找到对应的理货单' in result['error']
    
    def test_update_manifest_success(self, manifest_service, sample_manifest_data):
        """测试成功更新理货单"""
        # 先创建理货单
        create_result = manifest_service.create_manifest(sample_manifest_data)
        manifest_id = create_result['data']['id']
        
        # 更新数据
        update_data = sample_manifest_data.copy()
        update_data['transport_code'] = 'T002'
        update_data['weight'] = '2.0'
        
        result = manifest_service.update_manifest(manifest_id, update_data)
        
        assert result['success'] is True
        
        # 验证更新结果
        get_result = manifest_service.get_manifest_by_id(manifest_id)
        assert get_result['data']['transport_code'] == 'T002'
        assert get_result['data']['weight'] == 2.0
    
    def test_update_manifest_not_found(self, manifest_service, sample_manifest_data):
        """测试更新不存在的理货单"""
        result = manifest_service.update_manifest(99999, sample_manifest_data)
        
        assert result['success'] is False
        assert '理货单不存在' in result['errors']
    
    def test_delete_manifest_success(self, manifest_service, sample_manifest_data):
        """测试成功删除理货单"""
        # 先创建理货单
        create_result = manifest_service.create_manifest(sample_manifest_data)
        manifest_id = create_result['data']['id']
        
        # 删除理货单
        result = manifest_service.delete_manifest(manifest_id, operator='test_user')
        
        assert result['success'] is True
        assert result['data']['tracking_number'] == 'TEST123456789'
        
        # 验证已删除
        get_result = manifest_service.get_manifest_by_id(manifest_id)
        assert get_result['success'] is False
    
    def test_delete_manifest_not_found(self, manifest_service):
        """测试删除不存在的理货单"""
        result = manifest_service.delete_manifest(99999)
        
        assert result['success'] is False
        assert '理货单不存在' in result['error']
    
    def test_search_manifests_no_query(self, manifest_service, sample_manifest_data):
        """测试无搜索条件的理货单搜索"""
        # 创建几个理货单
        for i in range(3):
            data = sample_manifest_data.copy()
            data['tracking_number'] = f'TEST{i:06d}'
            manifest_service.create_manifest(data)
        
        # 搜索所有记录
        result = manifest_service.search_manifests()
        
        assert result['success'] is True
        assert len(result['data']) == 3
        assert result['pagination']['total_count'] == 3
    
    def test_search_manifests_with_query(self, manifest_service, sample_manifest_data):
        """测试带搜索条件的理货单搜索"""
        # 创建理货单
        manifest_service.create_manifest(sample_manifest_data)
        
        # 搜索特定快递单号
        result = manifest_service.search_manifests(search_query='TEST123')
        
        assert result['success'] is True
        assert len(result['data']) == 1
        assert result['data'][0]['tracking_number'] == 'TEST123456789'
    
    def test_search_manifests_pagination(self, manifest_service, sample_manifest_data):
        """测试理货单搜索分页"""
        # 创建多个理货单
        for i in range(5):
            data = sample_manifest_data.copy()
            data['tracking_number'] = f'TEST{i:06d}'
            manifest_service.create_manifest(data)
        
        # 测试分页
        result = manifest_service.search_manifests(page=1, limit=2)
        
        assert result['success'] is True
        assert len(result['data']) == 2
        assert result['pagination']['total_count'] == 5
        assert result['pagination']['total_pages'] == 3
        assert result['pagination']['has_next'] is True
    
    def test_batch_delete_manifests_success(self, manifest_service, sample_manifest_data):
        """测试批量删除理货单成功"""
        # 创建多个理货单
        manifest_ids = []
        for i in range(3):
            data = sample_manifest_data.copy()
            data['tracking_number'] = f'TEST{i:06d}'
            create_result = manifest_service.create_manifest(data)
            manifest_ids.append(create_result['data']['id'])
        
        # 批量删除
        result = manifest_service.batch_delete_manifests(manifest_ids, operator='test_user')
        
        assert result['success'] is True
        assert result['data']['deleted_count'] == 3
        
        # 验证已删除
        search_result = manifest_service.search_manifests()
        assert search_result['pagination']['total_count'] == 0
    
    def test_get_statistics(self, manifest_service, sample_manifest_data):
        """测试获取统计信息"""
        # 创建理货单（有集包单号）
        manifest_service.create_manifest(sample_manifest_data)
        
        # 创建理货单（无集包单号）
        data_no_package = sample_manifest_data.copy()
        data_no_package['tracking_number'] = 'TEST000001'
        data_no_package['package_number'] = None
        manifest_service.create_manifest(data_no_package)
        
        # 获取统计信息
        result = manifest_service.get_statistics()
        
        assert result['success'] is True
        assert result['data']['total_count'] == 2
        assert result['data']['with_package_count'] == 1
        assert result['data']['without_package_count'] == 1
        assert result['data']['package_rate'] == 50.0
    
    def test_validate_manifest_data_success(self, manifest_service, sample_manifest_data):
        """测试数据验证成功"""
        errors = manifest_service.validate_manifest_data(sample_manifest_data)
        assert len(errors) == 0
    
    def test_validate_manifest_data_missing_required(self, manifest_service):
        """测试数据验证缺少必需字段"""
        incomplete_data = {
            'tracking_number': 'TEST123'
            # 缺少其他必需字段
        }
        
        errors = manifest_service.validate_manifest_data(incomplete_data)
        assert len(errors) > 0
        assert any('不能为空' in error for error in errors)
    
    def test_validate_manifest_data_invalid_format(self, manifest_service):
        """测试数据验证格式错误"""
        invalid_data = {
            'tracking_number': 'TEST@123',  # 包含非法字符
            'manifest_date': '2024-01-15',
            'transport_code': 'T001',
            'customer_code': 'C001',
            'goods_code': 'G001',
            'weight': 'invalid_number'  # 无效数字
        }
        
        errors = manifest_service.validate_manifest_data(invalid_data)
        assert len(errors) > 0
        assert any('只能包含字母和数字' in error for error in errors)
        assert any('必须是有效数字' in error for error in errors)


if __name__ == '__main__':
    pytest.main([__file__])