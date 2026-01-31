"""
验证API集成
Verify API Integration
"""

from app.api.v1.api import api_router
from app.api.v1 import tracking
from fastapi import FastAPI

def test_api_integration():
    """测试API集成"""
    
    # 创建测试应用
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    
    # 检查路由是否正确注册
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else [],
                'name': getattr(route, 'name', 'unknown')
            })
    
    print("注册的路由:")
    for route in routes:
        print(f"  {route['methods']} {route['path']} ({route['name']})")
    
    # 验证关键路由存在
    expected_routes = [
        ('/api/v1/tracking/query', ['POST']),
        ('/api/v1/tracking/batch-query', ['POST']),
        ('/api/v1/tracking/validate/{tracking_number}', ['GET'])
    ]
    
    for expected_path, expected_methods in expected_routes:
        found = False
        for route in routes:
            if route['path'] == expected_path:
                for method in expected_methods:
                    if method in route['methods']:
                        found = True
                        break
        
        if found:
            print(f"✓ 找到路由: {expected_methods} {expected_path}")
        else:
            print(f"✗ 未找到路由: {expected_methods} {expected_path}")
    
    print("\n路由集成验证完成!")


def test_tracking_router_structure():
    """测试tracking路由器结构"""
    
    print("\nTracking路由器结构:")
    
    # 检查tracking路由器的路由
    for route in tracking.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)} {route.path}")
    
    print("✓ Tracking路由器结构验证完成")


if __name__ == "__main__":
    test_api_integration()
    test_tracking_router_structure()