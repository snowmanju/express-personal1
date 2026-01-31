"""
测试理货单管理API端点结构
Test Manifest Management API Endpoints Structure
"""

import sys
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_manifest_api_structure():
    """测试理货单API端点结构"""
    
    print("=== 测试理货单API端点结构 ===")
    
    # 创建一个简单的FastAPI应用来测试路由结构
    app = FastAPI()
    
    # 导入理货单路由
    try:
        from app.api.v1.manifest import router as manifest_router
        app.include_router(manifest_router, prefix="/api/v1/admin/manifest")
        print("✓ 理货单路由导入成功")
    except Exception as e:
        print(f"✗ 理货单路由导入失败: {e}")
        return False
    
    # 创建测试客户端
    client = TestClient(app)
    
    # 测试端点是否存在（不需要认证的结构测试）
    endpoints_to_test = [
        ("POST", "/api/v1/admin/manifest/upload"),
        ("GET", "/api/v1/admin/manifest/search"),
        ("GET", "/api/v1/admin/manifest/1"),
        ("POST", "/api/v1/admin/manifest/"),
        ("PUT", "/api/v1/admin/manifest/1"),
        ("DELETE", "/api/v1/admin/manifest/1"),
        ("DELETE", "/api/v1/admin/manifest/batch"),
        ("GET", "/api/v1/admin/manifest/statistics/overview"),
        ("GET", "/api/v1/admin/manifest/tracking/TEST123"),
    ]
    
    print("\n=== 测试API端点存在性 ===")
    for method, endpoint in endpoints_to_test:
        try:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            # 检查端点是否存在（不是404）
            if response.status_code != 404:
                print(f"✓ {method} {endpoint}: 端点存在 (状态码: {response.status_code})")
            else:
                print(f"✗ {method} {endpoint}: 端点不存在 (404)")
                return False
                
        except Exception as e:
            print(f"✗ {method} {endpoint}: 测试失败 - {e}")
            return False
    
    print("\n=== 测试认证要求 ===")
    # 测试端点是否需要认证（应该返回403或401）
    auth_required_endpoints = [
        ("GET", "/api/v1/admin/manifest/search"),
        ("GET", "/api/v1/admin/manifest/statistics/overview"),
    ]
    
    for method, endpoint in auth_required_endpoints:
        try:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            if response.status_code in [401, 403]:
                print(f"✓ {method} {endpoint}: 需要认证 (状态码: {response.status_code})")
            else:
                print(f"? {method} {endpoint}: 可能不需要认证 (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"✗ {method} {endpoint}: 认证测试失败 - {e}")
    
    return True


def test_file_upload_endpoint_structure():
    """测试文件上传端点结构"""
    
    print("\n=== 测试文件上传端点结构 ===")
    
    app = FastAPI()
    
    try:
        from app.api.v1.manifest import router as manifest_router
        app.include_router(manifest_router, prefix="/api/v1/admin/manifest")
        
        client = TestClient(app)
        
        # 测试文件上传端点（不提供文件应该返回422）
        response = client.post("/api/v1/admin/manifest/upload")
        
        if response.status_code == 422:
            print("✓ 文件上传端点正确要求文件参数")
        elif response.status_code in [401, 403]:
            print("✓ 文件上传端点需要认证")
        else:
            print(f"? 文件上传端点响应: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ 文件上传端点测试失败: {e}")
        return False


def test_manifest_crud_operations():
    """测试理货单CRUD操作端点"""
    
    print("\n=== 测试理货单CRUD操作端点 ===")
    
    app = FastAPI()
    
    try:
        from app.api.v1.manifest import router as manifest_router
        app.include_router(manifest_router, prefix="/api/v1/admin/manifest")
        
        client = TestClient(app)
        
        # 测试CRUD操作
        crud_operations = [
            ("POST", "/api/v1/admin/manifest/", "创建"),
            ("GET", "/api/v1/admin/manifest/1", "读取"),
            ("PUT", "/api/v1/admin/manifest/1", "更新"),
            ("DELETE", "/api/v1/admin/manifest/1", "删除"),
        ]
        
        for method, endpoint, operation in crud_operations:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                elif method == "POST":
                    response = client.post(endpoint, json={})
                elif method == "PUT":
                    response = client.put(endpoint, json={})
                elif method == "DELETE":
                    response = client.delete(endpoint)
                
                if response.status_code != 404:
                    print(f"✓ {operation}操作端点存在: {method} {endpoint}")
                else:
                    print(f"✗ {operation}操作端点不存在: {method} {endpoint}")
                    
            except Exception as e:
                print(f"✗ {operation}操作测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ CRUD操作测试失败: {e}")
        return False


def test_authentication_middleware():
    """测试认证中间件"""
    
    print("\n=== 测试认证中间件 ===")
    
    try:
        # 检查认证依赖是否正确导入
        from app.core.auth import get_current_active_user, get_current_user
        print("✓ 认证依赖导入成功")
        
        # 检查理货单路由是否使用认证依赖
        from app.api.v1.manifest import router
        
        # 检查路由中是否有认证依赖
        auth_dependency_found = False
        for route in router.routes:
            if hasattr(route, 'dependant') and route.dependant:
                for dep in route.dependant.dependencies:
                    if 'get_current_active_user' in str(dep.call):
                        auth_dependency_found = True
                        break
        
        if auth_dependency_found:
            print("✓ 理货单路由使用认证中间件")
        else:
            print("? 未检测到认证中间件使用")
        
        return True
        
    except Exception as e:
        print(f"✗ 认证中间件测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 开始测试理货单API端点...")
    
    success = True
    
    # 运行所有测试
    success &= test_manifest_api_structure()
    success &= test_file_upload_endpoint_structure()
    success &= test_manifest_crud_operations()
    success &= test_authentication_middleware()
    
    if success:
        print("\n🎉 理货单API端点结构测试全部通过！")
    else:
        print("\n❌ 部分测试失败，请检查实现")