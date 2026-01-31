"""
测试理货单管理API端点
Test Manifest Management API Endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.admin_user import AdminUser
from app.models.cargo_manifest import CargoManifest
from app.services.auth_service import auth_service


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_manifest_api.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """创建数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_admin_user(db_session):
    """创建测试管理员用户"""
    # 创建测试用户
    user_data = {
        "username": "testadmin",
        "password": "testpassword123"
    }
    
    # 使用auth_service创建用户
    result = auth_service.create_admin_user(db_session, user_data)
    if result['success']:
        return result['user']
    else:
        # 如果用户已存在，直接获取
        user = db_session.query(AdminUser).filter(AdminUser.username == "testadmin").first()
        return user


@pytest.fixture
def auth_headers(test_admin_user, db_session):
    """获取认证头"""
    # 登录获取token
    login_data = {
        "username": "testadmin",
        "password": "testpassword123"
    }
    
    result = auth_service.authenticate_user(db_session, login_data['username'], login_data['password'])
    if result['success']:
        token = auth_service.create_access_token(data={"sub": result['user'].username})
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.fail("Failed to authenticate test user")


@pytest.fixture
def sample_manifest_data():
    """示例理货单数据"""
    return {
        "tracking_number": "TEST123456789",
        "manifest_date": "2024-01-01",
        "transport_code": "T001",
        "customer_code": "C001",
        "goods_code": "G001",
        "package_number": "PKG123456789",
        "weight": 1.5,
        "length": 10.0,
        "width": 8.0,
        "height": 5.0,
        "special_fee": 0.0
    }


class TestManifestAPIEndpoints:
    """理货单API端点测试类"""
    
    def test_manifest_endpoints_require_authentication(self, setup_database):
        """测试理货单端点需要认证"""
        # 测试没有认证头的请求
        endpoints = [
            ("GET", "/api/v1/admin/manifest/search"),
            ("GET", "/api/v1/admin/manifest/1"),
            ("POST", "/api/v1/admin/manifest/"),
            ("PUT", "/api/v1/admin/manifest/1"),
            ("DELETE", "/api/v1/admin/manifest/1"),
            ("GET", "/api/v1/admin/manifest/statistics/overview"),
            ("GET", "/api/v1/admin/manifest/tracking/TEST123"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == 403, f"Endpoint {method} {endpoint} should require authentication"
    
    def test_manifest_search_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试理货单搜索端点"""
        # 先创建一个理货单
        manifest = CargoManifest(**sample_manifest_data)
        db_session.add(manifest)
        db_session.commit()
        
        # 测试搜索
        response = client.get(
            "/api/v1/admin/manifest/search",
            headers=auth_headers,
            params={"q": "TEST123", "page": 1, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
    
    def test_manifest_create_endpoint(self, setup_database, auth_headers, sample_manifest_data):
        """测试理货单创建端点"""
        # 修改tracking_number以避免重复
        sample_manifest_data["tracking_number"] = "CREATE_TEST123"
        
        response = client.post(
            "/api/v1/admin/manifest/",
            headers=auth_headers,
            json=sample_manifest_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["tracking_number"] == "CREATE_TEST123"
    
    def test_manifest_get_by_id_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试根据ID获取理货单端点"""
        # 创建理货单
        sample_manifest_data["tracking_number"] = "GET_BY_ID_TEST"
        manifest = CargoManifest(**sample_manifest_data)
        db_session.add(manifest)
        db_session.commit()
        db_session.refresh(manifest)
        
        # 测试获取
        response = client.get(
            f"/api/v1/admin/manifest/{manifest.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["tracking_number"] == "GET_BY_ID_TEST"
    
    def test_manifest_update_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试理货单更新端点"""
        # 创建理货单
        sample_manifest_data["tracking_number"] = "UPDATE_TEST123"
        manifest = CargoManifest(**sample_manifest_data)
        db_session.add(manifest)
        db_session.commit()
        db_session.refresh(manifest)
        
        # 测试更新
        update_data = {"weight": 2.5, "special_fee": 10.0}
        response = client.put(
            f"/api/v1/admin/manifest/{manifest.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["weight"] == 2.5
        assert data["data"]["special_fee"] == 10.0
    
    def test_manifest_delete_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试理货单删除端点"""
        # 创建理货单
        sample_manifest_data["tracking_number"] = "DELETE_TEST123"
        manifest = CargoManifest(**sample_manifest_data)
        db_session.add(manifest)
        db_session.commit()
        db_session.refresh(manifest)
        
        # 测试删除
        response = client.delete(
            f"/api/v1/admin/manifest/{manifest.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_manifest_get_by_tracking_number_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试根据快递单号获取理货单端点"""
        # 创建理货单
        sample_manifest_data["tracking_number"] = "TRACKING_TEST123"
        manifest = CargoManifest(**sample_manifest_data)
        db_session.add(manifest)
        db_session.commit()
        
        # 测试获取
        response = client.get(
            "/api/v1/admin/manifest/tracking/TRACKING_TEST123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["tracking_number"] == "TRACKING_TEST123"
    
    def test_manifest_statistics_endpoint(self, setup_database, auth_headers):
        """测试理货单统计端点"""
        response = client.get(
            "/api/v1/admin/manifest/statistics/overview",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_file_upload_endpoint_structure(self, setup_database, auth_headers):
        """测试文件上传端点结构"""
        # 测试没有文件的请求
        response = client.post(
            "/api/v1/admin/manifest/upload",
            headers=auth_headers,
            data={"preview_only": "true"}
        )
        
        # 应该返回422因为缺少文件
        assert response.status_code == 422
    
    def test_batch_delete_endpoint(self, setup_database, auth_headers, sample_manifest_data, db_session):
        """测试批量删除端点"""
        # 创建多个理货单
        manifests = []
        for i in range(3):
            data = sample_manifest_data.copy()
            data["tracking_number"] = f"BATCH_DELETE_{i}"
            manifest = CargoManifest(**data)
            db_session.add(manifest)
            manifests.append(manifest)
        
        db_session.commit()
        
        # 获取ID列表
        manifest_ids = [m.id for m in manifests]
        
        # 测试批量删除
        response = client.delete(
            "/api/v1/admin/manifest/batch",
            headers=auth_headers,
            json=manifest_ids
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_invalid_manifest_id_returns_404(self, setup_database, auth_headers):
        """测试无效理货单ID返回404"""
        response = client.get(
            "/api/v1/admin/manifest/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_invalid_tracking_number_returns_404(self, setup_database, auth_headers):
        """测试无效快递单号返回404"""
        response = client.get(
            "/api/v1/admin/manifest/tracking/NONEXISTENT123",
            headers=auth_headers
        )
        
        assert response.status_code == 404


def test_manifest_api_endpoints_comprehensive():
    """综合测试理货单API端点"""
    print("=== 测试理货单API端点认证 ===")
    
    # 测试未认证访问
    endpoints_to_test = [
        "/api/v1/admin/manifest/search",
        "/api/v1/admin/manifest/statistics/overview",
    ]
    
    for endpoint in endpoints_to_test:
        response = client.get(endpoint)
        print(f"未认证访问 {endpoint}: {response.status_code}")
        assert response.status_code == 403, f"端点 {endpoint} 应该需要认证"
    
    print("✓ 理货单API端点认证测试通过")


if __name__ == "__main__":
    test_manifest_api_endpoints_comprehensive()
    print("🎉 理货单API端点测试完成！")