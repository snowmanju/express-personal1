"""
属性测试：并发安全 (Property 19)
验证需求8.3：多用户同时上传时不会发生数据损坏

**Feature: csv-file-upload, Property 19: Concurrency Safety**
**Validates: Requirements 8.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import io
import csv
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from app.services.csv_processor import CSVProcessor
from app.services.data_validator import DataValidator
from app.services.manifest_storage import ManifestStorage, ManifestRecord


# 生成CSV内容的策略
def generate_csv_content(num_rows: int, prefix: str = "TRK") -> bytes:
    """生成CSV文件内容"""
    headers = ['理货日期', '快递单号', '集包单号', '长度', '宽度', '高度', '重量', '货物代码', '客户代码', '运输代码']
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for i in range(num_rows):
        row = [
            '2024-01-15',
            f'{prefix}{i:010d}',
            f'PKG{i:08d}',
            '10.5',
            '8.3',
            '5.2',
            '2.5',
            'GOODS001',
            'CUST001',
            'TRANS001'
        ]
        writer.writerow(row)
    
    return output.getvalue().encode('utf-8')


class TestConcurrencySafety:
    """并发安全属性测试"""
    
    def test_property_19_concurrent_parsing(self):
        """
        属性19：并发安全 - 并发解析
        
        多个线程同时解析不同的CSV文件时，不应发生数据损坏或错误
        
        **Validates: Requirements 8.3**
        """
        num_threads = 5
        rows_per_file = 1000
        
        def parse_file(thread_id: int) -> dict:
            """单个线程的解析任务"""
            csv_content = generate_csv_content(rows_per_file, prefix=f"T{thread_id}_")
            processor = CSVProcessor()
            
            result = processor.parse_csv(csv_content)
            
            return {
                'thread_id': thread_id,
                'success': result.success,
                'total_rows': result.total_rows,
                'errors': result.errors
            }
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(parse_file, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证：所有解析都应成功
        for result in results:
            assert result['success'], f"线程 {result['thread_id']} 解析失败: {result['errors']}"
            assert result['total_rows'] == rows_per_file, (
                f"线程 {result['thread_id']} 行数不匹配: {result['total_rows']} != {rows_per_file}"
            )
        
        print(f"并发解析测试通过：{num_threads}个线程同时解析，全部成功")
    
    def test_property_19_concurrent_validation(self):
        """
        属性19：并发安全 - 并发验证
        
        多个线程同时验证数据时，不应发生状态混乱
        
        **Validates: Requirements 8.3**
        """
        num_threads = 5
        rows_per_file = 500
        
        def validate_file(thread_id: int) -> dict:
            """单个线程的验证任务"""
            csv_content = generate_csv_content(rows_per_file, prefix=f"V{thread_id}_")
            
            processor = CSVProcessor()
            validator = DataValidator()
            
            result = processor.process_file(
                file_content=csv_content,
                filename=f'test_{thread_id}.csv',
                preview_only=True,
                data_validator=validator,
                manifest_storage=None
            )
            
            return {
                'thread_id': thread_id,
                'success': result.success,
                'valid_rows': result.statistics.valid_rows if result.statistics else 0,
                'invalid_rows': result.statistics.invalid_rows if result.statistics else 0
            }
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(validate_file, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证：所有验证都应成功
        for result in results:
            assert result['success'], f"线程 {result['thread_id']} 验证失败"
            assert result['valid_rows'] == rows_per_file, (
                f"线程 {result['thread_id']} 有效行数不匹配: {result['valid_rows']} != {rows_per_file}"
            )
            assert result['invalid_rows'] == 0, (
                f"线程 {result['thread_id']} 存在无效行: {result['invalid_rows']}"
            )
        
        print(f"并发验证测试通过：{num_threads}个线程同时验证，全部成功")
    
    def test_property_19_concurrent_storage_isolation(self, db_session):
        """
        属性19：并发安全 - 并发存储隔离
        
        多个线程同时存储数据时，应保持数据完整性（使用不同的tracking numbers）
        
        **Validates: Requirements 8.3**
        """
        num_threads = 3
        records_per_thread = 100
        
        def store_records(thread_id: int) -> dict:
            """单个线程的存储任务"""
            # 每个线程使用不同的tracking number前缀，避免冲突
            records = []
            for i in range(records_per_thread):
                record = ManifestRecord(
                    tracking_number=f'CONC{thread_id}_{i:06d}',
                    manifest_date='2024-01-15',
                    transport_code='TRANS001',
                    customer_code='CUST001',
                    goods_code='GOODS001',
                    length=10.5,
                    width=8.3,
                    height=5.2,
                    weight=2.5
                )
                records.append(record)
            
            # 创建独立的存储实例
            storage = ManifestStorage(db_session)
            result = storage.save_manifest_records(records)
            
            return {
                'thread_id': thread_id,
                'success': result.success,
                'inserted': result.inserted,
                'errors': result.errors
            }
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(store_records, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证：所有存储都应成功
        total_inserted = 0
        for result in results:
            assert result['success'], f"线程 {result['thread_id']} 存储失败: {result['errors']}"
            assert result['inserted'] == records_per_thread, (
                f"线程 {result['thread_id']} 插入数量不匹配: {result['inserted']} != {records_per_thread}"
            )
            total_inserted += result['inserted']
        
        # 验证总数
        expected_total = num_threads * records_per_thread
        assert total_inserted == expected_total, (
            f"总插入数量不匹配: {total_inserted} != {expected_total}"
        )
        
        print(f"并发存储测试通过：{num_threads}个线程同时存储，共插入{total_inserted}条记录")
    
    def test_property_19_concurrent_duplicate_handling(self, db_session):
        """
        属性19：并发安全 - 并发重复处理
        
        多个线程同时处理相同tracking number时，应正确处理重复
        
        **Validates: Requirements 8.3**
        """
        num_threads = 3
        shared_tracking_numbers = [f'SHARED{i:06d}' for i in range(50)]
        
        def store_shared_records(thread_id: int) -> dict:
            """存储共享tracking number的记录"""
            records = []
            for tracking_number in shared_tracking_numbers:
                record = ManifestRecord(
                    tracking_number=tracking_number,
                    manifest_date='2024-01-15',
                    transport_code=f'TRANS{thread_id:03d}',  # 不同线程使用不同的transport_code
                    customer_code='CUST001',
                    goods_code='GOODS001',
                    length=10.5 + thread_id,  # 不同的值
                    width=8.3,
                    height=5.2,
                    weight=2.5
                )
                records.append(record)
            
            storage = ManifestStorage(db_session)
            result = storage.save_manifest_records(records)
            
            return {
                'thread_id': thread_id,
                'success': result.success,
                'inserted': result.inserted,
                'updated': result.updated
            }
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(store_shared_records, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证：所有操作都应成功
        total_operations = 0
        for result in results:
            assert result['success'], f"线程 {result['thread_id']} 操作失败"
            operations = result['inserted'] + result['updated']
            assert operations == len(shared_tracking_numbers), (
                f"线程 {result['thread_id']} 操作数量不匹配: {operations} != {len(shared_tracking_numbers)}"
            )
            total_operations += operations
        
        print(f"并发重复处理测试通过：{num_threads}个线程处理共享tracking numbers，"
              f"总操作数: {total_operations}")
    
    @given(num_threads=st.integers(min_value=2, max_value=5))
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    def test_property_19_concurrent_processing_property(self, num_threads):
        """
        属性19：并发安全 - 属性测试
        
        对于任意数量的并发线程，处理应该是安全的
        
        **Validates: Requirements 8.3**
        """
        rows_per_file = 100
        
        def process_file(thread_id: int) -> bool:
            """单个线程的处理任务"""
            try:
                csv_content = generate_csv_content(rows_per_file, prefix=f"P{thread_id}_")
                processor = CSVProcessor()
                validator = DataValidator()
                
                result = processor.process_file(
                    file_content=csv_content,
                    filename=f'test_{thread_id}.csv',
                    preview_only=True,
                    data_validator=validator,
                    manifest_storage=None
                )
                
                return result.success and result.statistics.valid_rows == rows_per_file
            except Exception as e:
                print(f"线程 {thread_id} 异常: {str(e)}")
                return False
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(process_file, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证：所有处理都应成功
        assert all(results), f"并发处理失败，成功率: {sum(results)}/{len(results)}"
        
        print(f"并发处理属性测试通过：{num_threads}个线程同时处理")


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    from app.core.database import SessionLocal, engine
    from app.models.cargo_manifest import Base
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    db = SessionLocal()
    
    try:
        yield db
    finally:
        # 清理测试数据
        db.rollback()
        db.close()
        
        # 删除表
        Base.metadata.drop_all(bind=engine)
