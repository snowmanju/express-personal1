"""
端到端集成测试 (End-to-End Integration Tests)
测试完整的查询流程（前台到后台）、文件上传和管理流程、API集成和错误处理

Feature: express-tracking-website, Task 12.1: 编写端到端集成测试
"""

import pytest
import asyncio
import json
import io
import csv
from datetime import datetime, date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, AsyncMock, patch

# Import application components
from app.main import app
from app.core.database import get_db, engine
from app.models.cargo_manifest import CargoManifest
from app.models.admin_user import AdminUser
from app.services.auth_service import auth_service
from app.services.intelligent_query_service import IntelligentQueryService
from app.services.manifest_service import ManifestService
from app.services.file_processor_service import FileProcessorService
from app.services.data_sync_service import data_sync_service


class TestEndToEndIntegration:
    """端到端集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.db = next(get_db())
        
        # 清理测试数据
        self.cleanup_test_data()
        
        # 创建测试管理员用户
        self.admin_user = self.create_test_admin()
        self.admin_token = self.get_admin_token()
        
        # 清理缓存和同步状态
        data_sync_service.invalidate_all_cache()
        data_sync_service.clear_pending_sync_operations()
        
        yield
        
        # 测试后清理
        self.cleanup_test_data()
        self.db.close()
    
    def cleanup_test_data(self):
        """清理测试数据"""
        try:
            # 清理理货单测试数据
            self.db.query(CargoManifest).filter(
                CargoManifest.tracking_number.like('E2E_TEST_%')
            ).delete()
            
            # 清理测试管理员用户
            self.db.query(AdminUser).filter(
                AdminUser.username == 'e2e_test_admin'
            ).delete()
            
            self.db.commit()
        except Exception as e:
            print(f"清理测试数据时出错: {e}")
            self.db.rollback()
    
    def create_test_admin(self):
        """创建测试管理员用户"""
        try:
            existing_user = self.db.query(AdminUser).filter(
                AdminUser.username == 'e2e_test_admin'
            ).first()
            
            if existing_user:
                return existing_user
            
            user = auth_service.create_user(self.db, 'e2e_test_admin', 'test_password_123')
            return user
        except Exception as e:
            print(f"创建测试管理员用户失败: {e}")
            return None
    
    def get_admin_token(self):
        """获取管理员认证令牌"""
        if not self.admin_user:
            return None
        
        response = self.client.post('/api/v1/admin/auth/login', json={
            'username': 'e2e_test_admin',
            'password': 'test_password_123'
        })
        
        if response.status_code == 200:
            return response.json()['access_token']
        return None
    
    def create_test_csv_file(self, data):
        """创建测试CSV文件"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'tracking_number', 'manifest_date', 'transport_code', 
            'customer_code', 'goods_code', 'package_number', 
            'weight', 'length', 'width', 'height', 'special_fee'
        ])
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return io.BytesIO(csv_content.encode('utf-8'))
    
    def test_complete_frontend_to_backend_query_flow(self):
        """
        测试完整的查询流程（前台到后台）
        
        测试场景：
        1. 管理员上传理货单文件
        2. 前台用户查询快递单号
        3. 系统智能判断并返回结果
        4. 验证数据同步和缓存机制
        """
        print("🔍 测试完整的查询流程（前台到后台）")
        
        # Step 1: 管理员上传理货单文件
        print("  📤 Step 1: 管理员上传理货单文件")
        
        test_manifest_data = [
            {
                'tracking_number': 'E2E_TEST_001',
                'manifest_date': '2024-01-15',
                'transport_code': 'TC001',
                'customer_code': 'CC001',
                'goods_code': 'GC001',
                'package_number': 'PKG_E2E_001',
                'weight': '2.5',
                'length': '30.0',
                'width': '20.0',
                'height': '10.0',
                'special_fee': '15.50'
            },
            {
                'tracking_number': 'E2E_TEST_002',
                'manifest_date': '2024-01-15',
                'transport_code': 'TC002',
                'customer_code': 'CC002',
                'goods_code': 'GC002',
                'package_number': '',  # 无集包单号
                'weight': '1.2',
                'length': '25.0',
                'width': '15.0',
                'height': '8.0',
                'special_fee': '10.00'
            }
        ]
        
        csv_file = self.create_test_csv_file(test_manifest_data)
        
        # 上传文件
        upload_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('test_manifest.csv', csv_file, 'text/csv')},
            data={'preview_only': 'false'}
        )
        
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        assert upload_result['success'] is True
        assert upload_result['statistics']['inserted'] == 2
        
        print("    ✓ 理货单文件上传成功")
        
        # Step 2: 验证数据已保存到数据库
        print("  🗄️ Step 2: 验证数据已保存到数据库")
        
        manifest1 = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'E2E_TEST_001'
        ).first()
        
        manifest2 = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'E2E_TEST_002'
        ).first()
        
        assert manifest1 is not None
        assert manifest1.package_number == 'PKG_E2E_001'
        assert manifest2 is not None
        assert manifest2.package_number is None or manifest2.package_number == ''
        
        print("    ✓ 数据已正确保存到数据库")
        
        # Step 3: 前台查询有集包单号的快递
        print("  🔍 Step 3: 前台查询有集包单号的快递")
        
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
            
            query_response = self.client.post('/api/v1/tracking/query', json={
                'tracking_number': 'E2E_TEST_001'
            })
            
            assert query_response.status_code == 200
            query_result = query_response.json()
            
            # 验证智能查询结果
            assert query_result['success'] is True
            assert query_result['original_tracking_number'] == 'E2E_TEST_001'
            assert query_result['query_tracking_number'] == 'PKG_E2E_001'  # 使用集包单号查询
            assert query_result['query_type'] == 'package'
            assert query_result['has_package_association'] is True
            
            # 验证理货单信息
            assert query_result['manifest_info'] is not None
            assert query_result['manifest_info']['transport_code'] == 'TC001'
            assert query_result['manifest_info']['customer_code'] == 'CC001'
            
            # 验证快递信息
            assert query_result['tracking_info'] is not None
            assert query_result['tracking_info']['company_name'] == '顺丰速运'
            
            # 验证API调用使用了集包单号
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]
            assert call_args['tracking_number'] == 'PKG_E2E_001'
        
        print("    ✓ 有集包单号的快递查询成功")
        
        # Step 4: 前台查询无集包单号的快递
        print("  🔍 Step 4: 前台查询无集包单号的快递")
        
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
            
            query_response = self.client.post('/api/v1/tracking/query', json={
                'tracking_number': 'E2E_TEST_002'
            })
            
            assert query_response.status_code == 200
            query_result = query_response.json()
            
            # 验证智能查询结果
            assert query_result['success'] is True
            assert query_result['original_tracking_number'] == 'E2E_TEST_002'
            assert query_result['query_tracking_number'] == 'E2E_TEST_002'  # 使用原单号查询
            assert query_result['query_type'] == 'original'
            assert query_result['has_package_association'] is False
            
            # 验证API调用使用了原单号
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]
            assert call_args['tracking_number'] == 'E2E_TEST_002'
        
        print("    ✓ 无集包单号的快递查询成功")
        
        # Step 5: 验证数据同步机制
        print("  🔄 Step 5: 验证数据同步机制")
        
        # 获取同步统计信息
        sync_stats = data_sync_service.get_sync_statistics()
        assert sync_stats['sync_operations'] > 0
        
        # 验证缓存中有数据
        cached_manifest1 = data_sync_service.get_cached_manifest('E2E_TEST_001')
        assert cached_manifest1 is not None
        assert cached_manifest1['package_number'] == 'PKG_E2E_001'
        
        print("    ✓ 数据同步机制工作正常")
        
        print("✅ 完整的查询流程测试通过")
    
    def test_file_upload_and_management_flow(self):
        """
        测试文件上传和管理流程
        
        测试场景：
        1. 文件格式验证
        2. 数据预览功能
        3. 增量更新机制
        4. 理货单管理操作（搜索、编辑、删除）
        """
        print("🔍 测试文件上传和管理流程")
        
        # Step 1: 测试文件格式验证
        print("  📋 Step 1: 测试文件格式验证")
        
        # 测试不支持的文件格式
        invalid_file = io.BytesIO(b"invalid file content")
        upload_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('test.txt', invalid_file, 'text/plain')},
            data={'preview_only': 'false'}
        )
        
        assert upload_response.status_code == 400
        assert '不支持的文件格式' in upload_response.json()['detail']
        
        print("    ✓ 文件格式验证正常")
        
        # Step 2: 测试数据预览功能
        print("  👁️ Step 2: 测试数据预览功能")
        
        preview_data = [
            {
                'tracking_number': 'E2E_PREVIEW_001',
                'manifest_date': '2024-01-16',
                'transport_code': 'TC_PREVIEW',
                'customer_code': 'CC_PREVIEW',
                'goods_code': 'GC_PREVIEW',
                'package_number': 'PKG_PREVIEW_001',
                'weight': '3.0',
                'length': '40.0',
                'width': '30.0',
                'height': '20.0',
                'special_fee': '25.00'
            }
        ]
        
        csv_file = self.create_test_csv_file(preview_data)
        
        preview_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('preview.csv', csv_file, 'text/csv')},
            data={'preview_only': 'true'}
        )
        
        assert preview_response.status_code == 200
        preview_result = preview_response.json()
        assert preview_result['success'] is True
        assert len(preview_result['preview_data']) == 1
        assert preview_result['preview_data'][0]['tracking_number'] == 'E2E_PREVIEW_001'
        
        # 验证数据未保存到数据库（仅预览）
        preview_manifest = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'E2E_PREVIEW_001'
        ).first()
        assert preview_manifest is None
        
        print("    ✓ 数据预览功能正常")
        
        # Step 3: 测试增量更新机制
        print("  🔄 Step 3: 测试增量更新机制")
        
        # 首次上传
        initial_data = [
            {
                'tracking_number': 'E2E_UPDATE_001',
                'manifest_date': '2024-01-17',
                'transport_code': 'TC_INITIAL',
                'customer_code': 'CC_INITIAL',
                'goods_code': 'GC_INITIAL',
                'package_number': 'PKG_INITIAL_001',
                'weight': '1.0',
                'length': '10.0',
                'width': '10.0',
                'height': '10.0',
                'special_fee': '5.00'
            }
        ]
        
        csv_file = self.create_test_csv_file(initial_data)
        
        initial_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('initial.csv', csv_file, 'text/csv')},
            data={'preview_only': 'false'}
        )
        
        assert initial_response.status_code == 200
        initial_result = initial_response.json()
        assert initial_result['statistics']['inserted'] == 1
        assert initial_result['statistics']['updated'] == 0
        
        # 更新上传（相同快递单号，不同数据）
        updated_data = [
            {
                'tracking_number': 'E2E_UPDATE_001',  # 相同快递单号
                'manifest_date': '2024-01-17',
                'transport_code': 'TC_UPDATED',  # 更新的运输代码
                'customer_code': 'CC_UPDATED',   # 更新的客户代码
                'goods_code': 'GC_UPDATED',      # 更新的货物代码
                'package_number': 'PKG_UPDATED_001',  # 更新的集包单号
                'weight': '2.0',  # 更新的重量
                'length': '20.0',
                'width': '20.0',
                'height': '20.0',
                'special_fee': '10.00'
            }
        ]
        
        csv_file = self.create_test_csv_file(updated_data)
        
        update_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('updated.csv', csv_file, 'text/csv')},
            data={'preview_only': 'false'}
        )
        
        assert update_response.status_code == 200
        update_result = update_response.json()
        assert update_result['statistics']['inserted'] == 0
        assert update_result['statistics']['updated'] == 1
        
        # 验证数据已更新
        updated_manifest = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'E2E_UPDATE_001'
        ).first()
        
        assert updated_manifest is not None
        assert updated_manifest.transport_code == 'TC_UPDATED'
        assert updated_manifest.customer_code == 'CC_UPDATED'
        assert updated_manifest.package_number == 'PKG_UPDATED_001'
        assert float(updated_manifest.weight) == 2.0
        
        print("    ✓ 增量更新机制正常")
        
        # Step 4: 测试理货单管理操作
        print("  📊 Step 4: 测试理货单管理操作")
        
        # 4.1 搜索功能
        search_response = self.client.get(
            '/api/v1/admin/manifest/search?q=E2E_UPDATE&page=1&limit=10',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result['success'] is True
        assert len(search_result['data']) >= 1
        
        manifest_id = search_result['data'][0]['id']
        
        print("    ✓ 搜索功能正常")
        
        # 4.2 获取理货单详情
        detail_response = self.client.get(
            f'/api/v1/admin/manifest/{manifest_id}',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        assert detail_response.status_code == 200
        detail_result = detail_response.json()
        assert detail_result['success'] is True
        assert detail_result['data']['tracking_number'] == 'E2E_UPDATE_001'
        
        print("    ✓ 获取详情功能正常")
        
        # 4.3 编辑理货单
        edit_data = {
            'tracking_number': 'E2E_UPDATE_001',
            'manifest_date': '2024-01-17',
            'transport_code': 'TC_EDITED',
            'customer_code': 'CC_EDITED',
            'goods_code': 'GC_EDITED',
            'package_number': 'PKG_EDITED_001',
            'weight': 3.0,
            'length': 30.0,
            'width': 30.0,
            'height': 30.0,
            'special_fee': 15.00
        }
        
        edit_response = self.client.put(
            f'/api/v1/admin/manifest/{manifest_id}',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            json=edit_data
        )
        
        assert edit_response.status_code == 200
        edit_result = edit_response.json()
        assert edit_result['success'] is True
        assert edit_result['data']['transport_code'] == 'TC_EDITED'
        
        print("    ✓ 编辑功能正常")
        
        # 4.4 删除理货单
        delete_response = self.client.delete(
            f'/api/v1/admin/manifest/{manifest_id}',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        assert delete_response.status_code == 200
        delete_result = delete_response.json()
        assert delete_result['success'] is True
        
        # 验证已删除
        deleted_manifest = self.db.query(CargoManifest).filter(
            CargoManifest.id == manifest_id
        ).first()
        assert deleted_manifest is None
        
        print("    ✓ 删除功能正常")
        
        print("✅ 文件上传和管理流程测试通过")
    
    def test_api_integration_and_error_handling(self):
        """
        测试API集成和错误处理
        
        测试场景：
        1. 快递100 API集成测试
        2. 网络错误处理
        3. 认证错误处理
        4. 输入验证错误处理
        5. 系统异常处理
        """
        print("🔍 测试API集成和错误处理")
        
        # Step 1: 快递100 API集成测试
        print("  🌐 Step 1: 快递100 API集成测试")
        
        # 创建测试理货单
        test_manifest = CargoManifest(
            tracking_number='E2E_API_001',
            manifest_date=date(2024, 1, 18),
            transport_code='TC_API',
            customer_code='CC_API',
            goods_code='GC_API',
            package_number='PKG_API_001',
            weight=Decimal('1.5')
        )
        
        self.db.add(test_manifest)
        self.db.commit()
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            # 测试成功响应
            mock_query.return_value = {
                'success': True,
                'company_code': 'SF',
                'company_name': '顺丰速运',
                'state': '3',
                'status': '已签收',
                'data': [
                    {
                        'time': '2024-01-18 16:00:00',
                        'location': '上海市',
                        'context': '快件已签收'
                    }
                ]
            }
            
            api_response = self.client.post('/api/v1/tracking/query', json={
                'tracking_number': 'E2E_API_001'
            })
            
            assert api_response.status_code == 200
            api_result = api_response.json()
            assert api_result['success'] is True
            assert api_result['tracking_info']['state'] == '3'
            
            # 验证API调用参数
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]
            assert call_args['tracking_number'] == 'PKG_API_001'  # 使用集包单号
        
        print("    ✓ API集成测试正常")
        
        # Step 2: 网络错误处理
        print("  🌐 Step 2: 网络错误处理")
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            # 模拟网络错误
            mock_query.side_effect = Exception("Network connection failed")
            
            network_error_response = self.client.post('/api/v1/tracking/query', json={
                'tracking_number': 'E2E_API_001'
            })
            
            assert network_error_response.status_code == 200
            network_error_result = network_error_response.json()
            assert network_error_result['success'] is False
            assert 'API调用失败' in network_error_result['error']
        
        print("    ✓ 网络错误处理正常")
        
        # Step 3: 认证错误处理
        print("  🔐 Step 3: 认证错误处理")
        
        # 测试无效令牌
        invalid_token_response = self.client.get(
            '/api/v1/admin/manifest/search',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        assert invalid_token_response.status_code == 401
        
        # 测试缺少令牌
        no_token_response = self.client.get('/api/v1/admin/manifest/search')
        assert no_token_response.status_code == 401
        
        print("    ✓ 认证错误处理正常")
        
        # Step 4: 输入验证错误处理
        print("  ✅ Step 4: 输入验证错误处理")
        
        # 测试无效快递单号
        invalid_input_response = self.client.post('/api/v1/tracking/query', json={
            'tracking_number': '<script>alert("xss")</script>'
        })
        
        assert invalid_input_response.status_code == 200
        invalid_input_result = invalid_input_response.json()
        assert invalid_input_result['success'] is False
        assert '输入验证失败' in invalid_input_result['error']
        
        # 测试空输入
        empty_input_response = self.client.post('/api/v1/tracking/query', json={
            'tracking_number': ''
        })
        
        assert empty_input_response.status_code == 200
        empty_input_result = empty_input_response.json()
        assert empty_input_result['success'] is False
        
        print("    ✓ 输入验证错误处理正常")
        
        # Step 5: 系统异常处理
        print("  ⚠️ Step 5: 系统异常处理")
        
        # 测试数据库连接异常
        with patch('app.services.intelligent_query_service.IntelligentQueryService._find_manifest_by_tracking_number') as mock_find:
            mock_find.side_effect = Exception("Database connection failed")
            
            db_error_response = self.client.post('/api/v1/tracking/query', json={
                'tracking_number': 'VALID_NUMBER_123'
            })
            
            assert db_error_response.status_code == 500
        
        print("    ✓ 系统异常处理正常")
        
        print("✅ API集成和错误处理测试通过")
    
    def test_batch_operations_and_performance(self):
        """
        测试批量操作和性能
        
        测试场景：
        1. 批量查询功能
        2. 批量删除功能
        3. 大文件上传处理
        4. 并发请求处理
        """
        print("🔍 测试批量操作和性能")
        
        # Step 1: 批量查询功能
        print("  📊 Step 1: 批量查询功能")
        
        # 创建多个测试理货单
        batch_manifests = []
        for i in range(5):
            manifest = CargoManifest(
                tracking_number=f'E2E_BATCH_{i:03d}',
                manifest_date=date(2024, 1, 19),
                transport_code=f'TC_BATCH_{i}',
                customer_code=f'CC_BATCH_{i}',
                goods_code=f'GC_BATCH_{i}',
                package_number=f'PKG_BATCH_{i:03d}',
                weight=Decimal(f'{i + 1}.0')
            )
            batch_manifests.append(manifest)
        
        self.db.add_all(batch_manifests)
        self.db.commit()
        
        # 测试批量查询API
        batch_tracking_numbers = [f'E2E_BATCH_{i:03d}' for i in range(3)]
        
        with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
            mock_query.return_value = {
                'success': True,
                'company_code': 'SF',
                'company_name': '顺丰速运',
                'state': '1',
                'status': '运输中',
                'data': []
            }
            
            batch_response = self.client.post('/api/v1/tracking/batch-query', json={
                'tracking_numbers': batch_tracking_numbers
            })
            
            assert batch_response.status_code == 200
            batch_result = batch_response.json()
            assert batch_result['success_count'] == 3
            assert batch_result['failed_count'] == 0
            assert len(batch_result['results']) == 3
        
        print("    ✓ 批量查询功能正常")
        
        # Step 2: 批量删除功能
        print("  🗑️ Step 2: 批量删除功能")
        
        # 获取理货单ID列表
        manifest_ids = [manifest.id for manifest in batch_manifests[:3]]
        
        batch_delete_response = self.client.request(
            'DELETE',
            '/api/v1/admin/manifest/batch',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            json=manifest_ids
        )
        
        assert batch_delete_response.status_code == 200
        batch_delete_result = batch_delete_response.json()
        assert batch_delete_result['success'] is True
        
        # 验证已删除
        remaining_count = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number.like('E2E_BATCH_%')
        ).count()
        assert remaining_count == 2  # 5 - 3 = 2
        
        print("    ✓ 批量删除功能正常")
        
        # Step 3: 大文件上传处理
        print("  📁 Step 3: 大文件上传处理")
        
        # 创建较大的测试数据集（100条记录）
        large_data = []
        for i in range(100):
            large_data.append({
                'tracking_number': f'E2E_LARGE_{i:04d}',
                'manifest_date': '2024-01-20',
                'transport_code': f'TC_LARGE_{i % 10}',
                'customer_code': f'CC_LARGE_{i % 5}',
                'goods_code': f'GC_LARGE_{i % 3}',
                'package_number': f'PKG_LARGE_{i:04d}',
                'weight': f'{(i % 10) + 1}.{i % 10}',
                'length': f'{(i % 50) + 10}.0',
                'width': f'{(i % 30) + 5}.0',
                'height': f'{(i % 20) + 3}.0',
                'special_fee': f'{(i % 100) + 1}.00'
            })
        
        large_csv_file = self.create_test_csv_file(large_data)
        
        large_upload_response = self.client.post(
            '/api/v1/admin/manifest/upload',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            files={'file': ('large_manifest.csv', large_csv_file, 'text/csv')},
            data={'preview_only': 'false'}
        )
        
        assert large_upload_response.status_code == 200
        large_upload_result = large_upload_response.json()
        assert large_upload_result['success'] is True
        assert large_upload_result['statistics']['inserted'] == 100
        
        print("    ✓ 大文件上传处理正常")
        
        # Step 4: 并发请求处理
        print("  🔄 Step 4: 并发请求处理")
        
        import threading
        import time
        
        results = []
        
        def concurrent_query(tracking_number):
            with patch('app.services.kuaidi100_client.Kuaidi100Client.query_tracking') as mock_query:
                mock_query.return_value = {
                    'success': True,
                    'company_code': 'SF',
                    'company_name': '顺丰速运',
                    'state': '1',
                    'status': '运输中',
                    'data': []
                }
                
                response = self.client.post('/api/v1/tracking/query', json={
                    'tracking_number': tracking_number
                })
                results.append(response.status_code == 200)
        
        # 创建5个并发线程
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=concurrent_query,
                args=(f'E2E_LARGE_{i:04d}',)
            )
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 验证所有请求都成功
        assert all(results)
        assert len(results) == 5
        
        # 验证响应时间合理（应该在10秒内完成）
        assert (end_time - start_time) < 10
        
        print("    ✓ 并发请求处理正常")
        
        print("✅ 批量操作和性能测试通过")
    
    def test_data_consistency_and_sync(self):
        """
        测试数据一致性和同步
        
        测试场景：
        1. 数据同步服务测试
        2. 缓存一致性测试
        3. 并发修改处理
        4. 数据完整性验证
        """
        print("🔍 测试数据一致性和同步")
        
        # Step 1: 数据同步服务测试
        print("  🔄 Step 1: 数据同步服务测试")
        
        # 创建测试理货单
        sync_manifest = CargoManifest(
            tracking_number='E2E_SYNC_001',
            manifest_date=date(2024, 1, 21),
            transport_code='TC_SYNC',
            customer_code='CC_SYNC',
            goods_code='GC_SYNC',
            package_number='PKG_SYNC_001',
            weight=Decimal('2.0')
        )
        
        self.db.add(sync_manifest)
        self.db.commit()
        
        # 验证同步统计信息
        sync_stats_before = data_sync_service.get_sync_statistics()
        
        # 触发同步操作
        sync_result = data_sync_service.force_sync_manifest('E2E_SYNC_001', self.db)
        assert sync_result['success'] is True
        
        sync_stats_after = data_sync_service.get_sync_statistics()
        assert sync_stats_after['sync_operations'] > sync_stats_before['sync_operations']
        
        print("    ✓ 数据同步服务正常")
        
        # Step 2: 缓存一致性测试
        print("  💾 Step 2: 缓存一致性测试")
        
        # 验证缓存中的数据
        cached_manifest = data_sync_service.get_cached_manifest('E2E_SYNC_001')
        assert cached_manifest is not None
        assert cached_manifest['package_number'] == 'PKG_SYNC_001'
        
        # 更新数据库中的数据
        sync_manifest.package_number = 'PKG_SYNC_001_UPDATED'
        self.db.commit()
        
        # 强制同步
        data_sync_service.force_sync_manifest('E2E_SYNC_001', self.db)
        
        # 验证缓存已更新
        updated_cached_manifest = data_sync_service.get_cached_manifest('E2E_SYNC_001')
        assert updated_cached_manifest is not None
        assert updated_cached_manifest['package_number'] == 'PKG_SYNC_001_UPDATED'
        
        print("    ✓ 缓存一致性正常")
        
        # Step 3: 并发修改处理
        print("  🔄 Step 3: 并发修改处理")
        
        import threading
        
        modification_results = []
        
        def concurrent_modification(suffix):
            try:
                # 通过API修改理货单
                edit_response = self.client.put(
                    f'/api/v1/admin/manifest/{sync_manifest.id}',
                    headers={'Authorization': f'Bearer {self.admin_token}'},
                    json={
                        'tracking_number': 'E2E_SYNC_001',
                        'manifest_date': '2024-01-21',
                        'transport_code': f'TC_SYNC_{suffix}',
                        'customer_code': f'CC_SYNC_{suffix}',
                        'goods_code': f'GC_SYNC_{suffix}',
                        'package_number': f'PKG_SYNC_001_{suffix}',
                        'weight': 2.0 + float(suffix)
                    }
                )
                modification_results.append(edit_response.status_code == 200)
            except Exception as e:
                print(f"并发修改异常: {e}")
                modification_results.append(False)
        
        # 创建3个并发修改线程
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=concurrent_modification,
                args=(str(i),)
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证至少有一个修改成功（其他可能因为并发冲突失败）
        assert any(modification_results)
        
        print("    ✓ 并发修改处理正常")
        
        # Step 4: 数据完整性验证
        print("  ✅ Step 4: 数据完整性验证")
        
        # 验证数据库中的数据完整性
        final_manifest = self.db.query(CargoManifest).filter(
            CargoManifest.tracking_number == 'E2E_SYNC_001'
        ).first()
        
        assert final_manifest is not None
        assert final_manifest.tracking_number == 'E2E_SYNC_001'
        assert final_manifest.transport_code is not None
        assert final_manifest.customer_code is not None
        assert final_manifest.goods_code is not None
        
        # 验证缓存与数据库的一致性
        final_cached_manifest = data_sync_service.get_cached_manifest('E2E_SYNC_001')
        if final_cached_manifest:
            assert final_cached_manifest['transport_code'] == final_manifest.transport_code
            assert final_cached_manifest['customer_code'] == final_manifest.customer_code
        
        print("    ✓ 数据完整性验证正常")
        
        print("✅ 数据一致性和同步测试通过")


def run_end_to_end_tests():
    """运行端到端集成测试"""
    print("🚀 开始端到端集成测试...")
    print("=" * 60)
    
    test_instance = TestEndToEndIntegration()
    
    try:
        # 设置测试环境
        test_instance.setup_method()
        
        # 运行所有测试
        test_instance.test_complete_frontend_to_backend_query_flow()
        print()
        
        test_instance.test_file_upload_and_management_flow()
        print()
        
        test_instance.test_api_integration_and_error_handling()
        print()
        
        test_instance.test_batch_operations_and_performance()
        print()
        
        test_instance.test_data_consistency_and_sync()
        print()
        
        print("=" * 60)
        print("🎉 所有端到端集成测试通过！")
        print()
        print("测试覆盖范围:")
        print("✅ 完整的查询流程（前台到后台）")
        print("✅ 文件上传和管理流程")
        print("✅ API集成和错误处理")
        print("✅ 批量操作和性能测试")
        print("✅ 数据一致性和同步测试")
        
    except Exception as e:
        print(f"\n❌ 端到端集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # 清理测试环境
        try:
            test_instance.cleanup_test_data()
        except:
            pass


if __name__ == "__main__":
    run_end_to_end_tests()