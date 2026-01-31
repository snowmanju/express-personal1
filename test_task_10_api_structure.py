#!/usr/bin/env python3
"""
测试任务10的API结构和端点定义
Test Task 10 API structure and endpoint definitions
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_auth_api_structure():
    """测试认证API结构"""
    # Mock database dependencies to avoid connection issues
    with patch('app.core.database.get_db'), \
         patch('app.core.auth.get_current_active_user'), \
         patch('app.services.auth_service.auth_service'), \
         patch('app.services.session_service.session_service'):
        
        from app.api.v1 import auth
        
        # Check that the router exists
        assert hasattr(auth, 'router')
        
        # Check that key functions exist
        assert hasattr(auth, 'login')
        assert hasattr(auth, 'logout')
        assert hasattr(auth, 'get_current_user_info')
        assert hasattr(auth, 'get_session_status')
        assert hasattr(auth, 'refresh_session')
        assert hasattr(auth, 'change_password')
        assert hasattr(auth, 'create_user')

def test_manifest_api_structure():
    """测试理货单管理API结构"""
    # Mock database dependencies to avoid connection issues
    with patch('app.core.database.get_db'), \
         patch('app.core.auth.get_current_active_user'), \
         patch('app.services.manifest_service.ManifestService'), \
         patch('app.services.file_processor_service.FileProcessorService'):
        
        from app.api.v1 import manifest
        
        # Check that the router exists
        assert hasattr(manifest, 'router')
        
        # Check that key functions exist
        assert hasattr(manifest, 'upload_manifest_file')
        assert hasattr(manifest, 'search_manifests')
        assert hasattr(manifest, 'get_manifest')
        assert hasattr(manifest, 'create_manifest')
        assert hasattr(manifest, 'update_manifest')
        assert hasattr(manifest, 'delete_manifest')
        assert hasattr(manifest, 'batch_delete_manifests')
        assert hasattr(manifest, 'get_manifest_statistics')
        assert hasattr(manifest, 'get_manifest_by_tracking_number')

def test_api_router_integration():
    """测试API路由聚合"""
    # Mock database dependencies
    with patch('app.core.database.get_db'), \
         patch('app.core.auth.get_current_active_user'), \
         patch('app.services.auth_service.auth_service'), \
         patch('app.services.session_service.session_service'), \
         patch('app.services.manifest_service.ManifestService'), \
         patch('app.services.file_processor_service.FileProcessorService'):
        
        from app.api.v1 import api
        
        # Check that the main API router exists
        assert hasattr(api, 'api_router')
        
        # Check that the API info endpoint exists
        assert hasattr(api, 'api_info')

def test_auth_schemas():
    """测试认证相关的数据模式"""
    from app.schemas import auth
    
    # Check that key schemas exist
    assert hasattr(auth, 'LoginRequest')
    assert hasattr(auth, 'LoginResponse')
    assert hasattr(auth, 'UserInfo')
    assert hasattr(auth, 'UserResponse')
    assert hasattr(auth, 'CreateUserRequest')
    assert hasattr(auth, 'ChangePasswordRequest')

def test_manifest_schemas():
    """测试理货单相关的数据模式"""
    from app.schemas import manifest
    
    # Check that key schemas exist
    assert hasattr(manifest, 'ManifestResponse')
    assert hasattr(manifest, 'ManifestListResponse')
    assert hasattr(manifest, 'ManifestCreateRequest')
    assert hasattr(manifest, 'ManifestUpdateRequest')
    assert hasattr(manifest, 'ManifestSearchRequest')
    assert hasattr(manifest, 'FileUploadResponse')
    assert hasattr(manifest, 'ManifestDeleteResponse')
    assert hasattr(manifest, 'ManifestStatisticsResponse')

def test_admin_interface_files():
    """测试管理界面文件存在性"""
    # Check login page
    assert os.path.exists('static/admin/login.html')
    
    # Check dashboard page
    assert os.path.exists('static/admin/dashboard.html')
    
    # Check JavaScript file
    assert os.path.exists('static/admin/js/admin-dashboard.js')

def test_admin_login_page_content():
    """测试管理员登录页面内容"""
    with open('static/admin/login.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for essential form elements
    assert 'id="loginForm"' in content
    assert 'id="username"' in content
    assert 'id="password"' in content
    assert 'type="submit"' in content
    
    # Check for JavaScript functionality
    assert 'AdminLogin' in content
    assert 'handleLogin' in content

def test_admin_dashboard_page_content():
    """测试管理后台页面内容"""
    with open('static/admin/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for essential sections
    assert 'id="dashboardSection"' in content
    assert 'id="uploadSection"' in content
    assert 'id="manifestsSection"' in content
    
    # Check for forms and tables
    assert 'id="uploadForm"' in content
    assert 'id="searchForm"' in content
    assert 'id="manifestsTable"' in content
    assert 'id="editManifestModal"' in content

def test_admin_javascript_content():
    """测试管理后台JavaScript内容"""
    with open('static/admin/js/admin-dashboard.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for essential class and methods
    assert 'class AdminDashboard' in content
    assert 'handleFileUpload()' in content
    assert 'loadManifests(' in content
    assert 'editManifest(' in content
    assert 'deleteManifest(' in content
    assert 'batchDeleteManifests(' in content
    assert 'apiRequest(' in content
    assert 'logout()' in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])