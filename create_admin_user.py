#!/usr/bin/env python3
"""
创建管理员用户脚本
Create Admin User Script
"""

import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.auth_service import auth_service
from app.models.admin_user import AdminUser


def create_admin_user(username: str, password: str) -> bool:
    """
    创建管理员用户
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        bool: 创建是否成功
    """
    db = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(AdminUser).filter(AdminUser.username == username).first()
        
        if existing_user:
            print(f"用户 '{username}' 已存在")
            return False
        
        # 创建新用户
        user = auth_service.create_user(db, username, password)
        
        print(f"管理员用户 '{username}' 创建成功")
        print(f"用户ID: {user.id}")
        print(f"创建时间: {user.created_at}")
        
        return True
        
    except Exception as e:
        print(f"创建用户失败: {e}")
        return False
        
    finally:
        db.close()


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法: python create_admin_user.py <用户名> <密码>")
        print("示例: python create_admin_user.py admin admin123")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    if len(password) < 6:
        print("密码长度至少为6位")
        sys.exit(1)
    
    success = create_admin_user(username, password)
    
    if success:
        print("\n管理员用户创建成功！")
        print("现在可以使用该用户登录后台管理系统")
    else:
        print("\n管理员用户创建失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()