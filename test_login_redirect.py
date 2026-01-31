"""
测试登录后跳转到仪表板
Test login redirect to dashboard
"""

import requests
import time

def test_login_and_redirect():
    """测试登录和跳转功能"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试登录后跳转功能")
    print("=" * 60)
    
    # 1. 测试登录API
    print("\n1. 测试登录API...")
    login_url = f"{base_url}/api/v1/admin/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 登录成功")
            print(f"   Token: {data.get('access_token', '')[:50]}...")
            token = data.get('access_token')
        else:
            print(f"   ✗ 登录失败: {response.text}")
            return
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
        return
    
    # 2. 测试验证token
    print("\n2. 测试验证token...")
    auth_url = f"{base_url}/api/v1/admin/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(auth_url, headers=headers)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✓ Token验证成功")
            print(f"   用户名: {user_data.get('username')}")
        else:
            print(f"   ✗ Token验证失败: {response.text}")
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    # 3. 测试访问仪表板页面
    print("\n3. 测试访问仪表板页面...")
    dashboard_url = f"{base_url}/admin/dashboard.html"
    
    try:
        response = requests.get(dashboard_url)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ 仪表板页面可访问")
            print(f"   页面大小: {len(response.text)} 字节")
            
            # 检查页面是否包含关键元素
            if "管理后台" in response.text:
                print(f"   ✓ 页面包含正确的标题")
            if "admin-dashboard.js" in response.text:
                print(f"   ✓ 页面引用了JavaScript文件")
        else:
            print(f"   ✗ 无法访问仪表板: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    # 4. 测试访问登录页面
    print("\n4. 测试访问登录页面...")
    login_page_url = f"{base_url}/admin/login.html"
    
    try:
        response = requests.get(login_page_url)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ 登录页面可访问")
            print(f"   页面大小: {len(response.text)} 字节")
            
            # 检查页面是否包含关键元素
            if "员工登录" in response.text:
                print(f"   ✓ 页面包含正确的标题")
            if "/admin/dashboard.html" in response.text:
                print(f"   ✓ 页面包含正确的跳转路径")
        else:
            print(f"   ✗ 无法访问登录页面: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n请在浏览器中测试:")
    print(f"1. 访问: {base_url}/admin/login.html")
    print(f"2. 使用用户名: admin, 密码: admin123 登录")
    print(f"3. 登录成功后应该自动跳转到: {base_url}/admin/dashboard.html")
    print()

if __name__ == "__main__":
    test_login_and_redirect()
