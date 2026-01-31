#!/usr/bin/env python3
"""
智能查询属性测试
Intelligent Query Property Tests

**Feature: express-tracking-website, Property 1: 智能查询决策**
**验证需求: Requirements 1.2, 1.3, 1.4**
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

from hypothesis import given, strategies as st, settings, assume
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
    # 使用更复杂的策略确保唯一性
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
    # 使用不同的前缀确保与tracking_number不同
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
def manifest_with_package_strategy(draw):
    """生成有集包单号的理货单数据策略"""
    return {
        'tracking_number': draw(tracking_number_strategy()),
        'manifest_date': draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31))),
        'transport_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'customer_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'goods_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'package_number': draw(package_number_strategy()),  # 必须有集包单号
        'weight': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2))),
        'length': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'width': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'height': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'special_fee': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2)))
    }


@st.composite
def manifest_without_package_strategy(draw):
    """生成无集包单号的理货单数据策略"""
    return {
        'tracking_number': draw(tracking_number_strategy()),
        'manifest_date': draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31))),
        'transport_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'customer_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'goods_code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)),
        'package_number': None,  # 明确设置为None
        'weight': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2))),
        'length': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'width': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'height': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=999, places=2))),
        'special_fee': draw(st.one_of(st.none(), st.decimals(min_value=0, max_value=9999, places=2)))
    }


@st.composite
def api_response_strategy(draw):
    """生成快递100 API响应的策略"""
    success = draw(st.booleans())
    
    if success:
        return {
            'success': True,
            'company_code': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=2, max_size=10)),
            'company_name': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=2, max_size=20)),
            'status': draw(st.sampled_from(['在途', '派件中', '已签收', '异常', '疑难'])),
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
    else:
        return {
            'success': False,
            'error': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=5, max_size=50)),
            'query_time': draw(st.text(alphabet='0123456789-: ', min_size=10, max_size=30))
        }


class TestIntelligentQueryDecision:
    """智能查询决策属性测试"""
    
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
    
    @given(manifest_with_package_strategy(), api_response_strategy())
    @settings(max_examples=2, deadline=None)
    def test_intelligent_query_uses_package_number_when_exists(self, manifest_data, api_response):
        """
        **Feature: express-tracking-website, Property 1: 智能查询决策**
        
        属性: 对于任何存在集包单号关联的快递单号，系统应该使用集包单号进行查询，
        并在结果中正确标识查询策略为"package"类型
        
        验证需求: Requirements 1.3 - 当快递单号存在集包单号关联时，
        快递查询系统应使用集包单号调用快递100_API并返回集包的快递信息
        """
        # 创建有集包单号的理货单记录
        manifest = self._create_manifest_record(manifest_data)
        
        # 模拟快递100 API客户端
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行查询
            result = asyncio.run(service.query_tracking(manifest_data['tracking_number']))
            
            # 验证查询策略决策
            assert result['original_tracking_number'] == manifest_data['tracking_number'], \
                f"原始单号应该保持不变: {result['original_tracking_number']} != {manifest_data['tracking_number']}"
            
            assert result['query_tracking_number'] == manifest_data['package_number'], \
                f"查询单号应该使用集包单号: {result['query_tracking_number']} != {manifest_data['package_number']}"
            
            assert result['query_type'] == 'package', \
                f"查询类型应该为'package': {result['query_type']}"
            
            assert result['has_package_association'] == True, \
                f"应该标识存在集包单号关联: {result['has_package_association']}"
            
            # 验证API调用使用了正确的单号
            mock_client.query_tracking.assert_called_once()
            call_args = mock_client.query_tracking.call_args
            assert call_args[1]['tracking_number'] == manifest_data['package_number'], \
                f"API调用应该使用集包单号: {call_args[1]['tracking_number']} != {manifest_data['package_number']}"
            
            # 验证理货单信息被正确包含
            assert result['manifest_info'] is not None, "应该包含理货单信息"
            assert result['manifest_info']['tracking_number'] == manifest_data['tracking_number'], \
                "理货单信息中的快递单号应该正确"
            assert result['manifest_info']['package_number'] == manifest_data['package_number'], \
                "理货单信息中的集包单号应该正确"
    
    @given(tracking_number_strategy(), api_response_strategy())
    @settings(max_examples=2, deadline=None)
    def test_intelligent_query_uses_original_number_when_no_package(self, tracking_number, api_response):
        """
        **Feature: express-tracking-website, Property 1: 智能查询决策**
        
        属性: 对于任何不存在集包单号关联的快递单号，系统应该使用原单号进行查询，
        并在结果中正确标识查询策略为"original"类型
        
        验证需求: Requirements 1.4 - 当快递单号不存在集包单号关联时，
        快递查询系统应使用原单号调用快递100_API并返回原单号的快递信息
        """
        # 确保数据库中没有该快递单号的记录
        existing = self.session.query(TestCargoManifest).filter(
            TestCargoManifest.tracking_number == tracking_number
        ).first()
        assume(existing is None)
        
        # 模拟快递100 API客户端
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行查询
            result = asyncio.run(service.query_tracking(tracking_number))
            
            # 验证查询策略决策
            assert result['original_tracking_number'] == tracking_number, \
                f"原始单号应该保持不变: {result['original_tracking_number']} != {tracking_number}"
            
            assert result['query_tracking_number'] == tracking_number, \
                f"查询单号应该使用原单号: {result['query_tracking_number']} != {tracking_number}"
            
            assert result['query_type'] == 'original', \
                f"查询类型应该为'original': {result['query_type']}"
            
            assert result['has_package_association'] == False, \
                f"应该标识不存在集包单号关联: {result['has_package_association']}"
            
            # 验证API调用使用了正确的单号
            mock_client.query_tracking.assert_called_once()
            call_args = mock_client.query_tracking.call_args
            assert call_args[1]['tracking_number'] == tracking_number, \
                f"API调用应该使用原单号: {call_args[1]['tracking_number']} != {tracking_number}"
            
            # 验证理货单信息为空
            assert result['manifest_info'] is None, "理货单信息应该为空"
    
    @given(manifest_without_package_strategy(), api_response_strategy())
    @settings(max_examples=2, deadline=None)
    def test_intelligent_query_uses_original_when_package_is_none(self, manifest_data, api_response):
        """
        **Feature: express-tracking-website, Property 1: 智能查询决策**
        
        属性: 对于任何存在理货单记录但集包单号为空的快递单号，系统应该使用原单号进行查询，
        并在结果中正确标识查询策略为"original"类型
        
        验证需求: Requirements 1.2, 1.4 - 系统应该首先检查该单号是否存在关联的集包单号，
        当不存在时使用原单号查询
        """
        # 创建无集包单号的理货单记录
        manifest = self._create_manifest_record(manifest_data)
        
        # 模拟快递100 API客户端
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 执行查询
            result = asyncio.run(service.query_tracking(manifest_data['tracking_number']))
            
            # 验证查询策略决策
            assert result['original_tracking_number'] == manifest_data['tracking_number'], \
                f"原始单号应该保持不变: {result['original_tracking_number']} != {manifest_data['tracking_number']}"
            
            assert result['query_tracking_number'] == manifest_data['tracking_number'], \
                f"查询单号应该使用原单号: {result['query_tracking_number']} != {manifest_data['tracking_number']}"
            
            assert result['query_type'] == 'original', \
                f"查询类型应该为'original': {result['query_type']}"
            
            assert result['has_package_association'] == False, \
                f"应该标识不存在集包单号关联: {result['has_package_association']}"
            
            # 验证API调用使用了正确的单号
            mock_client.query_tracking.assert_called_once()
            call_args = mock_client.query_tracking.call_args
            assert call_args[1]['tracking_number'] == manifest_data['tracking_number'], \
                f"API调用应该使用原单号: {call_args[1]['tracking_number']} != {manifest_data['tracking_number']}"
            
            # 验证理货单信息被正确包含（即使没有集包单号）
            assert result['manifest_info'] is not None, "应该包含理货单信息"
            assert result['manifest_info']['tracking_number'] == manifest_data['tracking_number'], \
                "理货单信息中的快递单号应该正确"
            assert result['manifest_info']['package_number'] is None, \
                "理货单信息中的集包单号应该为空"
    
    @given(
        st.lists(manifest_with_package_strategy(), min_size=1, max_size=3),
        st.lists(tracking_number_strategy(), min_size=1, max_size=3),
        api_response_strategy()
    )
    @settings(max_examples=10, deadline=None)
    def test_intelligent_query_decision_consistency_across_multiple_queries(self, manifests_with_package, tracking_numbers_without_manifest, api_response):
        """
        **Feature: express-tracking-website, Property 1: 智能查询决策**
        
        属性: 对于任何包含有集包单号和无集包单号的混合查询列表，系统应该为每个单号
        做出正确的查询决策，并保持决策的一致性
        
        验证需求: Requirements 1.2, 1.3, 1.4 - 系统应该首先检查该单号是否存在关联的集包单号，
        根据检查结果选择相应的查询策略
        """
        # 确保manifests中的tracking_number都是唯一的
        unique_manifests = []
        seen_tracking_numbers = set()
        for manifest in manifests_with_package:
            if manifest['tracking_number'] not in seen_tracking_numbers:
                unique_manifests.append(manifest)
                seen_tracking_numbers.add(manifest['tracking_number'])
        
        # 确保tracking_numbers_without_manifest与manifests不重复
        unique_tracking_numbers = []
        for tracking_number in tracking_numbers_without_manifest:
            if tracking_number not in seen_tracking_numbers:
                unique_tracking_numbers.append(tracking_number)
                seen_tracking_numbers.add(tracking_number)
        
        assume(len(unique_manifests) > 0 and len(unique_tracking_numbers) > 0)
        
        # 创建有集包单号的理货单记录
        for manifest_data in unique_manifests:
            try:
                self._create_manifest_record(manifest_data)
            except Exception as e:
                # 如果创建失败，跳过这个记录
                print(f"Failed to create manifest record: {e}")
                continue
        
        # 模拟快递100 API客户端
        with patch('app.services.intelligent_query_service.Kuaidi100Client') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.query_tracking.return_value = api_response
            mock_client_class.return_value = mock_client
            
            # 创建智能查询服务实例
            service = IntelligentQueryService(self.session)
            service.kuaidi100_client = mock_client
            
            # 查询所有有集包单号的快递单号
            for manifest_data in unique_manifests:
                result = asyncio.run(service.query_tracking(manifest_data['tracking_number']))
                
                # 验证使用集包单号查询
                assert result['query_type'] == 'package', \
                    f"有集包单号的快递单号应该使用package查询策略: {manifest_data['tracking_number']}"
                assert result['query_tracking_number'] == manifest_data['package_number'], \
                    f"应该使用集包单号查询: {result['query_tracking_number']} != {manifest_data['package_number']}"
                assert result['has_package_association'] == True, \
                    f"应该标识存在集包单号关联: {manifest_data['tracking_number']}"
            
            # 查询所有无理货单记录的快递单号
            for tracking_number in unique_tracking_numbers:
                result = asyncio.run(service.query_tracking(tracking_number))
                
                # 验证使用原单号查询
                assert result['query_type'] == 'original', \
                    f"无理货单记录的快递单号应该使用original查询策略: {tracking_number}"
                assert result['query_tracking_number'] == tracking_number, \
                    f"应该使用原单号查询: {result['query_tracking_number']} != {tracking_number}"
                assert result['has_package_association'] == False, \
                    f"应该标识不存在集包单号关联: {tracking_number}"
            
            # 验证API调用次数正确
            expected_calls = len(unique_manifests) + len(unique_tracking_numbers)
            assert mock_client.query_tracking.call_count == expected_calls, \
                f"API调用次数应该等于查询次数: {mock_client.query_tracking.call_count} != {expected_calls}"


def main():
    """运行属性测试"""
    print("=" * 60)
    print("智能查询决策属性测试")
    print("Intelligent Query Decision Property Tests")
    print("=" * 60)
    
    # 运行测试
    import pytest
    
    # 运行特定的测试类
    exit_code = pytest.main([
        __file__ + "::TestIntelligentQueryDecision",
        "-v",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n🎉 所有属性测试通过!")
        print("✅ 智能查询决策属性验证成功")
        print("\n📝 验证的属性:")
        print("- 存在集包单号时使用集包单号查询")
        print("- 不存在集包单号时使用原单号查询")
        print("- 集包单号为空时使用原单号查询")
        print("- 混合查询场景下决策一致性")
    else:
        print("\n❌ 部分属性测试失败")
    
    return exit_code == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)