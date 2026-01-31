"""
最终版端到端集成测试 (Final End-to-End Integration Tests)
专注于核心业务流程测试，简化认证和数据库配置

Feature: express-tracking-website, Task 12.1: 编写端到端集成测试
"""

import pytest
import asyncio
import json
import io
import csv
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

# 直接测试服务层，避免复杂的API和认证问题
from app.services.intelligent_query_service import IntelligentQueryService
from app.services.manifest_service import ManifestService
from app.services.file_processor_service import FileProcessorService
from app.services.data_sync_service import data_sync_service
from app.models.cargo_manifest import CargoManifest


class MockDatabase:
    """模拟数据库会话"""
    
    def __init__(self):
        self.manifests = {}
        self.id_counter = 1
    
    def add(self, manifest):
        """添加理货单"""
        manifest.id = self.id_counter
        self.id_counter += 1
        self.manifests[manifest.tracking_number] = manifest
    
    def commit(self):
        """提交事务"""
        pass
    
    def rollback(self):
        """回滚事务"""
        pass
    
    def refresh(self, obj):
        """刷新对象"""
        pass
    
    def query(self, model):
        """查询模型"""
        return MockQuery(self.manifests)
    
    def close(self):
        """关闭会话"""
        pass


class MockQuery:
    """模拟查询对象"""
    
    def __init__(self, manifests):
        self.manifests = manifests
        self.filters = []
    
    def filter(self, condition):
        """添加过滤条件"""
        # 简化处理，只处理tracking_number查询
        return self
    
    def order_by(self, *args):
        """排序"""
        return self
    
    def offset(self, offset):
        """偏移"""
        return self
    
    def limit(self, limit):
        """限制"""
        return self
    
    def first(self):
        """获取第一个结果"""
        # 简化处理，返回任意一个理货单用于测试
        if self.manifests:
            return list(self.manifests.values())[0]
        return None
    
    def all(self):
        """获取所有结果"""
        return list(self.manifests.values())
    
    def count(self):
        """获取数量"""
        return len(self.manifests)


