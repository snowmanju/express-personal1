"""
基础认证功能测试
Basic Authentication Functionality Test
"""

def test_auth_imports():
    """测试认证模块导入"""
    try:
        from app.services.auth_service import auth_service
        from app.services.session_service import session_service
        from app.schemas.auth import LoginRequest, LoginResponse
        from app.core.auth import get_current_user
        print("✓ 所有认证模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_auth_schemas():
    """测试认证模式定义"""
    try:
        from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
        
        # 测试登录请求模式
        login_req = LoginRequest(username="test", password="test123")
        assert login_req.username == "test"
        assert login_req.password == "test123"
        
        print("✓ 认证模式定义正确")
        return True
    except Exception as e:
        print(f"✗ 认证模式测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始基础认证功能测试...")
    
    test_results = []
    test_results.append(test_auth_imports())
    test_results.append(test_auth_schemas())
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有基础认证功能测试通过")
    else:
        print("✗ 部分测试失败")