#!/usr/bin/env python3
"""
数据模型属性测试
Data Model Property Tests

**Feature: express-tracking-website, Property 8: 增量更新一致性**
**验证需求: Requirements 3.4, 3.5**
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import tempfile
import sqlite3

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize
import pytest

# 导入SQLAlchemy组件
from sqlalchemy import create_engine, Column, Integer, String, Date, DECIMAL, TIMESTAMP, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func


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


class ManifestProcessor:
    """
    理货单处理器 - 实现增量更新逻辑
    用于测试增量更新一致性属性
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def process_manifest_data(self, manifest_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        处理理货单数据，实现增量更新
        
        Args:
            manifest_data: 理货单数据列表
            
        Returns:
            包含统计信息的字典: {total, inserted, updated, errors}
        """
        results = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'errors': 0
        }
        
        for data in manifest_data:
            try:
                # 验证必需字段
                if not self._validate_manifest_data(data):
                    results['errors'] += 1
                    continue
                
                # 检查是否已存在相同tracking_number的记录
                existing = self.db_session.query(TestCargoManifest).filter(
                    TestCargoManifest.tracking_number == data['tracking_number']
                ).first()
                
                if existing:
                    # 更新现有记录
                    self._update_manifest(existing, data)
                    results['updated'] += 1
                else:
                    # 插入新记录
                    self._insert_manifest(data)
                    results['inserted'] += 1
                
                results['total'] += 1
                
            except Exception as e:
                # 回滚当前事务并继续处理下一条记录
                self.db_session.rollback()
                results['errors'] += 1
                print(f"Error processing manifest data: {e}, data: {data}")  # Debug info
        
        # 提交事务
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            print(f"Error committing transaction: {e}")  # Debug info
            # 如果提交失败，将所有成功操作标记为错误
            results['errors'] += results['inserted'] + results['updated']
            results['inserted'] = 0
            results['updated'] = 0
            results['total'] = results['errors']
        
        return results
    
    def _validate_manifest_data(self, data: Dict[str, Any]) -> bool:
        """验证理货单数据"""
        required_fields = ['tracking_number', 'manifest_date', 'transport_code', 
                          'customer_code', 'goods_code']
        return all(field in data and data[field] is not None for field in required_fields)
    
    def _insert_manifest(self, data: Dict[str, Any]) -> None:
        """插入新的理货单记录"""
        manifest = TestCargoManifest(
            tracking_number=data['tracking_number'],
            manifest_date=data['manifest_date'],
            transport_code=data['transport_code'],
            customer_code=data['customer_code'],
            goods_code=data['goods_code'],
            package_number=data.get('package_number'),
            weight=data.get('weight'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            special_fee=data.get('special_fee')
        )
        self.db_session.add(manifest)
        self.db_session.flush()  # 立即执行插入以检测错误
    
    def _update_manifest(self, existing: TestCargoManifest, data: Dict[str, Any]) -> None:
        """更新现有的理货单记录"""
        existing.manifest_date = data['manifest_date']
        existing.transport_code = data['transport_code']
        existing.customer_code = data['customer_code']
        existing.goods_code = data['goods_code']
        existing.package_number = data.get('package_number')
        existing.weight = data.get('weight')
        existing.length = data.get('length')
        existing.width = data.get('width')
        existing.height = data.get('height')
        existing.special_fee = data.get('special_fee')
        self.db_session.flush()  # 立即执行更新以检测错误


# Hypothesis策略定义
@st.composite
def manifest_data_strategy(draw):
    """生成理货单数据的策略"""
    return {
        'tracking_number': draw(st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=5, max_size=20
        )),
        'manifest_date': draw(st.dates(
            min_value=date(2020, 1, 1),
            max_value=date(2024, 12, 31)
        )),
        'transport_code': draw(st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=1, max_size=10
        )),
        'customer_code': draw(st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=1, max_size=10
        )),
        'goods_code': draw(st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=1, max_size=10
        )),
        'package_number': draw(st.one_of(
            st.none(),
            st.text(
                alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                min_size=1, max_size=20
            )
        )),
        'weight': draw(st.one_of(
            st.none(),
            st.decimals(min_value=0, max_value=9999, places=2)
        )),
        'length': draw(st.one_of(
            st.none(),
            st.decimals(min_value=0, max_value=999, places=2)
        )),
        'width': draw(st.one_of(
            st.none(),
            st.decimals(min_value=0, max_value=999, places=2)
        )),
        'height': draw(st.one_of(
            st.none(),
            st.decimals(min_value=0, max_value=999, places=2)
        )),
        'special_fee': draw(st.one_of(
            st.none(),
            st.decimals(min_value=0, max_value=9999, places=2)
        ))
    }


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


class TestIncrementalUpdateConsistency:
    """增量更新一致性属性测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.session, self.db_path = create_test_db_session()
        self.processor = ManifestProcessor(self.session)
        
        # 清空数据库以确保测试隔离
        self.session.query(TestCargoManifest).delete()
        self.session.commit()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        try:
            # 清空数据库
            self.session.query(TestCargoManifest).delete()
            self.session.commit()
            self.session.close()
        except:
            pass
        
        # 尝试删除临时数据库文件
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except PermissionError:
            # Windows上可能出现文件被占用的情况，忽略这个错误
            pass
    
    @given(st.lists(manifest_data_strategy(), min_size=1, max_size=20))
    @settings(max_examples=10, deadline=None)
    def test_incremental_update_consistency_new_records(self, manifest_list):
        """
        **Feature: express-tracking-website, Property 8: 增量更新一致性**
        
        属性: 对于任何新的理货单数据列表，处理后应该全部作为新记录插入，
        统计信息应该准确反映插入的记录数量
        """
        # 确保所有tracking_number都是唯一的
        unique_manifests = []
        seen_tracking_numbers = set()
        
        for manifest in manifest_list:
            if manifest['tracking_number'] not in seen_tracking_numbers:
                unique_manifests.append(manifest)
                seen_tracking_numbers.add(manifest['tracking_number'])
        
        assume(len(unique_manifests) > 0)
        
        # 处理数据
        result = self.processor.process_manifest_data(unique_manifests)
        
        # 验证统计信息
        assert result['total'] == len(unique_manifests), \
            f"总数应该等于输入数据数量: {result['total']} != {len(unique_manifests)}"
        
        assert result['inserted'] == len(unique_manifests), \
            f"插入数量应该等于输入数据数量: {result['inserted']} != {len(unique_manifests)}"
        
        assert result['updated'] == 0, \
            f"更新数量应该为0: {result['updated']}"
        
        assert result['errors'] == 0, \
            f"错误数量应该为0: {result['errors']}"
        
        # 验证数据库中的记录数量
        db_count = self.session.query(TestCargoManifest).count()
        assert db_count == len(unique_manifests), \
            f"数据库记录数量应该等于插入数量: {db_count} != {len(unique_manifests)}"
    
    @given(st.lists(manifest_data_strategy(), min_size=1, max_size=10))
    @settings(max_examples=10, deadline=None)
    def test_incremental_update_consistency_existing_records(self, manifest_list):
        """
        **Feature: express-tracking-website, Property 8: 增量更新一致性**
        
        属性: 对于任何已存在的理货单数据，再次处理时应该作为更新操作，
        统计信息应该准确反映更新的记录数量
        """
        # 确保所有tracking_number都是唯一的
        unique_manifests = []
        seen_tracking_numbers = set()
        
        for manifest in manifest_list:
            if manifest['tracking_number'] not in seen_tracking_numbers:
                unique_manifests.append(manifest)
                seen_tracking_numbers.add(manifest['tracking_number'])
        
        assume(len(unique_manifests) > 0)
        
        # 第一次处理 - 插入数据
        first_result = self.processor.process_manifest_data(unique_manifests)
        
        # 修改数据（保持tracking_number不变）
        modified_manifests = []
        for manifest in unique_manifests:
            modified = manifest.copy()
            modified['transport_code'] = 'UPDATED_' + modified['transport_code'][:15]
            modified_manifests.append(modified)
        
        # 第二次处理 - 更新数据
        second_result = self.processor.process_manifest_data(modified_manifests)
        
        # 验证第二次处理的统计信息
        assert second_result['total'] == len(unique_manifests), \
            f"总数应该等于输入数据数量: {second_result['total']} != {len(unique_manifests)}"
        
        assert second_result['inserted'] == 0, \
            f"插入数量应该为0: {second_result['inserted']}"
        
        assert second_result['updated'] == len(unique_manifests), \
            f"更新数量应该等于输入数据数量: {second_result['updated']} != {len(unique_manifests)}"
        
        assert second_result['errors'] == 0, \
            f"错误数量应该为0: {second_result['errors']}"
        
        # 验证数据库中的记录数量没有增加
        db_count = self.session.query(TestCargoManifest).count()
        assert db_count == len(unique_manifests), \
            f"数据库记录数量应该保持不变: {db_count} != {len(unique_manifests)}"
        
        # 验证数据确实被更新了
        for modified in modified_manifests:
            record = self.session.query(TestCargoManifest).filter(
                TestCargoManifest.tracking_number == modified['tracking_number']
            ).first()
            assert record is not None, f"记录应该存在: {modified['tracking_number']}"
            assert record.transport_code == modified['transport_code'], \
                f"数据应该被更新: {record.transport_code} != {modified['transport_code']}"
    
    @given(
        st.lists(manifest_data_strategy(), min_size=1, max_size=5),
        st.lists(manifest_data_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=10, deadline=None)
    def test_incremental_update_consistency_mixed_operations(self, existing_manifests, new_manifests):
        """
        **Feature: express-tracking-website, Property 8: 增量更新一致性**
        
        属性: 对于包含新记录和已存在记录的混合数据，系统应该正确区分并执行
        相应的插入和更新操作，统计信息应该准确反映各种操作的数量
        """
        # 确保existing_manifests中的tracking_number都是唯一的
        unique_existing = []
        seen_existing = set()
        for manifest in existing_manifests:
            if manifest['tracking_number'] not in seen_existing:
                unique_existing.append(manifest)
                seen_existing.add(manifest['tracking_number'])
        
        # 确保new_manifests中的tracking_number都是唯一的，且与existing不重复
        unique_new = []
        seen_new = set()
        for manifest in new_manifests:
            if (manifest['tracking_number'] not in seen_new and 
                manifest['tracking_number'] not in seen_existing):
                unique_new.append(manifest)
                seen_new.add(manifest['tracking_number'])
        
        assume(len(unique_existing) > 0 and len(unique_new) > 0)
        
        # 第一步：插入existing数据
        self.processor.process_manifest_data(unique_existing)
        
        # 第二步：修改existing数据并与new数据混合
        modified_existing = []
        for manifest in unique_existing:
            modified = manifest.copy()
            modified['customer_code'] = 'UPD_' + modified['customer_code'][:16]
            modified_existing.append(modified)
        
        # 混合数据：修改的existing + 新的new
        mixed_data = modified_existing + unique_new
        
        # 处理混合数据
        result = self.processor.process_manifest_data(mixed_data)
        
        # 验证统计信息
        expected_total = len(unique_existing) + len(unique_new)
        assert result['total'] == expected_total, \
            f"总数应该等于混合数据数量: {result['total']} != {expected_total}"
        
        assert result['inserted'] == len(unique_new), \
            f"插入数量应该等于新数据数量: {result['inserted']} != {len(unique_new)}"
        
        assert result['updated'] == len(unique_existing), \
            f"更新数量应该等于已存在数据数量: {result['updated']} != {len(unique_existing)}"
        
        assert result['errors'] == 0, \
            f"错误数量应该为0: {result['errors']}"
        
        # 验证数据库中的总记录数量
        db_count = self.session.query(TestCargoManifest).count()
        assert db_count == expected_total, \
            f"数据库记录数量应该等于总数量: {db_count} != {expected_total}"


def main():
    """运行属性测试"""
    print("=" * 60)
    print("数据模型增量更新一致性属性测试")
    print("Data Model Incremental Update Consistency Property Tests")
    print("=" * 60)
    
    # 运行测试
    import pytest
    
    # 运行特定的测试类
    exit_code = pytest.main([
        __file__ + "::TestIncrementalUpdateConsistency",
        "-v",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n🎉 所有属性测试通过!")
        print("✅ 增量更新一致性属性验证成功")
        print("\n📝 验证的属性:")
        print("- 新记录正确插入并统计")
        print("- 已存在记录正确更新并统计")
        print("- 混合操作正确区分并统计")
    else:
        print("\n❌ 部分属性测试失败")
    
    return exit_code == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)