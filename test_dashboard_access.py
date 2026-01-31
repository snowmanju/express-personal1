"""
测试仪表板页面访问
"""
import requests

def test_dashboard_access():
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试仪表板页面访问")
    print("=" * 60)
    
    # 1. 测试直接访问仪表板
    print("\n1. 测试直接访问仪表板...")
    dashboard_url = f"{base_url}/admin/dashboard.html"
    
    try:
        response = requests.get(dashboard_url, allow_redirects=False)
        print(f"   状态码: {response.status_code}")
        print(f"   内容长度: {len(response.text)} 字节")
        
        if response.status_code == 200:
            print(f"   ✓ 仪表板可以直接访问")
            
            # 检查关键内容
            if "管理后台" in response.text:
                print(f"   ✓ 包含标题")
            if "admin-dashboard.js" in response.text:
                print(f"   ✓ 引用了JavaScript文件")
            if "bootstrap" in response.text:
                print(f"   ✓ 引用了Bootstrap")
                
        elif response.status_code == 302 or response.status_code == 301:
            print(f"   ! 页面重定向到: {response.headers.get('Location')}")
        else:
            print(f"   ✗ 无法访问: {response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    # 2. 测试JavaScript文件
    print("\n2. 测试JavaScript文件...")
    js_url = f"{base_url}/admin/js/admin-dashboard.js"
    
    try:
        response = requests.get(js_url)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ JavaScript文件可访问")
            print(f"   文件大小: {len(response.text)} 字节")
            
            # 检查关键函数
            if "checkAuth" in response.text:
                print(f"   ✓ 包含checkAuth函数")
            if "handleLogin" in response.text:
                print(f"   ✓ 包含handleLogin函数")
            if "/admin/dashboard.html" in response.text:
                print(f"   ✓ 包含正确的跳转路径")
            if "/admin/login.html" in response.text:
                print(f"   ✓ 包含正确的登录页路径")
        else:
            print(f"   ✗ 无法访问JavaScript文件")
            
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    # 3. 测试登录页面
    print("\n3. 测试登录页面...")
    login_url = f"{base_url}/admin/login.html"
    
    try:
        response = requests.get(login_url)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ 登录页面可访问")
            
            # 检查跳转代码
            if "window.location.href = '/admin/dashboard.html'" in response.text:
                print(f"   ✓ 包含正确的跳转代码")
            else:
                print(f"   ! 跳转代码可能不正确")
                
            if "setTimeout" in response.text:
                print(f"   ✓ 包含延迟跳转逻辑")
                
        else:
            print(f"   ✗ 无法访问登录页面")
            
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 在浏览器中打开: http://localhost:8000/admin/login_debug.html")
    print("2. 使用 admin/admin123 登录")
    print("3. 查看调试日志，了解跳转过程")
    print("4. 打开浏览器开发者工具（F12）查看控制台错误")
    print()

if __name__ == "__main__":
    test_dashboard_access()
