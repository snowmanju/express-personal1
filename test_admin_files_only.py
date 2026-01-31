"""
测试管理后台文件结构和内容
"""

import os
import re

def test_admin_files_exist():
    """测试管理后台文件是否存在"""
    admin_files = [
        "static/admin/login.html",
        "static/admin/dashboard.html", 
        "static/admin/js/admin-dashboard.js"
    ]
    
    for file_path in admin_files:
        assert os.path.exists(file_path), f"Admin file not found: {file_path}"
        print(f"✅ {file_path} exists")
    
    return True

def test_login_page_content():
    """测试登录页面内容"""
    with open("static/admin/login.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for essential elements
    assert "管理员登录" in content, "Login page title not found"
    assert "用户名" in content, "Username field not found"
    assert "密码" in content, "Password field not found"
    assert "/api/v1/admin/auth/login" in content, "Login API endpoint not found"
    assert "AdminLogin" in content, "AdminLogin class not found"
    
    print("✅ Login page content is valid")
    return True

def test_dashboard_page_content():
    """测试管理后台页面内容"""
    with open("static/admin/dashboard.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for essential elements
    assert "管理后台" in content, "Dashboard title not found"
    assert "理货单管理" in content, "Manifest management not found"
    assert "文件上传" in content, "File upload not found"
    assert "admin-dashboard.js" in content, "JavaScript file reference not found"
    
    print("✅ Dashboard page content is valid")
    return True

def test_javascript_content():
    """测试JavaScript文件内容"""
    with open("static/admin/js/admin-dashboard.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for essential classes and methods
    assert "class AdminDashboard" in content, "AdminDashboard class not found"
    assert "handleFileUpload" in content, "File upload handler not found"
    assert "loadManifests" in content, "Load manifests method not found"
    assert "editManifest" in content, "Edit manifest method not found"
    assert "deleteManifest" in content, "Delete manifest method not found"
    assert "/api/v1/admin/manifest" in content, "Manifest API endpoints not found"
    
    print("✅ JavaScript content is valid")
    return True

def test_api_endpoints_referenced():
    """测试API端点引用是否正确"""
    with open("static/admin/js/admin-dashboard.js", "r", encoding="utf-8") as f:
        js_content = f.read()
    
    # Expected API endpoints
    expected_endpoints = [
        "/api/v1/admin/auth/logout",
        "/api/v1/admin/manifest/upload",
        "/api/v1/admin/manifest/search",
        "/api/v1/admin/manifest/statistics/overview"
    ]
    
    for endpoint in expected_endpoints:
        assert endpoint in js_content, f"API endpoint not found: {endpoint}"
        print(f"✅ API endpoint referenced: {endpoint}")
    
    return True

def test_form_validation():
    """测试表单验证逻辑"""
    with open("static/admin/js/admin-dashboard.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for validation logic in file upload
    assert "file.size > 10 * 1024 * 1024" in content, "File size validation not found"
    assert "allowedTypes" in content, "File type validation not found"
    assert "不支持的文件格式" in content, "File format error message not found"
    assert "文件大小不能超过10MB" in content, "File size error message not found"
    
    print("✅ Form validation logic is present")
    return True

def test_file_upload_functionality():
    """测试文件上传功能"""
    with open("static/admin/js/admin-dashboard.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for file upload related code
    assert "handleFileUpload" in content, "File upload handler not found"
    assert "FormData" in content, "FormData usage not found"
    assert "displayUploadResults" in content, "Upload results display not found"
    assert "displayDataPreview" in content, "Data preview display not found"
    
    print("✅ File upload functionality is present")
    return True

def test_responsive_design():
    """测试响应式设计"""
    with open("static/admin/dashboard.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for Bootstrap and responsive elements
    assert "bootstrap@5.1.3" in content, "Bootstrap CSS not found"
    assert "viewport" in content, "Viewport meta tag not found"
    assert "@media" in content, "Media queries not found"
    assert "col-md-" in content, "Bootstrap grid classes not found"
    
    print("✅ Responsive design elements are present")
    return True

if __name__ == "__main__":
    print("Testing admin interface files...")
    
    tests = [
        test_admin_files_exist,
        test_login_page_content,
        test_dashboard_page_content,
        test_javascript_content,
        test_api_endpoints_referenced,
        test_form_validation,
        test_file_upload_functionality,
        test_responsive_design
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test.__name__} - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All admin interface tests passed!")
        print("\n✅ 管理后台界面实现完成:")
        print("  - 管理员登录页面 (/admin/login.html)")
        print("  - 管理后台主页面 (/admin/dashboard.html)")
        print("  - 文件上传和数据预览功能")
        print("  - 理货单管理功能")
        print("  - 响应式设计")
        print("  - 完整的JavaScript交互逻辑")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    # return passed == total  # Cannot return from module level