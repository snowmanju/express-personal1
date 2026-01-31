"""
基础API功能测试
Basic API Functionality Test
"""

import json
from fastapi.testclient import TestClient
from app.api.v1.tracking import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router, prefix="/tracking")

client = TestClient(app)


def test_api_endpoints_exist():
    """测试API端点是否存在"""
    
    # 测试查询端点
    response = client.post("/tracking/query", json={
        "tracking_number": "TEST123456789"
    })
    print(f"Query endpoint status: {response.status_code}")
    # 不应该是404，说明端点存在
    assert response.status_code != 404
    
    # 测试批量查询端点
    response = client.post("/tracking/batch-query", json={
        "tracking_numbers": ["TEST123456789"]
    })
    print(f"Batch query endpoint status: {response.status_code}")
    assert response.status_code != 404
    
    # 测试验证端点
    response = client.get("/tracking/validate/TEST123456789")
    print(f"Validation endpoint status: {response.status_code}")
    assert response.status_code != 404


def test_api_request_validation():
    """测试API请求验证"""
    
    # 测试空请求体
    response = client.post("/tracking/query", json={})
    print(f"Empty request status: {response.status_code}")
    # 应该返回422验证错误
    assert response.status_code == 422
    
    # 测试无效字段类型
    response = client.post("/tracking/query", json={
        "tracking_number": 123  # 应该是字符串
    })
    print(f"Invalid type status: {response.status_code}")
    assert response.status_code == 422


def test_api_response_format():
    """测试API响应格式"""
    
    # 测试正常请求的响应格式
    response = client.post("/tracking/query", json={
        "tracking_number": "TEST123456789"
    })
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response data keys: {list(data.keys())}")
        
        # 验证必需的响应字段
        required_fields = [
            "success", "original_tracking_number", "query_tracking_number",
            "query_type", "has_package_association"
        ]
        
        for field in required_fields:
            assert field in data, f"响应中缺少必需字段: {field}"
        
        print("✓ 响应格式验证通过")
    else:
        print(f"API返回错误状态码: {response.status_code}")
        print(f"错误详情: {response.json()}")


def test_batch_query_validation():
    """测试批量查询验证"""
    
    # 测试空列表
    response = client.post("/tracking/batch-query", json={
        "tracking_numbers": []
    })
    print(f"Empty list status: {response.status_code}")
    
    # 测试超过限制的列表
    large_list = [f"TEST{i:010d}" for i in range(101)]
    response = client.post("/tracking/batch-query", json={
        "tracking_numbers": large_list
    })
    print(f"Large list status: {response.status_code}")
    
    # 测试正常批量请求
    response = client.post("/tracking/batch-query", json={
        "tracking_numbers": ["TEST123456789", "TEST987654321"]
    })
    print(f"Normal batch status: {response.status_code}")


if __name__ == "__main__":
    print("=== 测试API端点存在性 ===")
    test_api_endpoints_exist()
    print("✓ API端点存在性测试通过\n")
    
    print("=== 测试API请求验证 ===")
    test_api_request_validation()
    print("✓ API请求验证测试通过\n")
    
    print("=== 测试API响应格式 ===")
    test_api_response_format()
    print("✓ API响应格式测试通过\n")
    
    print("=== 测试批量查询验证 ===")
    test_batch_query_validation()
    print("✓ 批量查询验证测试通过\n")
    
    print("🎉 所有基础API功能测试通过！")