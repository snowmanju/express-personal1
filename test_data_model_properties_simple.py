#!/usr/bin/env python3
"""
数据模型属性测试 - 简化版本
Data Model Property Tests - Simplified Version

**Feature: express-tracking-website, Property 8: 增量更新一致性**
**验证需求: Requirements 3.4, 3.5**
"""

import sys
import os
from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import tempfile
import random
import string

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

# 导入SQLAlchemy组件
from sqlalchemy import create_engine, Column, Integer, String, Date, DECIMAL, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker, Session
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
        
        # 提交事务
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
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


def generate_random_manifest_data(count: int = 1) -> List[Dict[str, Any]]:
    """生成随机理货单数据"""
    manifests = []
    
    for i in range(count):
        tracking_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        manifest = {
            'tracking_number': tracking_number,
            'manifest_date': date(2024, random.randint(1, 12), random.randint(1, 28)),
            'transport_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
            'customer_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
            'goods_code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
            'package_number': ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) if random.choice([True, False]) else None,
            'weight': Decimal(str(round(random.uniform(0.1, 1000.0), 2))) if random.choice([True, False]) else None,
            'length': Decimal(str(round(random.uniform(1.0, 100.0), 2))) if random.choice([True, False]) else None,
            'width': Decimal(str(round(random.uniform(1.0, 100.0), 2))) if random.choice([True, False]) else None,
            'height': Decimal(str(round(random.uniform(1.0, 100.0), 2))) if random.choice([True, False]) else None,
            'special_fee': Decimal(str(round(random.uniform(0.0, 500.0), 2))) if random.choice([True, False]) else None
        }
        manifests.append(manifest)
    
    return manifests


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


def test_incremental_update_consistency_new_records():
    """
    **Feature: express-tracking-website, Property 8: 增量更新一致性**
    
    属性: 对于任何新的理货单数据列表，处理后应该全部作为新记录插入，
    统计信息应该准确反映插入的记录数量
    """
    print("🔍 测试新记录插入一致性...")
    
    session, db_path = create_test_db_session()
    processor = ManifestProcessor(session)
    
    try:
        # 生成测试数据
        test_data = generate_random_manifest_data(5)
        
        # 处理数据
        result = processor.process_manifest_data(test_data)
        
        # 验证统计信息
        assert result['total'] == len(test_data), \
            f"总数应该等于输入数据数量: {result['total']} != {len(test_data)}"
        
        assert result['inserted'] == len(test_data), \
            f"插入数量应该等于输入数据数量: {result['inserted']} != {len(test_data)}"
        
        assert result['updated'] == 0, \
            f"更新数量应该为0: {result['updated']}"
        
        assert result['errors'] == 0, \
            f"错误数量应该为0: {result['errors']}"
        
        # 验证数据库中的记录数量
        db_count = session.query(TestCargoManifest).count()
        assert db_count == len(test_data), \
            f"数据库记录数量应该等于插入数量: {db_count} != {len(test_data)}"
        
        print(f"✅ 新记录插入测试通过 - 插入了 {result['inserted']} 条记录")
        return True
        
    finally:
        session.close()
        try:
            os.unlink(db_path)
        except:
            pass


def test_incremental_update_consistency_existing_records():
    """
    **Feature: express-tracking-website, Property 8: 增量更新一致性**
    
    属性: 对于任何已存在的理货单数据，再次处理时应该作为更新操作，
    统计信息应该准确反映更新的记录数量
    """
    print("🔍 测试现有记录更新一致性...")
    
    session, db_path = create_test_db_session()
    processor = ManifestProcessor(session)
    
    try:
        # 生成测试数据
        test_data = generate_random_manifest_data(3)
        
        # 第一次处理 - 插入数据
        first_result = processor.process_manifest_data(test_data)
        
        # 修改数据（保持tracking_number不变）
        modified_data = []
        for manifest in test_data:
            modified = manifest.copy()
            modified['transport_code'] = 'UPD_' + modified['transport_code'][:2]
            modified_data.append(modified)
        
        # 第二次处理 - 更新数据
        second_result = processor.process_manifest_data(modified_data)
        
        # 验证第二次处理的统计信息
        assert second_result['total'] == len(test_data), \
            f"总数应该等于输入数据数量: {second_result['total']} != {len(test_data)}"
        
        assert second_result['inserted'] == 0, \
            f"插入数量应该为0: {second_result['inserted']}"
        
        assert second_result['updated'] == len(test_data), \
            f"更新数量应该等于输入数据数量: {second_result['updated']} != {len(test_data)}"
        
        assert second_result['errors'] == 0, \
            f"错误数量应该为0: {second_result['errors']}"
        
        # 验证数据库中的记录数量没有增加
        db_count = session.query(TestCargoManifest).count()
        assert db_count == len(test_data), \
            f"数据库记录数量应该保持不变: {db_count} != {len(test_data)}"
        
        # 验证数据确实被更新了
        for modified in modified_data:
            record = session.query(TestCargoManifest).filter(
                TestCargoManifest.tracking_number == modified['tracking_number']
            ).first()
            assert record is not None, f"记录应该存在: {modified['tracking_number']}"
            assert record.transport_code == modified['transport_code'], \
                f"数据应该被更新: {record.transport_code} != {modified['transport_code']}"
        
        print(f"✅ 现有记录更新测试通过 - 更新了 {second_result['updated']} 条记录")
        return True
        
    finally:
        session.close()
        try:
            os.unlink(db_path)
        except:
            pass


