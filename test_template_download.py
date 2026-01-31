"""
单元测试：模板下载功能
Tests for template download endpoint
"""

import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.api.v1.manifest import router
from app.core.auth import get_current_active_user
from app.models.admin_user import AdminUser


# Mock authentication
def mock_get_current_user():
    """Mock authentication to return a test user"""
    user = AdminUser()
    user.id = 1
    user.username = "testuser"
    user.password_hash = "test_hash"
    return user


@pytest.fixture
def client():
    """Create test client with authentication"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/admin/manifest")
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user
    return TestClient(test_app)


@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/admin/manifest")
    return TestClient(test_app)


def test_template_download_endpoint_availability(client):
    """
    测试模板下载端点可用性
    验证需求：5.1 - 提供模板下载端点
    """
    response = client.get("/api/v1/admin/manifest/template/download")
    
    # 端点应该返回成功状态码（200）
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_template_download_response_format(client):
    """
    测试模板下载响应格式
    验证需求：5.2 - 返回正确的文件和content-type
    """
    response = client.get("/api/v1/admin/manifest/template/download")
    
    # 检查响应状态码
    assert response.status_code == 200
    
    # 检查content-type头
    assert "text/csv" in response.headers.get("content-type", ""), \
        f"Expected text/csv content-type, got {response.headers.get('content-type')}"
    
    # 检查content-disposition头
    content_disposition = response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition, \
        f"Expected attachment in content-disposition, got {content_disposition}"
    assert "manifest_upload_template.csv" in content_disposition, \
        f"Expected filename in content-disposition, got {content_disposition}"


def test_template_download_correct_file(client):
    """
    测试下载的是正确的模板文件
    验证需求：5.2 - 提供static/templates/manifest_upload_template.csv文件
    """
    response = client.get("/api/v1/admin/manifest/template/download")
    
    assert response.status_code == 200
    
    # 读取实际的模板文件内容
    template_path = os.path.join("static", "templates", "manifest_upload_template.csv")
    if os.path.exists(template_path):
        with open(template_path, "rb") as f:
            expected_content = f.read()
        
        # 比较下载的内容与实际文件内容
        assert response.content == expected_content, \
            "Downloaded content does not match template file"


def test_template_content_validation(client):
    """
    测试模板内容验证
    验证需求：5.3, 5.4 - 模板包含正确的列标题和示例数据
    """
    response = client.get("/api/v1/admin/manifest/template/download")
    
    assert response.status_code == 200
    
    # 解码CSV内容
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")
    
    # 至少应该有标题行
    assert len(lines) >= 1, "Template should have at least header row"
    
    # 检查标题行包含必需的列
    header = lines[0]
    required_columns = [
        "理货日期", "快递单号", "集包单号", "长度", "宽度", 
        "高度", "重量", "货物代码", "客户代码", "运输代码"
    ]
    
    for column in required_columns:
        assert column in header, f"Header should contain column: {column}"
    
    # 检查是否有示例数据行
    assert len(lines) > 1, "Template should contain sample data rows"


def test_template_download_requires_authentication(unauthenticated_client):
    """
    测试模板下载需要身份验证
    验证需求：5.1 - 端点应该需要身份验证
    """
    response = unauthenticated_client.get("/api/v1/admin/manifest/template/download")
    
    # 未认证的请求应该返回401或403
    assert response.status_code in [401, 403], \
        f"Expected 401 or 403 for unauthenticated request, got {response.status_code}"


def test_template_file_exists():
    """
    测试模板文件存在于预期位置
    验证需求：5.2 - 模板文件应该存在于static/templates/目录
    """
    template_path = os.path.join("static", "templates", "manifest_upload_template.csv")
    assert os.path.exists(template_path), \
        f"Template file should exist at {template_path}"


def test_template_download_with_missing_file(client, monkeypatch):
    """
    测试当模板文件不存在时的错误处理
    验证需求：错误处理 - 文件不存在时应返回404
    """
    # 模拟文件不存在的情况
    original_exists = os.path.exists
    
    def mock_exists(path):
        if "manifest_upload_template.csv" in str(path):
            return False
        return original_exists(path)
    
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    response = client.get("/api/v1/admin/manifest/template/download")
    
    # 文件不存在应该返回404
    assert response.status_code == 404, \
        f"Expected 404 when file doesn't exist, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
