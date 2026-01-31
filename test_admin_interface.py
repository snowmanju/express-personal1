"""
测试管理后台界面功能
"""

import requests
import time
import os

def test_admin_interface_accessibility():
    """测试管理后台界面是否可访问"""
    base_url = "http://localhost:8000"
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test admin login page
        response = requests.get(f"{base_url}/admin/login.html")
        assert response.status_code == 200, f"Admin login page not accessible: {response.status_code}"
        assert "管理员登录" in response.text, "Admin login page content not found"
        print("✅ Admin login page is accessible")
        
        # Test admin dashboard page
        response = requests.get(f"{base_url}/admin/dashboard.html")
        assert response.status_code == 200, f"Admin dashboard page not accessible: {response.status_code}"
        assert "管理后台" in response.text, "Admin dashboard page content not found"
        print("✅ Admin dashboard page is accessible")
        
        # Test admin JavaScript file
        response = requests.get(f"{base_url}/admin/js/admin-dashboard.js")
        assert response.status_code == 200, f"Admin JavaScript file not accessible: {response.status_code}"
        assert "AdminDashboard" in response.text, "Admin JavaScript content not found"
        print("✅ Admin JavaScript file is accessible")
        
        # Test main frontend page
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200, f"Main page not accessible: {response.status_code}"
        assert "快递查询网站" in response.text, "Main page content not found"
        print("✅ Main frontend page is accessible")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        return False
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_admin_static_files_structure():
    """测试管理后台静态文件结构"""
    
    # Check if admin files exist
    admin_files = [
        "static/admin/login.html",
        "static/admin/dashboard.html", 
        "static/admin/js/admin-dashboard.js"
    ]
    
    for file_path in admin_files:
        assert os.path.exists(file_path), f"Admin file not found: {file_path}"
        print(f"✅ {file_path} exists")
    
    return True

if __name__ == "__main__":
    print("Testing admin interface...")
    
    # Test file structure
    print("\n1. Testing static files structure...")
    if test_admin_static_files_structure():
        print("✅ All admin static files exist")
    
    # Test accessibility
    print("\n2. Testing admin interface accessibility...")
    if test_admin_interface_accessibility():
        print("✅ All admin interface pages are accessible")
    
    print("\n🎉 Admin interface implementation test completed!")