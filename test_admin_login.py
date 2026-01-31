"""
测试管理员登录问题
"""

import requests
import pymysql
import json
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 70)
print("诊断管理员登录问题")
print("=" * 70)
print()

# 数据库配置
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'admin123'
DB_NAME = 'express_tracking'

# 测试1: 检查数据库中的用户
print("[1/3] 检查数据库中的管理员用户...")
try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # 查询所有管理员用户
    cursor.execute("SELECT id, username, created_at FROM admin_users")
    users = cursor.fetchall()
    
    if users:
        print(f"✓ 找到 {len(users)} 个管理员用户:")
        for user in users:
            print(f"  - ID: {user[0]}, 用户名: {user[1]}, 创建时间: {user[2]}")
    else:
        print("✗ 数据库中没有管理员用户")
        print("  需要运行: python create_admin_user.py admin admin123")
    
    # 检查admin用户
    cursor.execute("SELECT id, username, password_hash FROM admin_users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    
    if admin_user:
        print()
        print("✓ 找到admin用户:")
        print(f"  - ID: {admin_user[0]}")
        print(f"  - 用户名: {admin_user[1]}")
        print(f"  - 密码哈希: {admin_user[2][:50]}...")
    else:
        print()
        print("✗ 未找到admin用户")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ 数据库检查失败: {e}")

# 测试2: 测试登录API
print()
print("[2/3] 测试登录API...")
base_url = "http://localhost:8000"

try:
    response = requests.post(
        f"{base_url}/api/v1/admin/login",
        json={
            "username": "admin",
            "password": "admin123"
        },
        timeout=10
    )
    
    print(f"HTTP状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✓ 登录成功！")
        print(f"  - access_token: {data.get('access_token', '')[:50]}...")
        print(f"  - token_type: {data.get('token_type')}")
    else:
        print("✗ 登录失败")
        try:
            error_data = response.json()
            print(f"  - 错误: {error_data.get('detail', response.text)}")
        except:
            print(f"  - 响应: {response.text}")
            
except Exception as e:
    print(f"✗ API测试失败: {e}")

# 测试3: 测试密码验证
print()
print("[3/3] 测试密码哈希验证...")
try:
    from app.services.auth_service import auth_service
    from app.core.database import SessionLocal
    from app.models.admin_user import AdminUser
    
    db = SessionLocal()
    
    # 查找admin用户
    user = db.query(AdminUser).filter(AdminUser.username == "admin").first()
    
    if user:
        print(f"✓ 找到用户: {user.username}")
        
        # 测试密码验证
        is_valid = auth_service.verify_password("admin123", user.password_hash)
        
        if is_valid:
            print("✓ 密码验证成功")
        else:
            print("✗ 密码验证失败")
            print("  密码哈希可能已损坏，需要重新创建用户")
    else:
        print("✗ 未找到admin用户")
        print("  需要运行: python create_admin_user.py admin admin123")
    
    db.close()
    
except Exception as e:
    print(f"✗ 密码验证测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("诊断完成")
print()
print("如果发现问题，可以尝试:")
print("1. 删除现有admin用户: DELETE FROM admin_users WHERE username='admin';")
print("2. 重新创建用户: python create_admin_user.py admin admin123")
print("3. 重启服务器: python run.py")
print("=" * 70)
