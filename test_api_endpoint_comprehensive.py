"""
综合测试快递查询API端点功能
Comprehensive Test for Tracking API Endpoint Functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from app.api.v1.tracking import router
from fastapi import FastAPI
import json

# 创建测试应用
app = FastAPI()
app.include_router(router, prefix="/tracking")

client = TestClient(app)


def test_api_endpoint_structure():
    """测试API端点结构和响应格式"""
    
    # 模拟数据库会话
    with patch('app.api.v1.tracking.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # 模拟智能查询服务
        with patch('app.api.v1.tracking.IntelligentQueryService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # 模拟成功查询结果
            mock_service.query_tracking.return_value = {
                "success": True,
                "original_tracking_number": "TEST123456789",
                "cleaned_tracking_number": "TEST123456789",
                "query_tracking_number": "PKG123456789",
                "query_type": "package",
                "has_package_association": True,
                "manifest_info": {
                    "id": 1,
                    "tracking_number": "TEST123456789",
                    "package_number": "PKG123456789"
                },
                "tracking_info": {
                    "company_code": "sto",
                    "company_name": "申通快递",
                    "status": "在途中",
                    "tracks": [
                        {
                            "time": "2024-01-01 10:00:00",
                            "location": "北京",
                            "description": "快件已发出"
                        }
                    ]
                },
                "error": None,
                "query_time": 1766851905
            }
            
            # 测试POST /tracking/query端点
            response = client.post("/tracking/query", json={
                "tracking_number": "TEST123456789"
            })
            
            print(f"Query endpoint status: {response.status_code}")
            print(f"Query response: {response.json()}")
            
            assert response.status_code == 200
            data = response.json()
            
            # 验证响应结构
            assert data["success"] is True
            assert data["original_tracking_number"] == "TEST123456789"
            assert data["query_tracking_number"] == "PKG123456789"
            assert data["query_type"] == "package"
            assert data["has_package_association"] is True
            assert data["manifest_info"] is not None
            assert data["tracking_info"] is not None
            assert data["error"] is None
            assert data["query_time"] == 1766851905
            
            # 验证智能查询服务被正确调用
            mock_service.query_tracking.assert_called_once_with(
                tracking_number="TEST123456789",
                company_code="auto",
                phone=None
            )


def test_api_error_handling():
    """测试API错误处理"""
    
    with patch('app.api.v1.tracking.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch('app.api.v1.tracking.IntelligentQueryService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # 模拟查询失败结果
            mock_service.query_tracking.return_value = {
                "success": False,
                "original_tracking_number": "INVALID123",
                "cleaned_tracking_number": "INVALID123",
                "query_tracking_number": "INVALID123",
                "query_type": "original",
                "has_package_association": False,
                "manifest_info": None,
                "tracking_info": None,
                "error": "输入验证失败: 快递单号格式不正确",
                "query_time": 1766851905
            }
            
            response = client.post("/tracking/query", json={
                "tracking_number": "INVALID123"
            })
            
            print(f"Error handling status: {response.status_code}")
            print(f"Error response: {response.json()}")
            
            assert response.status_code == 200  # API层面成功，业务层面失败
            data = response.json()
            
            assert data["success"] is False
            assert data["error"] == "输入验证失败: 快递单号格式不正确"
            assert data["tracking_info"] is None


def test_batch_query_endpoint():
    """测试批量查询端点"""
    
    with patch('app.api.v1.tracking.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        with patch('app.api.v1.tracking.IntelligentQueryService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # 模拟批量查询结果
            mock_service.batch_intelligent_query.return_value = {
                "total": 2,
                "success_count": 1,
                "failed_count": 1,
                "results": [
                    {
                        "success": True,
                        "original_tracking_number": "TEST123456789",
                        "query_tracking_number": "PKG123456789",
                        "query_type": "package"
                    },
                    {
                        "success": False,
                        "original_tracking_number": "INVALID123",
                        "query_tracking_number": "INVALID123",
                        "query_type": "original",
                        "error": "查询失败"
                    }
                ]
            }
            
            response = client.post("/tracking/batch-query", json={
                "tracking_numbers": ["TEST123456789", "INVALID123"]
            })
            
            print(f"Batch query status: {response.status_code}")
            print(f"Batch response: {response.json()}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 2
            assert data["success_count"] == 1
            assert data["failed_count"] == 1
            assert len(data["results"]) == 2


def test_validation_endpoint():
    """测试验证端点"""
    
    with patch('app.api.v1.tracking.validate_tracking_number') as mock_validate:
        # 模拟验证成功
        mock_validate.return_value = MagicMock(
            is_valid=True,
            cleaned_value="TEST123456789",
            errors=[]
        )
        
        response = client.get("/tracking/validate/TEST123456789")
        
        print(f"Validation status: {response.status_code}")
        print(f"Validation response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tracking_number"] == "TEST123456789"
        assert data["is_valid"] is True
        assert data["cleaned_value"] == "TEST123456789"
        assert data["errors"] == []


if __name__ == "__main__":
    print("Testing API endpoint structure...")
    test_api_endpoint_structure()
    print("✓ API endpoint structure test passed")
    
    print("\nTesting API error handling...")
    test_api_error_handling()
    print("✓ API error handling test passed")
    
    print("\nTesting batch query endpoint...")
    test_batch_query_endpoint()
    print("✓ Batch query endpoint test passed")
    
    print("\nTesting validation endpoint...")
    test_validation_endpoint()
    print("✓ Validation endpoint test passed")
    
    print("\n🎉 All comprehensive API tests passed!")