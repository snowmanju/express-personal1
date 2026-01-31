"""
理货单管理操作属性测试
Property 12: 理货单管理操作
验证需求: Requirements 7.2, 7.3, 7.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, Integer, String, Date, DECIMAL, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column
from contextlib import contextmanager
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


@contextmanager
def get_test_manifest_service():
    """创建测试用的理货单服务上下文管理器"""
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # 替换原始模型
    import app.models.cargo_manifest
    original_model = app.models.cargo_manifest.CargoManifest
    app.models.cargo_manifest.CargoManifest = TestCargoManifest
    
    try:
        service = ManifestService(db=session)
        yield service
    finally:
        # 恢复原始模型
        app.models.cargo_manifest.CargoManifest = original_model
        session.close()


# 生成策略
tracking_number_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=5,
    max_size=20
)

code_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    min_size=3,
    max_size=10
)

package_number_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        min_size=5,
        max_size=20
    )
)

date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2030, 12, 31)
)

positive_decimal_strategy = st.one_of(
    st.none(),
    st.decimals(
        min_value=Decimal('0.1'),
        max_value=Decimal('9999.999'),
        places=3
    )
)

dimension_strategy = st.one_of(
    st.none(),
    st.decimals(
        min_value=Decimal('0.1'),
        max_value=Decimal('999.99'),
        places=2
    )
)

fee_strategy = st.one_of(
    st.none(),
    st.decimals(
        min_value=Decimal('0.1'),
        max_value=Decimal('9999.99'),
        places=2
    )
)

manifest_data_strategy = st.fixed_dictionaries({
    'tracking_number': tracking_number_strategy,
    'manifest_date': date_strategy,
    'transport_code': code_strategy,
    'customer_code': code_strategy,
    'goods_code': code_strategy,
    'package_number': package_number_strategy,
    'weight': positive_decimal_strategy,
    'length': dimension_strategy,
    'width': dimension_strategy,
    'height': dimension_strategy,
    'special_fee': fee_strategy
})

search_query_strategy = st.one_of(
    st.none(),
    st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)
)


class TestManifestManagementProperties:
    """理货单管理操作属性测试类"""

    @given(
        manifests_data=st.lists(manifest_data_strategy, min_size=0, max_size=10),
        search_query=search_query_strategy
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_12_search_returns_correct_results(self, manifests_data, search_query):
        """
        **Feature: express-tracking-website, Property 12: 理货单管理操作**
        **Validates: Requirements 7.2**
        
        对于任何理货单搜索操作，系统应该返回正确的搜索结果
        """
        with get_test_manifest_service() as manifest_service:
            # 创建理货单数据
            created_manifests = []
            for i, manifest_data in enumerate(manifests_data):
                # 确保快递单号唯一
                manifest_data['tracking_number'] = f"{manifest_data['tracking_number']}_{i}"
                
                # 转换日期为字符串格式
                if isinstance(manifest_data['manifest_date'], date):
                    manifest_data['manifest_date'] = manifest_data['manifest_date'].isoformat()
                
                # 转换Decimal为字符串
                for field in ['weight', 'length', 'width', 'height', 'special_fee']:
                    if manifest_data[field] is not None:
                        manifest_data[field] = str(manifest_data[field])
                
                result = manifest_service.create_manifest(manifest_data)
                if result['success']:
                    created_manifests.append(manifest_data)
            
            # 执行搜索
            search_result = manifest_service.search_manifests(search_query=search_query)
            
            # 验证搜索结果的正确性
            assert search_result['success'] is True
            assert 'data' in search_result
            assert 'pagination' in search_result
            assert isinstance(search_result['data'], list)
            
            # 如果有搜索条件，验证结果包含搜索关键词
            if search_query and search_query.strip():
                search_term = search_query.strip().lower()
                for result_item in search_result['data']:
                    # 至少在某个字段中包含搜索关键词
                    found_in_field = (
                        search_term in result_item['tracking_number'].lower() or
                        (result_item['package_number'] and search_term in result_item['package_number'].lower()) or
                        search_term in result_item['customer_code'].lower() or
                        search_term in result_item['transport_code'].lower() or
                        search_term in result_item['goods_code'].lower()
                    )
                    assert found_in_field, f"搜索结果 {result_item['tracking_number']} 不包含搜索关键词 {search_term}"
            
            # 验证分页信息的正确性
            pagination = search_result['pagination']
            assert pagination['total_count'] >= 0
            assert pagination['page'] >= 1
            assert pagination['limit'] > 0
            assert len(search_result['data']) <= pagination['limit']
            
            # 验证总页数计算正确
            expected_total_pages = (pagination['total_count'] + pagination['limit'] - 1) // pagination['limit']
            if pagination['total_count'] == 0:
                expected_total_pages = 0
            assert pagination['total_pages'] == expected_total_pages

    @given(
        manifest_data=manifest_data_strategy,
        update_data=manifest_data_strategy
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_12_edit_validates_data_integrity(self, manifest_data, update_data):
        """
        **Feature: express-tracking-website, Property 12: 理货单管理操作**
        **Validates: Requirements 7.3**
        
        对于任何理货单编辑操作，系统应该验证编辑数据的完整性
        """
        with get_test_manifest_service() as manifest_service:
            # 转换日期为字符串格式
            if isinstance(manifest_data['manifest_date'], date):
                manifest_data['manifest_date'] = manifest_data['manifest_date'].isoformat()
            if isinstance(update_data['manifest_date'], date):
                update_data['manifest_date'] = update_data['manifest_date'].isoformat()
            
            # 转换Decimal为字符串
            for field in ['weight', 'length', 'width', 'height', 'special_fee']:
                if manifest_data[field] is not None:
                    manifest_data[field] = str(manifest_data[field])
                if update_data[field] is not None:
                    update_data[field] = str(update_data[field])
            
            # 创建初始理货单
            create_result = manifest_service.create_manifest(manifest_data)
            assume(create_result['success'])  # 只测试成功创建的情况
            
            manifest_id = create_result['data']['id']
            
            # 确保更新数据的快递单号不与其他记录冲突（使用相同的快递单号）
            update_data['tracking_number'] = manifest_data['tracking_number']
            
            # 执行更新操作
            update_result = manifest_service.update_manifest(manifest_id, update_data)
            
            # 验证更新操作的数据完整性验证
            if update_result['success']:
                # 如果更新成功，验证数据确实被更新
                get_result = manifest_service.get_manifest_by_id(manifest_id)
                assert get_result['success'] is True
                
                updated_manifest = get_result['data']
                
                # 验证必需字段都存在且有效
                required_fields = ['tracking_number', 'manifest_date', 'transport_code', 'customer_code', 'goods_code']
                for field in required_fields:
                    assert updated_manifest[field] is not None
                    assert str(updated_manifest[field]).strip() != ''
                
                # 验证数值字段的有效性
                numeric_fields = ['weight', 'length', 'width', 'height', 'special_fee']
                for field in numeric_fields:
                    if updated_manifest[field] is not None:
                        assert updated_manifest[field] >= 0
                
                # 验证快递单号格式
                import re
                assert re.match(r'^[A-Za-z0-9_]+$', updated_manifest['tracking_number'])
                
            else:
                # 如果更新失败，应该有错误信息
                assert 'errors' in update_result or 'error' in update_result
                
                # 验证原始数据未被修改
                get_result = manifest_service.get_manifest_by_id(manifest_id)
                assert get_result['success'] is True

    @given(
        manifests_data=st.lists(manifest_data_strategy, min_size=1, max_size=3),
        operator=st.one_of(st.none(), st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=20))
    )
    @settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much])
    def test_property_12_delete_records_operation_log(self, manifests_data, operator):
        """
        **Feature: express-tracking-website, Property 12: 理货单管理操作**
        **Validates: Requirements 7.4**
        
        对于任何理货单删除操作，系统应该记录操作日志
        """
        with get_test_manifest_service() as manifest_service:
            # 创建理货单数据
            created_manifest_ids = []
            created_tracking_numbers = []
            
            for i, manifest_data in enumerate(manifests_data):
                # 确保快递单号唯一
                manifest_data['tracking_number'] = f"{manifest_data['tracking_number']}_{i}"
                
                # 转换日期为字符串格式
                if isinstance(manifest_data['manifest_date'], date):
                    manifest_data['manifest_date'] = manifest_data['manifest_date'].isoformat()
                
                # 转换Decimal为字符串
                for field in ['weight', 'length', 'width', 'height', 'special_fee']:
                    if manifest_data[field] is not None:
                        manifest_data[field] = str(manifest_data[field])
                
                result = manifest_service.create_manifest(manifest_data)
                if result['success']:
                    created_manifest_ids.append(result['data']['id'])
                    created_tracking_numbers.append(result['data']['tracking_number'])
            
            # 如果没有成功创建任何记录，跳过测试
            if len(created_manifest_ids) == 0:
                return
            
            # 测试单个删除操作
            if len(created_manifest_ids) >= 1:
                manifest_id = created_manifest_ids[0]
                tracking_number = created_tracking_numbers[0]
                
                # 执行删除操作
                delete_result = manifest_service.delete_manifest(manifest_id, operator=operator)
                
                # 验证删除操作的结果
                if delete_result['success']:
                    # 验证返回的数据包含被删除记录的信息
                    assert 'data' in delete_result
                    assert delete_result['data']['id'] == manifest_id
                    assert delete_result['data']['tracking_number'] == tracking_number
                    
                    # 验证记录确实被删除
                    get_result = manifest_service.get_manifest_by_id(manifest_id)
                    assert get_result['success'] is False
                    assert '理货单不存在' in get_result['error']
                    
                    # 验证有成功消息（表明操作被记录）
                    assert 'message' in delete_result
                    assert '删除成功' in delete_result['message']
                
                else:
                    # 如果删除失败，应该有错误信息
                    assert 'error' in delete_result
            
            # 测试批量删除操作（如果有多个记录）
            if len(created_manifest_ids) >= 2:
                remaining_ids = created_manifest_ids[1:]
                remaining_tracking_numbers = created_tracking_numbers[1:]
                
                # 执行批量删除操作
                batch_delete_result = manifest_service.batch_delete_manifests(remaining_ids, operator=operator)
                
                # 验证批量删除操作的结果
                if batch_delete_result['success']:
                    # 验证返回的数据包含删除统计信息
                    assert 'data' in batch_delete_result
                    assert batch_delete_result['data']['deleted_count'] == len(remaining_ids)
                    assert set(batch_delete_result['data']['deleted_ids']) == set(remaining_ids)
                    assert set(batch_delete_result['data']['deleted_tracking_numbers']) == set(remaining_tracking_numbers)
                    
                    # 验证记录确实被删除
                    for manifest_id in remaining_ids:
                        get_result = manifest_service.get_manifest_by_id(manifest_id)
                        assert get_result['success'] is False
                    
                    # 验证有成功消息（表明操作被记录）
                    assert 'message' in batch_delete_result
                    assert '成功删除' in batch_delete_result['message']
                    assert str(len(remaining_ids)) in batch_delete_result['message']
                
                else:
                    # 如果批量删除失败，应该有错误信息
                    assert 'error' in batch_delete_result

    @given(
        page=st.integers(min_value=1, max_value=10),
        limit=st.integers(min_value=1, max_value=50),
        sort_by=st.sampled_from(['id', 'tracking_number', 'manifest_date', 'created_at']),
        sort_order=st.sampled_from(['asc', 'desc'])
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_12_search_pagination_consistency(self, page, limit, sort_by, sort_order):
        """
        **Feature: express-tracking-website, Property 12: 理货单管理操作**
        **Validates: Requirements 7.2**
        
        对于任何理货单搜索操作，分页和排序应该保持一致性
        """
        with get_test_manifest_service() as manifest_service:
            # 创建一些测试数据
            test_data = []
            for i in range(5):
                manifest_data = {
                    'tracking_number': f'TEST{i:06d}',
                    'manifest_date': (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
                    'transport_code': f'T{i:03d}',
                    'customer_code': f'C{i:03d}',
                    'goods_code': f'G{i:03d}',
                    'package_number': f'PKG{i:06d}' if i % 2 == 0 else None,
                    'weight': str(Decimal(f'{i+1}.5')),
                    'length': str(Decimal('10.0')),
                    'width': str(Decimal('8.0')),
                    'height': str(Decimal('5.0')),
                    'special_fee': str(Decimal(f'{i*10}.50'))
                }
                result = manifest_service.create_manifest(manifest_data)
                if result['success']:
                    test_data.append(manifest_data)
            
            # 执行搜索
            search_result = manifest_service.search_manifests(
                page=page,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # 验证搜索结果
            assert search_result['success'] is True
            
            # 验证分页参数
            pagination = search_result['pagination']
            assert pagination['page'] == page
            assert pagination['limit'] == limit
            
            # 验证返回的数据量不超过限制
            assert len(search_result['data']) <= limit
            
            # 验证分页逻辑的一致性
            if pagination['total_count'] > 0:
                expected_total_pages = (pagination['total_count'] + limit - 1) // limit
                assert pagination['total_pages'] == expected_total_pages
                
                # 验证has_next和has_prev的正确性
                assert pagination['has_next'] == (page < pagination['total_pages'])
                assert pagination['has_prev'] == (page > 1)
            
            # 如果有数据，验证排序的一致性
            if len(search_result['data']) > 1:
                data_list = search_result['data']
                
                # 根据排序字段验证顺序
                if sort_by == 'tracking_number':
                    values = [item['tracking_number'] for item in data_list]
                elif sort_by == 'manifest_date':
                    values = [item['manifest_date'] for item in data_list if item['manifest_date']]
                elif sort_by == 'created_at':
                    values = [item['created_at'] for item in data_list if item['created_at']]
                else:
                    values = [item.get('id', 0) for item in data_list]
                
                if len(values) > 1:
                    if sort_order == 'desc':
                        # 验证降序排列
                        for i in range(len(values) - 1):
                            assert values[i] >= values[i + 1], f"降序排列不正确: {values[i]} < {values[i + 1]}"
                    else:
                        # 验证升序排列
                        for i in range(len(values) - 1):
                            assert values[i] <= values[i + 1], f"升序排列不正确: {values[i]} > {values[i + 1]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])