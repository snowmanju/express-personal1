#!/usr/bin/env python3
"""
查询结果完整性属性测试
Query Result Completeness Property Tests

**Feature: express-tracking-website, Property 3: 查询结果完整性**
**验证需求: Requirements 1.6, 5.4**
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
import tempfile
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

from hypothesis import given, strategies as st, settings, assume, HealthCheck
import pytest

# 导入SQLAlchemy组件
from sqlalchemy import create_engine, Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# 导入被测试的服务
from app.services.intelligent_query_service import IntelligentQueryService
from app.models.cargo_manifest import CargoManifest


# 创建测试专用的Base和模型
TestBase = declarative_base()

class TestCargoManifest(TestBase):
    """
    测试用理货单模型 - 简化版本，适配SQLite
    """
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
    created_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __repr__(self):
        return f"<TestCargoManifest(id={self.id}, tracking_number='{self.tracking_number}', package_number='{self.package_number}')>"


def create_test_db_session() -> Tuple[Session, str]:
    """创建测试数据库会话"""
    # 创建临时SQLite数据库
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # 创建引擎和会话
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    TestBase.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    return session, db_path


# Hypothesis策略定义
@st.composite
def tracking_number_strategy(draw):
    """生成快递单号的策略"""
    prefix = draw(st.text(
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        min_size=2, max_size=5
    ))
    suffix = draw(st.text(
        alphabet='0123456789',
        min_size=5, max_size=15
    ))
    middle = draw(st.text(
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        min_size=0, max_size=10
    ))
    return f"{prefix}{middle}{suffix}"


@st.composite
def package_number_strategy(draw):
    """生成集包单号的策略"""
    prefix = draw(st.text(
        alphabet='PACKAGE',
        min_size=3, max_size=3
    ))
    suffix = draw(st.text(
        alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        min_size=5, max_size=20
    ))
    return f"{prefix}{suffix}"


@st.composite
def manifest_strategy(draw):
    """生成理货单数据策略"""
    has_package = draw(st.booleans())
    return {
        'tracking_number': draw(tracking_number_strategy()),
        'manifest_date': draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31))),
        'transport_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'customer_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'goods_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'package_number': draw(package_number_strategy()) if has_package else None,
        'weight': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2))),
        'length': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'width': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'height': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'special_fee': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2)))
    }


@st.composite
def successful_api_response_strategy(draw):
    """生成成功的快递100 API响应策略"""
    return {
        'success': True,
        'company_code': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=2, max_size=10)),
        'company_name': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=2, max_size=20)),
        'status': draw(st.sampled_from(['在途', '派件中', '已签收', '异常', '疑难', '待取件', '运输中'])),
        'tracks': draw(st.lists(
            st.fixed_dictionaries({
                'time': st.text(alphabet='0123456789-: ', min_size=10, max_size=20),
                'location': st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=2, max_size=20),
                'description': st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=5, max_size=50)
            }),
            min_size=1, max_size=10
        )),
        'query_time': draw(st.text(alphabet='0123456789-: ', min_size=10, max_size=30))
    }


@st.composite
def failed_api_response_strategy(draw):
    """生成失败的快递100 API响应策略"""
    return {
        'success': False,
        'error': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=5, max_size=20)),
        'query_time': draw(st.text(alphabet='0123456789-: ', min_size=10, max_size=20))
    }


class TestQueryResultCompleteness:
    """查询结果完整性属性测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.session, self.db_path = create_test_db_session()
        
        # 清空数据库以确保测试隔离
        try:
            self.session.query(TestCargoManifest).delete()
            self.session.commit()
        except Exception:
            self.session.rollback()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        try:
            # 清空数据库
            self.session.query(TestCargoManifest).delete()
            self.session.commit()
        except Exception:
            self.session.rollback()
        
        try:
            self.session.close()
        except Exception:
            pass
        
        # 尝试删除临时数据库文件
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except (PermissionError, FileNotFoundError):
            # Windows上可能出现文件被占用的情况，忽略这个错误
            pass
    
    def _create_manifest_record(self, manifest_data: Dict[str, Any]) -> TestCargoManifest:
        """创建理货单记录"""
        try:
            # 检查是否已存在相同的tracking_number
            existing = self.session.query(TestCargoManifest).filter(
                TestCargoManifest.tracking_number == manifest_data['tracking_number']
            ).first()
            
            if existing:
                # 如果已存在，先删除
                self.session.delete(existing)
                self.session.flush()
            
            manifest = TestCargoManifest(
                tracking_number=manifest_data['tracking_number'],
                manifest_date=manifest_data['manifest_date'],
                transport_code=manifest_data['transport_code'],
                customer_code=manifest_data['customer_code'],
                goods_code=manifest_data['goods_code'],
                package_number=manifest_data.get('package_number'),
                weight=manifest_data.get('weight'),
                length=manifest_data.get('length'),
                width=manifest_data.get('width'),
                height=manifest_data.get('height'),
                special_fee=manifest_data.get('special_fee')
            )
            self.session.add(manifest)
            self.session.commit()
            return manifest
        except Exception as e:
            self.session.rollback()
            raise e
    
    @given(st.one_of(manifest_strategy(), tracking_number_strategy()), successful_api_response_strategy())
    @settings(max_examples=3, deadline=None)
    def test_successful_query_result_contains_required_fields(self, query_input, api_response):
        """
        **Feature: express-tracking-website, Property 3: 查询结果完整性**
        
        属性: 对于任何成功的快递查询，返回的结果应该包含快递状态、物流轨迹列表、
        查询类型标识和原始单号信息
        
        验证需求: Requirements 1.6 - 当快递信息成功获取时，快递查询系统应以清晰易读的格式
        展示快递状态、物流轨迹和相关详情
        """
        # 处理输入数据
        if isinstance(query_input, dict):
            # 如果是理货单数据，创建记录并使用其快递单号
            manifest_data = query_input
            self._create_manifest_record(manifest_data)
            tracking_number = manifest_data['tracking_number']
        else:
            # 如果是快递单号字符串，直接使用
            tracking_number = query_input
        
        # 模拟快递100 API客户端返回成功响应
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行查询
            result = asyncio.run(service.query_tracking(tracking_number))
            
            # 验证查询结果的基本结构完整性
            assert isinstance(result, dict), "查询结果应该是字典类型"
            
            # 验证必需的顶级字段存在
            required_top_level_fields = [
                'success', 'original_tracking_number', 'query_tracking_number',
                'query_type', 'has_package_association', 'manifest_info',
                'tracking_info', 'error', 'query_time'
            ]
            
            for field in required_top_level_fields:
                assert field in result, f"查询结果应该包含字段: {field}"
            
            # 验证成功查询的特定要求
            if result['success']:
                # 验证原始单号信息 (Requirements 1.6)
                assert result['original_tracking_number'] == tracking_number, \
                    f"应该包含原始快递单号信息: {result['original_tracking_number']} != {tracking_number}"
                
                # 验证查询类型标识 (Requirements 1.6)
                assert result['query_type'] in ['package', 'original'], \
                    f"应该包含有效的查询类型标识: {result['query_type']}"
                
                # 验证快递状态和物流轨迹信息 (Requirements 1.6, 5.4)
                assert result['tracking_info'] is not None, "成功查询应该包含快递信息"
                
                tracking_info = result['tracking_info']
                
                # 验证快递状态信息
                assert 'status' in tracking_info, "快递信息应该包含状态字段"
                assert tracking_info['status'] is not None, "快递状态不应该为空"
                assert isinstance(tracking_info['status'], str), "快递状态应该是字符串类型"
                
                # 验证物流轨迹列表 (Requirements 5.4 - 结构化方式展示物流轨迹信息)
                assert 'tracks' in tracking_info, "快递信息应该包含物流轨迹字段"
                assert isinstance(tracking_info['tracks'], list), "物流轨迹应该是列表类型"
                assert len(tracking_info['tracks']) > 0, "成功查询应该包含至少一条物流轨迹"
                
                # 验证每条物流轨迹的结构完整性
                for i, track in enumerate(tracking_info['tracks']):
                    assert isinstance(track, dict), f"第{i+1}条物流轨迹应该是字典类型"
                    
                    # 验证轨迹记录的必需字段
                    track_required_fields = ['time', 'location', 'description']
                    for field in track_required_fields:
                        assert field in track, f"第{i+1}条物流轨迹应该包含字段: {field}"
                        assert track[field] is not None, f"第{i+1}条物流轨迹的{field}字段不应该为空"
                        assert isinstance(track[field], str), f"第{i+1}条物流轨迹的{field}字段应该是字符串类型"
                
                # 验证快递公司信息
                assert 'company_code' in tracking_info, "快递信息应该包含快递公司编码"
                assert 'company_name' in tracking_info, "快递信息应该包含快递公司名称"
                
                # 验证查询时间信息
                assert result['query_time'] is not None, "成功查询应该包含查询时间"
                
                # 验证错误字段在成功时为空
                assert result['error'] is None, "成功查询时错误字段应该为空"
            
            # 验证查询策略相关字段的一致性
            assert isinstance(result['has_package_association'], bool), \
                "集包单号关联标识应该是布尔类型"
            
            # 如果有理货单关联，验证理货单信息的完整性
            if result['has_package_association']:
                assert result['manifest_info'] is not None, "有理货单关联时应该包含理货单信息"
                manifest_info = result['manifest_info']
                
                # 验证理货单信息的必需字段
                manifest_required_fields = [
                    'id', 'tracking_number', 'package_number', 'manifest_date',
                    'transport_code', 'customer_code', 'goods_code'
                ]
                
                for field in manifest_required_fields:
                    assert field in manifest_info, f"理货单信息应该包含字段: {field}"
                
                assert manifest_info['tracking_number'] == tracking_number, \
                    "理货单信息中的快递单号应该与查询单号一致"
    
    @given(st.one_of(manifest_strategy(), tracking_number_strategy()), failed_api_response_strategy())
    @settings(max_examples=2, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
    def test_failed_query_result_contains_required_error_fields(self, query_input, api_response):
        """
        **Feature: express-tracking-website, Property 3: 查询结果完整性**
        
        属性: 对于任何失败的快递查询，返回的结果应该包含错误信息、查询类型标识
        和原始单号信息，同时确保结构完整性
        
        验证需求: Requirements 1.6 - 查询结果应该包含完整的信息结构，即使查询失败
        """
        # 处理输入数据
        if isinstance(query_input, dict):
            # 如果是理货单数据，创建记录并使用其快递单号
            manifest_data = query_input
            self._create_manifest_record(manifest_data)
            tracking_number = manifest_data['tracking_number']
        else:
            # 如果是快递单号字符串，直接使用
            tracking_number = query_input
        
        # 模拟快递100 API客户端返回失败响应
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行查询
            result = asyncio.run(service.query_tracking(tracking_number))
            
            # 验证查询结果的基本结构完整性
            assert isinstance(result, dict), "查询结果应该是字典类型"
            
            # 验证必需的顶级字段存在
            required_top_level_fields = [
                'success', 'original_tracking_number', 'query_tracking_number',
                'query_type', 'has_package_association', 'manifest_info',
                'tracking_info', 'error', 'query_time'
            ]
            
            for field in required_top_level_fields:
                assert field in result, f"查询结果应该包含字段: {field}"
            
            # 验证失败查询的特定要求
            assert result['success'] == False, "失败查询的success字段应该为False"
            
            # 验证原始单号信息仍然存在
            assert result['original_tracking_number'] == tracking_number, \
                f"失败查询仍应该包含原始快递单号信息: {result['original_tracking_number']} != {tracking_number}"
            
            # 验证查询类型标识仍然存在
            assert result['query_type'] in ['package', 'original'], \
                f"失败查询仍应该包含有效的查询类型标识: {result['query_type']}"
            
            # 验证错误信息存在且有意义
            assert result['error'] is not None, "失败查询应该包含错误信息"
            assert isinstance(result['error'], str), "错误信息应该是字符串类型"
            assert len(result['error'].strip()) > 0, "错误信息不应该为空字符串"
            
            # 验证失败时快递信息为空
            assert result['tracking_info'] is None, "失败查询时快递信息应该为空"
            
            # 验证查询策略相关字段仍然有效
            assert isinstance(result['has_package_association'], bool), \
                "集包单号关联标识应该是布尔类型"
    
    @given(st.lists(st.one_of(manifest_strategy(), tracking_number_strategy()), min_size=2, max_size=5))
    @settings(max_examples=10, deadline=None)
    def test_batch_query_result_completeness_consistency(self, query_inputs):
        """
        **Feature: express-tracking-website, Property 3: 查询结果完整性**
        
        属性: 对于任何批量查询，每个查询结果都应该保持相同的结构完整性，
        无论查询成功还是失败
        
        验证需求: Requirements 1.6, 5.4 - 所有查询结果都应该具有一致的结构和完整性
        """
        # 确保查询输入的唯一性
        unique_inputs = []
        seen_tracking_numbers = set()
        
        for query_input in query_inputs:
            if isinstance(query_input, dict):
                tracking_number = query_input['tracking_number']
            else:
                tracking_number = query_input
            
            if tracking_number not in seen_tracking_numbers:
                unique_inputs.append(query_input)
                seen_tracking_numbers.add(tracking_number)
        
        assume(len(unique_inputs) >= 2)
        
        # 创建理货单记录
        tracking_numbers = []
        for query_input in unique_inputs:
            if isinstance(query_input, dict):
                manifest_data = query_input
                self._create_manifest_record(manifest_data)
                tracking_numbers.append(manifest_data['tracking_number'])
            else:
                tracking_numbers.append(query_input)
        
        # 模拟混合的API响应（成功和失败）
        api_responses = []
        for i, _ in enumerate(tracking_numbers):
            if i % 2 == 0:
                # 偶数索引返回成功响应
                api_responses.append({
                    'success': True,
                    'company_code': f'test_company_{i}',
                    'company_name': f'Test Company {i}',
                    'status': '在途',
                    'tracks': [
                        {
                            'time': f'2024-01-{i+1:02d} 10:00:00',
                            'location': f'Test Location {i}',
                            'description': f'Test Description {i}'
                        }
                    ],
                    'query_time': f'2024-01-{i+1:02d} 10:00:00'
                })
            else:
                # 奇数索引返回失败响应
                api_responses.append({
                    'success': False,
                    'error': f'Test Error {i}',
                    'query_time': f'2024-01-{i+1:02d} 10:00:00'
                })
        
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            
            # 设置API客户端的副作用，根据调用次数返回不同响应
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                response = api_responses[call_count % len(api_responses)]
                call_count += 1
                return response
            
            mock_client.query_tracking.side_effect = side_effect
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行所有查询
            results = []
            for tracking_number in tracking_numbers:
                result = asyncio.run(service.query_tracking(tracking_number))
                results.append(result)
            
            # 验证所有结果的结构一致性
            required_fields = [
                'success', 'original_tracking_number', 'query_tracking_number',
                'query_type', 'has_package_association', 'manifest_info',
                'tracking_info', 'error', 'query_time'
            ]
            
            for i, result in enumerate(results):
                # 验证每个结果都有相同的字段结构
                for field in required_fields:
                    assert field in result, f"第{i+1}个查询结果应该包含字段: {field}"
                
                # 验证原始单号正确
                assert result['original_tracking_number'] == tracking_numbers[i], \
                    f"第{i+1}个查询结果的原始单号应该正确"
                
                # 验证查询类型有效
                assert result['query_type'] in ['package', 'original'], \
                    f"第{i+1}个查询结果的查询类型应该有效"
                
                # 验证成功和失败结果的特定字段
                if result['success']:
                    assert result['tracking_info'] is not None, f"第{i+1}个成功查询应该包含快递信息"
                    assert result['error'] is None, f"第{i+1}个成功查询的错误字段应该为空"
                    
                    # 验证快递信息的完整性
                    tracking_info = result['tracking_info']
                    assert 'status' in tracking_info, f"第{i+1}个查询结果的快递信息应该包含状态"
                    assert 'tracks' in tracking_info, f"第{i+1}个查询结果的快递信息应该包含轨迹"
                    assert isinstance(tracking_info['tracks'], list), f"第{i+1}个查询结果的轨迹应该是列表"
                    assert len(tracking_info['tracks']) > 0, f"第{i+1}个查询结果应该包含轨迹记录"
                else:
                    assert result['tracking_info'] is None, f"第{i+1}个失败查询的快递信息应该为空"
                    assert result['error'] is not None, f"第{i+1}个失败查询应该包含错误信息"
                    assert isinstance(result['error'], str), f"第{i+1}个失败查询的错误信息应该是字符串"


def main():
    """运行属性测试"""
    print("=" * 60)
    print("查询结果完整性属性测试")
    print("Query Result Completeness Property Tests")
    print("=" * 60)
    
    # 运行测试
    import pytest
    
    # 运行特定的测试类
    exit_code = pytest.main([
        __file__ + "::TestQueryResultCompleteness",
        "-v",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n🎉 所有属性测试通过!")
        print("✅ 查询结果完整性属性验证成功")
        print("\n📝 验证的属性:")
        print("- 成功查询结果包含所有必需字段")
        print("- 失败查询结果包含错误信息和基本结构")
        print("- 批量查询结果保持结构一致性")
        print("- 快递状态和物流轨迹信息完整性")
        print("- 查询类型标识和原始单号信息")
    else:
        print("\n❌ 部分属性测试失败")
    
    return exit_code == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)