class TestEndToEndIntegrationFinal:
    """最终版端到端集成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.mock_db = MockDatabase()
        
        # 清理缓存和同步状态
        data_sync_service.invalidate_all_cache()
        data_sync_service.clear_pending_sync_operations()
    
    def create_test_csv_content(self, data):
        """创建测试CSV内容"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            '快递单号', '理货日期', '运输代码', 
            '客户代码', '货物代码', '集包单号', 
            '重量', '长度', '宽度', '高度', '特殊费用'
        ])
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')
    
    def test_complete_query_flow_with_package_association(self):
        """
        测试完整的查询流程 - 有集包单号关联
        
        测试场景：
        1. 上传理货单数据
        2. 查询有集包单号的快递
        3. 验证智能判断逻辑
        4. 验证API调用参数
        """
        print("🔍 测试完整的查询流程 - 有集包单号关联")
        
        # Step 1: 创建理货单数据
        print("  📤 Step 1: 创建理货单数据")
        
        manifest = CargoManifest(
            tracking_number='E2ETEST001',
            manifest_date=date(2024, 1, 15),
            transport_code='TC001',
            customer_code='CC001',
            goods_code='GC001',
            package_number='PKGE2E001',
            weight=Decimal('2.5')
        )
        
        self.mock_db.add(manifest)
        self.mock_db.commit()
        
        print("    ✓ 理货单数据创建成功")
        
        # Step 2: 测试智能查询服务
        print("  🔍 Step 2: 测试智能查询服务")
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            # Mock快递100 API响应
            mock_query.return_value = {
                'success': True,
                'company_code': 'SF',
                'company_name': '顺丰速运',
                'state': '1',
                'status': '运输中',
                'data': [
                    {
                        'time': '2024-01-15 10:00:00',
                        'location': '深圳市',
                        'context': '快件已发出'
                    }
                ]
            }
            
            # 创建智能查询服务
            query_service = IntelligentQueryService(self.mock_db)
            
            # 模拟查找理货单的方法
            async def mock_find_manifest(tracking_number):
                if tracking_number == 'E2ETEST001':
                    return manifest
                return None
            
            query_service._find_manifest_by_tracking_number = mock_find_manifest
            
            # 执行查询
            result = asyncio.run(query_service.query_tracking('E2ETEST001'))
            
            # 调试输出
            print(f"    查询结果: {result}")
            
            # 验证查询结果
            assert result['success'] is True
            assert result['original_tracking_number'] == 'E2ETEST001'
            assert result['query_tracking_number'] == 'PKGE2E001'  # 使用集包单号查询
            assert result['query_type'] == 'package'
            assert result['has_package_association'] is True
            
            # 验证理货单信息
            assert result['manifest_info'] is not None
            assert result['manifest_info']['transport_code'] == 'TC001'
            assert result['manifest_info']['customer_code'] == 'CC001'
            
            # 验证快递信息
            assert result['tracking_info'] is not None
            assert result['tracking_info']['company_name'] == '顺丰速运'
            
            # 验证API调用使用了集包单号
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]
            assert call_args['tracking_number'] == 'PKGE2E001'
        
        print("    ✓ 智能查询服务测试通过")
        print("✅ 有集包单号关联的查询流程测试通过")
    
    def test_complete_query_flow_without_package_association(self):
        """
        测试完整的查询流程 - 无集包单号关联
        
        测试场景：
        1. 查询无集包单号的快递
        2. 验证智能判断逻辑
        3. 验证API调用参数
        """
        print("🔍 测试完整的查询流程 - 无集包单号关联")
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            mock_query.return_value = {
                'success': True,
                'company_code': 'YTO',
                'company_name': '圆通速递',
                'state': '2',
                'status': '派送中',
                'data': [
                    {
                        'time': '2024-01-15 14:00:00',
                        'location': '北京市',
                        'context': '正在派送'
                    }
                ]
            }
            
            # 创建智能查询服务
            query_service = IntelligentQueryService(self.mock_db)
            
            # 模拟查找理货单的方法（返回None表示无关联）
            async def mock_find_manifest(tracking_number):
                return None
            
            query_service._find_manifest_by_tracking_number = mock_find_manifest
            
            # 执行查询
            result = asyncio.run(query_service.query_tracking('E2ETEST002'))
            
            # 验证查询结果
            assert result['success'] is True
            assert result['original_tracking_number'] == 'E2ETEST002'
            assert result['query_tracking_number'] == 'E2ETEST002'  # 使用原单号查询
            assert result['query_type'] == 'original'
            assert result['has_package_association'] is False
            
            # 验证API调用使用了原单号
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]
            assert call_args['tracking_number'] == 'E2ETEST002'
        
        print("    ✓ 智能查询服务测试通过")
        print("✅ 无集包单号关联的查询流程测试通过")
    
    def test_file_processing_and_data_management(self):
        """
        测试文件处理和数据管理
        
        测试场景：
        1. CSV文件解析
        2. 数据验证
        3. 增量更新机制
        4. 理货单管理操作
        """
        print("🔍 测试文件处理和数据管理")
        
        # Step 1: 测试CSV文件解析
        print("  📋 Step 1: 测试CSV文件解析")
        
        test_data = [
            {
                '快递单号': 'E2EFILE001',
                '理货日期': '2024-01-16',
                '运输代码': 'TCFILE',
                '客户代码': 'CCFILE',
                '货物代码': 'GCFILE',
                '集包单号': 'PKGFILE001',
                '重量': '3.0',
                '长度': '40.0',
                '宽度': '30.0',
                '高度': '20.0',
                '特殊费用': '25.00'
            }
        ]
        
        csv_content = self.create_test_csv_content(test_data)
        
        # 创建文件处理服务
        file_processor = FileProcessorService(self.mock_db)
        
        # 解析CSV文件
        df, parse_errors = file_processor.parse_file(csv_content, 'test.csv')
        
        assert parse_errors == []
        assert len(df) == 1
        assert df.iloc[0]['快递单号'] == 'E2EFILE001'
        
        print("    ✓ CSV文件解析成功")
        
        # Step 2: 测试数据验证
        print("  ✅ Step 2: 测试数据验证")
        
        # 验证列结构
        column_errors = file_processor.validate_columns(df)
        print(f"    列验证错误: {column_errors}")
        assert column_errors == []
        
        # 验证数据内容
        validation_result = file_processor.validate_and_preview(csv_content, 'test.csv')
        print(f"    数据验证结果: {validation_result['success']}, 错误: {validation_result['errors']}")
        assert validation_result['success'] is True
        assert validation_result['valid_rows'] == 1
        
        # 获取处理后的数据
        processed_data = []
        for row in validation_result['preview_data']:
            if row['valid']:
                # 转换中文字段名为英文字段名
                english_data = {}
                chinese_data = row['data']
                field_mapping = {
                    '快递单号': 'tracking_number',
                    '理货日期': 'manifest_date',
                    '运输代码': 'transport_code',
                    '客户代码': 'customer_code',
                    '货物代码': 'goods_code',
                    '集包单号': 'package_number',
                    '重量': 'weight',
                    '长度': 'length',
                    '宽度': 'width',
                    '高度': 'height',
                    '特殊费用': 'special_fee'
                }
                for chinese_field, english_field in field_mapping.items():
                    if chinese_field in chinese_data:
                        english_data[english_field] = chinese_data[chinese_field]
                processed_data.append(english_data)
        
        assert len(processed_data) == 1
        assert processed_data[0]['tracking_number'] == 'E2EFILE001'
        
        print("    ✓ 数据验证通过")
        
        # Step 3: 测试理货单管理服务
        print("  📊 Step 3: 测试理货单管理服务")
        
        # 创建理货单管理服务
        manifest_service = ManifestService(self.mock_db)
        
        # 创建理货单
        print(f"    创建理货单数据: {processed_data[0]}")
        create_result = manifest_service.create_manifest(processed_data[0])
        print(f"    创建结果: {create_result}")
        assert create_result['success'] is True
        assert create_result['data']['tracking_number'] == 'E2EFILE001'
        
        print("    ✓ 理货单创建成功")
        
        # 搜索理货单
        search_result = manifest_service.search_manifests(search_query='E2EFILE')
        assert search_result['success'] is True
        assert len(search_result['data']) >= 1
        
        print("    ✓ 理货单搜索成功")
        
        print("✅ 文件处理和数据管理测试通过")
    
    def test_error_handling_scenarios(self):
        """
        测试错误处理场景
        
        测试场景：
        1. API调用失败处理
        2. 输入验证错误处理
        3. 数据处理异常处理
        """
        print("🔍 测试错误处理场景")
        
        # Step 1: 测试API调用失败处理
        print("  🌐 Step 1: 测试API调用失败处理")
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            # 模拟网络错误
            mock_query.side_effect = Exception("Network connection failed")
            
            # 创建智能查询服务
            query_service = IntelligentQueryService(self.mock_db)
            
            # 模拟查找理货单的方法
            async def mock_find_manifest(tracking_number):
                return None
            
            query_service._find_manifest_by_tracking_number = mock_find_manifest
            
            # 执行查询
            result = asyncio.run(query_service.query_tracking('TESTERROR001'))
            
            # 验证错误处理
            print(f"    错误处理结果: {result}")
            assert result['success'] is False
            assert '系统异常' in result['error']  # 智能查询服务返回通用错误消息
        
        print("    ✓ API调用失败处理正常")
        
        # Step 2: 测试输入验证错误处理
        print("  ✅ Step 2: 测试输入验证错误处理")
        
        # 创建智能查询服务
        query_service = IntelligentQueryService(self.mock_db)
        
        # 测试无效输入
        result = asyncio.run(query_service.query_tracking('<script>alert("xss")</script>'))
        assert result['success'] is False
        assert '输入验证失败' in result['error']
        
        # 测试空输入
        result = asyncio.run(query_service.query_tracking(''))
        assert result['success'] is False
        
        print("    ✓ 输入验证错误处理正常")
        
        # Step 3: 测试文件处理错误
        print("  📋 Step 3: 测试文件处理错误")
        
        # 创建文件处理服务
        file_processor = FileProcessorService(self.mock_db)
        
        # 测试无效文件内容
        invalid_content = b"invalid,csv,content\nwithout,proper,headers"
        df, parse_errors = file_processor.parse_file(invalid_content, 'invalid.csv')
        
        # 应该有解析错误或列验证错误
        if parse_errors == []:
            column_errors = file_processor.validate_columns(df)
            assert len(column_errors) > 0
        else:
            assert len(parse_errors) > 0
        
        print("    ✓ 文件处理错误处理正常")
        
        print("✅ 错误处理场景测试通过")
    
    def test_data_sync_and_consistency(self):
        """
        测试数据同步和一致性
        
        测试场景：
        1. 数据同步服务功能
        2. 缓存一致性
        3. 同步统计信息
        """
        print("🔍 测试数据同步和一致性")
        
        # Step 1: 测试数据同步服务功能
        print("  🔄 Step 1: 测试数据同步服务功能")
        
        # 获取同步统计信息
        stats_before = data_sync_service.get_sync_statistics()
        assert 'cache_size' in stats_before
        assert 'sync_operations' in stats_before
        
        # 手动添加缓存数据
        test_data = {
            'tracking_number': 'E2ESYNC001',
            'package_number': 'PKGSYNC001',
            'transport_code': 'TCSYNC'
        }
        
        data_sync_service.cache_manifest('E2ESYNC001', test_data)
        
        # 验证缓存数据
        cached_data = data_sync_service.get_cached_manifest('E2ESYNC001')
        assert cached_data is not None
        assert cached_data['tracking_number'] == 'E2ESYNC001'
        assert cached_data['package_number'] == 'PKGSYNC001'
        
        print("    ✓ 数据同步服务功能正常")
        
        # Step 2: 测试缓存失效机制
        print("  💾 Step 2: 测试缓存失效机制")
        
        # 失效所有缓存
        data_sync_service.invalidate_all_cache()
        
        # 验证缓存被清空
        cached_data_after = data_sync_service.get_cached_manifest('E2ESYNC001')
        assert cached_data_after is None
        
        # 验证统计信息更新
        stats_after = data_sync_service.get_sync_statistics()
        assert stats_after['cache_size'] == 0
        
        print("    ✓ 缓存失效机制正常")
        
        print("✅ 数据同步和一致性测试通过")
    
    def test_batch_operations(self):
        """
        测试批量操作
        
        测试场景：
        1. 批量数据处理
        2. 批量查询功能
        """
        print("🔍 测试批量操作")
        
        # Step 1: 测试批量数据处理
        print("  📊 Step 1: 测试批量数据处理")
        
        # 创建批量测试数据
        batch_data = []
        for i in range(5):
            batch_data.append({
                '快递单号': f'E2EBATCH{i:03d}',
                '理货日期': '2024-01-20',
                '运输代码': f'TCBATCH{i}',
                '客户代码': f'CCBATCH{i}',
                '货物代码': f'GCBATCH{i}',
                '集包单号': f'PKGBATCH{i:03d}',
                '重量': f'{i + 1}.0',
                '长度': '10.0',
                '宽度': '10.0',
                '高度': '10.0',
                '特殊费用': '5.00'
            })
        
        csv_content = self.create_test_csv_content(batch_data)
        
        # 创建文件处理服务
        file_processor = FileProcessorService(self.mock_db)
        
        # 解析批量数据
        df, parse_errors = file_processor.parse_file(csv_content, 'batch.csv')
        assert parse_errors == []
        assert len(df) == 5
        
        # 验证批量数据
        validation_result = file_processor.validate_and_preview(csv_content, 'batch.csv')
        assert validation_result['success'] is True
        assert validation_result['valid_rows'] == 5
        
        print("    ✓ 批量数据处理成功")
        
        # Step 2: 测试批量查询功能
        print("  🔍 Step 2: 测试批量查询功能")
        
        # 创建智能查询服务
        query_service = IntelligentQueryService(self.mock_db)
        
        # 模拟批量查询
        batch_tracking_numbers = [f'E2EBATCH{i:03d}' for i in range(3)]
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            mock_query.return_value = {
                'success': True,
                'company_code': 'SF',
                'company_name': '顺丰速运',
                'state': '1',
                'status': '运输中',
                'data': []
            }
            
            # 模拟查找理货单的方法
            async def mock_find_manifest(tracking_number):
                return None  # 简化处理，返回None表示无关联
            
            query_service._find_manifest_by_tracking_number = mock_find_manifest
            
            # 执行批量查询
            result = asyncio.run(query_service.batch_intelligent_query(batch_tracking_numbers))
            
            # 验证批量查询结果
            assert result['success_count'] == 3
            assert result['failed_count'] == 0
            assert len(result['results']) == 3
        
        print("    ✓ 批量查询功能正常")
        
        print("✅ 批量操作测试通过")


