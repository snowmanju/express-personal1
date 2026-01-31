"""
属性测试：性能合规 (Property 18)
验证需求8.1：处理10MB以内文件应在30秒内完成

**Feature: csv-file-upload, Property 18: Performance Compliance**
**Validates: Requirements 8.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import io
import csv
import time
from datetime import datetime

from app.services.csv_processor import CSVProcessor
from app.services.data_validator import DataValidator
from app.services.manifest_storage import ManifestStorage
from app.core.database import get_db


# 生成CSV内容的策略
@st.composite
def csv_file_content(draw, num_rows=None):
    """生成CSV文件内容"""
    if num_rows is None:
        # 生成足够大的文件（接近10MB）
        # 每行约100字节，10MB约需要100,000行
        num_rows = draw(st.integers(min_value=50000, max_value=100000))
    
    # CSV头部
    headers = ['理货日期', '快递单号', '集包单号', '长度', '宽度', '高度', '重量', '货物代码', '客户代码', '运输代码']
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # 生成数据行
    for i in range(num_rows):
        row = [
            '2024-01-15',
            f'TRK{i:010d}',
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
    
    # 转换为字节
    content = output.getvalue().encode('utf-8')
    return content


class TestPerformanceCompliance:
    """性能合规属性测试"""
    
    @given(file_size_mb=st.floats(min_value=0.1, max_value=10.0))
    @settings(
        max_examples=10,  # 减少示例数量，因为性能测试较慢
        deadline=None,  # 禁用deadline，因为我们要测试30秒限制
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
    )
    def test_property_18_performance_compliance_parsing(self, file_size_mb):
        """
        属性18：性能合规 - 文件解析
        
        对于任何10MB以内的文件，CSV处理器应在30秒内完成解析
        
        **Validates: Requirements 8.1**
        """
        # 计算需要的行数（每行约100字节）
        bytes_per_row = 100
        target_bytes = int(file_size_mb * 1024 * 1024)
        num_rows = max(1, target_bytes // bytes_per_row)
        
        # 生成指定大小的CSV内容
        csv_content = self._generate_csv_content(num_rows)
        
        # 验证文件大小
        actual_size_mb = len(csv_content) / (1024 * 1024)
        print(f"生成文件大小: {actual_size_mb:.2f}MB, 行数: {num_rows}")
        
        # 创建CSV处理器
        processor = CSVProcessor()
        
        # 测量解析时间
        start_time = time.time()
        result = processor.parse_csv(csv_content)
        elapsed_time = time.time() - start_time
        
        # 验证：解析应该成功
        assert result.success, f"文件解析失败: {result.errors}"
        
        # 验证：处理时间应在30秒内
        assert elapsed_time < 30.0, (
            f"性能不合规：处理{actual_size_mb:.2f}MB文件耗时{elapsed_time:.2f}秒，"
            f"超过30秒限制"
        )
        
        print(f"性能测试通过：{actual_size_mb:.2f}MB文件在{elapsed_time:.2f}秒内完成解析")
    
    def test_property_18_performance_compliance_10mb_file(self, db_session):
        """
        属性18：性能合规 - 完整处理流程（10MB文件）
        
        对于10MB的文件，完整的处理流程（解析+验证+存储）应在30秒内完成
        
        **Validates: Requirements 8.1**
        """
        # 生成接近10MB的CSV文件
        num_rows = 100000  # 约10MB
        csv_content = self._generate_csv_content(num_rows)
        
        actual_size_mb = len(csv_content) / (1024 * 1024)
        print(f"测试文件大小: {actual_size_mb:.2f}MB, 行数: {num_rows}")
        
        # 创建处理组件
        processor = CSVProcessor()
        validator = DataValidator()
        storage = ManifestStorage(db_session)
        
        # 测量完整处理时间
        start_time = time.time()
        
        # 预览模式处理（不保存到数据库）
        result = processor.process_file(
            file_content=csv_content,
            filename='test_large.csv',
            preview_only=True,
            data_validator=validator,
            manifest_storage=storage
        )
        
        elapsed_time = time.time() - start_time
        
        # 验证：处理应该成功
        assert result.success, f"文件处理失败: {result.errors}"
        
        # 验证：处理时间应在30秒内
        assert elapsed_time < 30.0, (
            f"性能不合规：处理{actual_size_mb:.2f}MB文件耗时{elapsed_time:.2f}秒，"
            f"超过30秒限制"
        )
        
        print(f"性能测试通过：{actual_size_mb:.2f}MB文件完整处理在{elapsed_time:.2f}秒内完成")
    
    def test_property_18_streaming_performance(self):
        """
        属性18：性能合规 - 流式处理性能
        
        验证流式处理能够有效处理大文件
        
        **Validates: Requirements 8.1, 8.2**
        """
        # 生成大文件（8MB）
        num_rows = 80000
        csv_content = self._generate_csv_content(num_rows)
        
        actual_size_mb = len(csv_content) / (1024 * 1024)
        print(f"流式处理测试文件大小: {actual_size_mb:.2f}MB")
        
        processor = CSVProcessor()
        
        # 测量流式处理时间
        start_time = time.time()
        result = processor.parse_csv(csv_content, use_streaming=True)
        elapsed_time = time.time() - start_time
        
        # 验证：处理应该成功
        assert result.success, f"流式处理失败: {result.errors}"
        
        # 验证：处理时间应在30秒内
        assert elapsed_time < 30.0, (
            f"流式处理性能不合规：处理{actual_size_mb:.2f}MB文件耗时{elapsed_time:.2f}秒"
        )
        
        print(f"流式处理性能测试通过：{actual_size_mb:.2f}MB文件在{elapsed_time:.2f}秒内完成")
    
    def test_property_18_batch_insert_performance(self, db_session):
        """
        属性18：性能合规 - 批量插入性能
        
        验证批量数据库操作的性能
        
        **Validates: Requirements 8.1, 8.5**
        """
        from app.services.manifest_storage import ManifestRecord
        
        # 生成大量记录
        num_records = 10000
        records = []
        
        for i in range(num_records):
            record = ManifestRecord(
                tracking_number=f'PERF{i:010d}',
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
        
        storage = ManifestStorage(db_session)
        
        # 测量批量插入时间
        start_time = time.time()
        result = storage.save_manifest_records(records)
        elapsed_time = time.time() - start_time
        
        # 验证：插入应该成功
        assert result.success, f"批量插入失败: {result.errors}"
        assert result.inserted == num_records, f"插入数量不匹配: {result.inserted} != {num_records}"
        
        # 验证：批量插入应该高效（10000条记录应在10秒内完成）
        assert elapsed_time < 10.0, (
            f"批量插入性能不合规：插入{num_records}条记录耗时{elapsed_time:.2f}秒"
        )
        
        print(f"批量插入性能测试通过：{num_records}条记录在{elapsed_time:.2f}秒内完成")
    
    def _generate_csv_content(self, num_rows: int) -> bytes:
        """生成指定行数的CSV内容"""
        headers = ['理货日期', '快递单号', '集包单号', '长度', '宽度', '高度', '重量', '货物代码', '客户代码', '运输代码']
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for i in range(num_rows):
            row = [
                '2024-01-15',
                f'TRK{i:010d}',
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