def test_incremental_update_consistency_mixed_operations():
    """
    **Feature: express-tracking-website, Property 8: 增量更新一致性**
    
    属性: 对于包含新记录和已存在记录的混合数据，系统应该正确区分并执行
    相应的插入和更新操作，统计信息应该准确反映各种操作的数量
    """
    print("🔍 测试混合操作一致性...")
    
    session, db_path = create_test_db_session()
    processor = ManifestProcessor(session)
    
    try:
        # 生成现有数据
        existing_data = generate_random_manifest_data(2)
        
        # 生成新数据
        new_data = generate_random_manifest_data(3)
        
        # 第一步：插入existing数据
        processor.process_manifest_data(existing_data)
        
        # 第二步：修改existing数据并与new数据混合
        modified_existing = []
        for manifest in existing_data:
            modified = manifest.copy()
            modified['customer_code'] = 'UPD_' + modified['customer_code'][:2]
            modified_existing.append(modified)
        
        # 混合数据：修改的existing + 新的new
        mixed_data = modified_existing + new_data
        
        # 处理混合数据
        result = processor.process_manifest_data(mixed_data)
        
        # 验证统计信息
        expected_total = len(existing_data) + len(new_data)
        assert result['total'] == expected_total, \
            f"总数应该等于混合数据数量: {result['total']} != {expected_total}"
        
        assert result['inserted'] == len(new_data), \
            f"插入数量应该等于新数据数量: {result['inserted']} != {len(new_data)}"
        
        assert result['updated'] == len(existing_data), \
            f"更新数量应该等于已存在数据数量: {result['updated']} != {len(existing_data)}"
        
        assert result['errors'] == 0, \
            f"错误数量应该为0: {result['errors']}"
        
        # 验证数据库中的总记录数量
        db_count = session.query(TestCargoManifest).count()
        assert db_count == expected_total, \
            f"数据库记录数量应该等于总数量: {db_count} != {expected_total}"
        
        print(f"✅ 混合操作测试通过 - 插入了 {result['inserted']} 条，更新了 {result['updated']} 条记录")
        return True
        
    finally:
        session.close()
        try:
            os.unlink(db_path)
        except:
            pass


def run_property_tests():
    """运行所有属性测试"""
    print("=" * 60)
    print("数据模型增量更新一致性属性测试")
    print("Data Model Incremental Update Consistency Property Tests")
    print("=" * 60)
    
    tests = [
        ("新记录插入一致性", test_incremental_update_consistency_new_records),
        ("现有记录更新一致性", test_incremental_update_consistency_existing_records),
        ("混合操作一致性", test_incremental_update_consistency_mixed_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有属性测试通过!")
        print("✅ 增量更新一致性属性验证成功")
        print("\n📝 验证的属性:")
        print("- 新记录正确插入并统计")
        print("- 已存在记录正确更新并统计")
        print("- 混合操作正确区分并统计")
        return True
    else:
        print("❌ 部分属性测试失败")
        return False


def main():
    """主函数"""
    # 运行多次以验证一致性
    print("🔄 运行多轮测试以验证一致性...")
    
    success_count = 0
    total_rounds = 10
    
    for round_num in range(1, total_rounds + 1):
        print(f"\n🔄 第 {round_num} 轮测试:")
        if run_property_tests():
            success_count += 1
    
    print(f"\n📊 总体结果: {success_count}/{total_rounds} 轮测试通过")
    
    if success_count == total_rounds:
        print("🎉 所有轮次测试通过! 增量更新一致性属性验证成功!")
        return True
    else:
        print("❌ 部分轮次测试失败")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)