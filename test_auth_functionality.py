"""
认证功能测试 - 简化版本
Authentication Functionality Tests - Simplified Version
"""

import pytest
from datetime import datetime, timedelta
from app.services.auth_service import auth_service
from app.services.session_service import session_service


def test_jwt_token_creation_and_verification():
    """测试JWT令牌创建和验证"""
    test_data = {"sub": "test_user", "role": "admin"}
    
    # 创建令牌
    token = auth_service.create_access_token(test_data)
    
    # 验证令牌
    payload = auth_service.verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == "test_user"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_jwt_token_expiration():
    """测试JWT令牌过期"""
    test_data = {"sub": "test_user"}
    
    # 创建一个已过期的令牌（过期时间为-1秒）
    expired_token = auth_service.create_access_token(
        test_data, 
        expires_delta=timedelta(seconds=-1)
    )
    
    # 验证过期令牌
    payload = auth_service.verify_token(expired_token)
    
    # 过期令牌应该返回None
    assert payload is None


def test_session_validation():
    """测试会话验证"""
    test_data = {"sub": "test_user"}
    
    # 创建有效令牌
    valid_token = auth_service.create_access_token(test_data)
    
    # 创建过期令牌
    expired_token = auth_service.create_access_token(
        test_data,
        expires_delta=timedelta(seconds=-1)
    )
    
    # 测试会话验证
    assert session_service.is_session_valid(valid_token) == True
    assert session_service.is_session_valid(expired_token) == False
    assert session_service.is_session_valid("invalid_token") == False


def test_session_remaining_time():
    """测试会话剩余时间计算"""
    test_data = {"sub": "test_user"}
    
    # 创建5分钟有效期的令牌
    token = auth_service.create_access_token(
        test_data,
        expires_delta=timedelta(minutes=5)
    )
    
    # 获取剩余时间
    remaining_time = session_service.get_session_remaining_time(token)
    
    # 剩余时间应该接近5分钟（300秒），允许一些误差
    assert remaining_time is not None
    assert 290 <= remaining_time <= 300


def test_invalid_token_handling():
    """测试无效令牌处理"""
    # 测试各种无效令牌
    invalid_tokens = [
        "",
        "invalid.token.format",
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        None
    ]
    
    for token in invalid_tokens:
        if token is not None:
            assert auth_service.verify_token(token) is None
            assert session_service.is_session_valid(token) == False
            assert session_service.get_session_remaining_time(token) is None


def test_session_timeout_warning():
    """测试会话超时警告"""
    test_data = {"sub": "test_user"}
    
    # 创建一个即将过期的令牌（30秒）
    token = auth_service.create_access_token(
        test_data,
        expires_delta=timedelta(seconds=30)
    )
    
    # 检查超时警告（警告时间设为1分钟）
    warning_info = session_service.check_session_timeout_warning(token, warning_minutes=1)
    
    # 应该显示警告
    assert warning_info["should_warn"] == True
    assert warning_info["should_logout"] == False
    assert warning_info["remaining_seconds"] <= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])