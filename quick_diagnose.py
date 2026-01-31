"""
快速诊断脚本 - 检查服务器启动问题
"""

print("=" * 60)
print("快速诊断 - 检查服务器启动问题")
print("=" * 60)

# 1. 检查Python和依赖
print("\n[1/5] 检查Python环境...")
try:
    import sys
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
except:
    print("✗ Python检查失败")

# 2. 检查关键包
print("\n[2/5] 检查关键依赖包...")
packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pymysql', 'pandas']
for pkg in packages:
    try:
        __import__(pkg)
        print(f"✓ {pkg}")
    except ImportError:
        print(f"✗ {pkg} 未安装")

# 3. 检查.env文件
print("\n[3/5] 检查配置文件...")
import os
if os.path.exists('.env'):
    print("✓ .env 文件存在")
    with open('.env', 'r') as f:
        content = f.read()
        if 'DATABASE_URL' in content:
            print("✓ DATABASE_URL 已配置")
        if 'SECRET_KEY' in content:
            print("✓ SECRET_KEY 已配置")
else:
    print("✗ .env 文件不存在")

# 4. 检查数据库连接（快速超时）
print("\n[4/5] 检查数据库连接...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    import pymysql
    import os
    
    # 解析DATABASE_URL
    db_url = os.getenv('DATABASE_URL', '')
    if 'mysql+pymysql://' in db_url:
        # 提取连接信息
        parts = db_url.replace('mysql+pymysql://', '').split('@')
        if len(parts) == 2:
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 3306
            database = host_db[1] if len(host_db) > 1 else 'express_tracking'
            
            try:
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    connect_timeout=3
                )
                print(f"✓ 数据库连接成功 ({database})")
                conn.close()
            except pymysql.err.OperationalError as e:
                if '1049' in str(e):
                    print(f"✗ 数据库 '{database}' 不存在")
                    print(f"  创建命令: CREATE DATABASE {database};")
                elif '1045' in str(e):
                    print("✗ 用户名或密码错误")
                    print("  检查 .env 中的 DATABASE_URL")
                elif '2003' in str(e):
                    print("✗ 无法连接到MySQL服务器")
                    print("  启动MySQL: net start MySQL")
                else:
                    print(f"✗ 数据库连接失败: {e}")
            except Exception as e:
                print(f"✗ 连接错误: {e}")
    else:
        print("✗ DATABASE_URL 格式错误")
except Exception as e:
    print(f"⚠ 无法检查数据库: {e}")

# 5. 检查端口
print("\n[5/5] 检查端口8000...")
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result == 0:
        print("✗ 端口8000已被占用")
        print("  查看占用: netstat -ano | findstr :8000")
    else:
        print("✓ 端口8000可用")
except:
    print("⚠ 无法检查端口")

# 6. 尝试导入应用
print("\n[6/6] 测试导入应用...")
try:
    from app.main import app
    print("✓ 应用导入成功")
    print(f"✓ 注册了 {len(app.routes)} 个路由")
except Exception as e:
    print(f"✗ 应用导入失败: {e}")
    import traceback
    print("\n错误详情:")
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
