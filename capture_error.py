"""
捕获并显示详细的启动错误信息
"""

import sys
import traceback

print("=" * 70)
print("正在检查服务器启动问题...")
print("=" * 70)
print()

# 检查1: 导入基础模块
print("[1/6] 检查基础模块...")
try:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ 基础模块正常")
except Exception as e:
    print(f"✗ 基础模块错误: {e}")
    sys.exit(1)

# 检查2: 检查配置
print("\n[2/6] 检查配置...")
try:
    db_url = os.getenv('DATABASE_URL')
    secret_key = os.getenv('SECRET_KEY')
    
    if not db_url:
        print("✗ DATABASE_URL 未配置")
        print("  请在 .env 文件中配置 DATABASE_URL")
        sys.exit(1)
    else:
        # 隐藏密码显示
        safe_url = db_url.split('@')[0].split(':')[0] + ':***@' + db_url.split('@')[1] if '@' in db_url else db_url
        print(f"✓ DATABASE_URL: {safe_url}")
    
    if not secret_key:
        print("⚠ SECRET_KEY 未配置（将使用默认值）")
    else:
        print("✓ SECRET_KEY 已配置")
except Exception as e:
    print(f"✗ 配置检查错误: {e}")

# 检查3: 测试数据库连接
print("\n[3/6] 测试数据库连接...")
try:
    import pymysql
    
    # 解析数据库URL
    db_url = os.getenv('DATABASE_URL', '')
    if 'mysql+pymysql://' in db_url:
        parts = db_url.replace('mysql+pymysql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        database = host_db[1].split('?')[0] if len(host_db) > 1 else 'express_tracking'
        
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            print(f"✓ 数据库连接成功: {database}")
            conn.close()
        except pymysql.err.OperationalError as e:
            error_code = e.args[0]
            error_msg = e.args[1] if len(e.args) > 1 else str(e)
            
            print(f"✗ 数据库连接失败 (错误代码: {error_code})")
            print(f"  错误信息: {error_msg}")
            print()
            
            if error_code == 1049:
                print("📋 解决方案: 数据库不存在")
                print("  1. 登录MySQL: mysql -u root -p")
                print(f"  2. 创建数据库: CREATE DATABASE {database};")
                print("  3. 退出: exit;")
                print("  4. 运行迁移: alembic upgrade head")
            elif error_code == 1045:
                print("📋 解决方案: 用户名或密码错误")
                print("  1. 检查 .env 文件中的 DATABASE_URL")
                print("  2. 确保密码正确")
                print(f"  3. 当前用户: {user}")
            elif error_code == 2003:
                print("📋 解决方案: MySQL服务未启动")
                print("  1. 启动MySQL: net start MySQL")
                print("  2. 或在服务管理器中启动MySQL服务")
            else:
                print("📋 请检查MySQL配置和服务状态")
            
            sys.exit(1)
except Exception as e:
    print(f"✗ 数据库检查错误: {e}")
    traceback.print_exc()

# 检查4: 导入应用核心模块
print("\n[4/6] 导入应用核心模块...")
try:
    from app.core.database import engine, SessionLocal
    print("✓ 数据库模块导入成功")
except Exception as e:
    print(f"✗ 数据库模块导入失败: {e}")
    print("\n错误详情:")
    traceback.print_exc()
    sys.exit(1)

try:
    from app.core.auth import get_password_hash, verify_password
    print("✓ 认证模块导入成功")
except Exception as e:
    print(f"✗ 认证模块导入失败: {e}")
    print("\n错误详情:")
    traceback.print_exc()
    sys.exit(1)

# 检查5: 导入FastAPI应用
print("\n[5/6] 导入FastAPI应用...")
try:
    from app.main import app
    print("✓ FastAPI应用导入成功")
    print(f"✓ 注册了 {len(app.routes)} 个路由")
except Exception as e:
    print(f"✗ FastAPI应用导入失败: {e}")
    print("\n错误详情:")
    traceback.print_exc()
    print()
    print("📋 可能的原因:")
    print("  1. app/main.py 文件有语法错误")
    print("  2. 缺少必要的依赖包")
    print("  3. 路由配置有问题")
    sys.exit(1)

# 检查6: 检查端口
print("\n[6/6] 检查端口...")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result == 0:
        print("⚠ 端口8000已被占用")
        print("  查看占用: netstat -ano | findstr :8000")
        print("  或修改 run.py 中的端口号")
    else:
        print("✓ 端口8000可用")
except Exception as e:
    print(f"⚠ 无法检查端口: {e}")

# 最终测试: 尝试启动
print("\n" + "=" * 70)
print("所有检查通过！尝试启动服务器...")
print("=" * 70)
print()

try:
    import uvicorn
    print("正在启动服务器...")
    print("如果看到 'Uvicorn running on...' 说明启动成功")
    print("按 Ctrl+C 停止服务器")
    print("-" * 70)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
except KeyboardInterrupt:
    print("\n\n服务器已停止")
except Exception as e:
    print(f"\n✗ 启动失败: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    print()
    print("=" * 70)
    print("请将上面的错误信息复制并发送给我，我会帮你解决！")
    print("=" * 70)
    sys.exit(1)
