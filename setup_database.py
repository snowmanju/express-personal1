"""
自动创建数据库和表
"""

import pymysql
import sys

print("=" * 60)
print("配置MySQL数据库")
print("=" * 60)
print()

# 数据库配置
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'admin123'
DB_NAME = 'express_tracking'

# 步骤1: 创建数据库
print("[1/3] 创建数据库...")
try:
    # 连接MySQL（不指定数据库）
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"✓ 数据库 '{DB_NAME}' 创建成功")
    
    cursor.close()
    conn.close()
except pymysql.err.OperationalError as e:
    print(f"✗ 连接MySQL失败: {e}")
    print("\n请检查:")
    print("1. MySQL服务是否启动")
    print("2. 用户名和密码是否正确")
    sys.exit(1)
except Exception as e:
    print(f"✗ 创建数据库失败: {e}")
    sys.exit(1)

# 步骤2: 运行数据库迁移
print("\n[2/3] 运行数据库迁移...")
try:
    import subprocess
    result = subprocess.run(
        ['alembic', 'upgrade', 'head'],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("✓ 数据库表创建成功")
        if result.stdout:
            print(result.stdout)
    else:
        print("⚠ 数据库迁移可能有问题")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
except FileNotFoundError:
    print("⚠ alembic未找到，尝试直接创建表...")
    # 如果alembic不可用，直接创建表
    try:
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✓ 使用SQLAlchemy创建表成功")
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        sys.exit(1)
except Exception as e:
    print(f"⚠ 迁移过程出现问题: {e}")
    # 尝试直接创建表
    try:
        from app.core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✓ 使用SQLAlchemy创建表成功")
    except Exception as e2:
        print(f"✗ 创建表失败: {e2}")
        sys.exit(1)

# 步骤3: 验证数据库
print("\n[3/3] 验证数据库...")
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
    
    # 查看表
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    if tables:
        print(f"✓ 数据库包含 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("⚠ 数据库中没有表")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ 验证失败: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✓ 数据库配置完成！")
print()
print("下一步:")
print("1. 创建管理员用户: python create_admin_user.py")
print("2. 启动服务器: python run.py")
print("=" * 60)