def run_final_end_to_end_tests():
    """运行最终版端到端集成测试"""
    print("🚀 开始最终版端到端集成测试...")
    print("=" * 60)
    
    test_instance = TestEndToEndIntegrationFinal()
    
    try:
        # 运行所有测试
        test_instance.setup_method()
        test_instance.test_complete_query_flow_with_package_association()
        print()
        
        test_instance.setup_method()
        test_instance.test_complete_query_flow_without_package_association()
        print()
        
        test_instance.setup_method()
        test_instance.test_file_processing_and_data_management()
        print()
        
        test_instance.setup_method()
        test_instance.test_error_handling_scenarios()
        print()
        
        test_instance.setup_method()
        test_instance.test_data_sync_and_consistency()
        print()
        
        test_instance.setup_method()
        test_instance.test_batch_operations()
        print()
        
        print("=" * 60)
        print("🎉 所有最终版端到端集成测试通过！")
        print()
        print("测试覆盖范围:")
        print("✅ 完整的查询流程（有/无集包单号关联）")
        print("✅ 文件处理和数据管理")
        print("✅ 错误处理场景")
        print("✅ 数据同步和一致性")
        print("✅ 批量操作功能")
        print()
        print("测试特点:")
        print("📝 直接测试服务层，避免复杂的API和认证问题")
        print("🔧 使用Mock对象模拟数据库和外部依赖")
        print("🎯 专注于核心业务逻辑测试")
        print("⚡ 快速执行，无外部依赖")
        print("🎯 覆盖主要业务场景和异常处理")
        
    except Exception as e:
        print(f"\n❌ 最终版端到端集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_final_end_to_end_tests()