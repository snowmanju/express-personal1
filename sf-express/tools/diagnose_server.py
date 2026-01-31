"""
服务器启动诊断脚本
检查所有可能导致服务器启动失败的问题
"""

import sys
import os

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python_version():
    """检查Python版本"""
    print_section("1. 检查Python版本")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("✓ Python版本符合要求 (>= 3.8)")
        return True
    else:
        print("✗ Python版本过低，需要 >= 3.8")
        return False

def check_dependencies():
    """检查关键依赖包"""
    print_section("2. 检查依赖包")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'sqlalchemy': 'SQLAlchemy',
        'pymysql': 'PyMySQL',
        'pandas': 'Pandas',
        'python-dotenv': 'python-dotenv',
        'pydantic': 'Pydantic',
        'python-jose': 'python-jose',
        'passlib': 'Passlib',
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {name} 已安装")
        except ImportError:
            print(f"✗ {name} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n缺少的包: {', '.join(missing)}")
        print(f"安装命令: pip install {' '.join(missing)}")
        return False
    return True

def check_env_file():
    """检查.env配置文件"""
    print_section("3. 检查.env配置文件")
    
    if not os.path.exists('.env'):
        print("✗ .env 文件不存在")
        print("\n建议操作:")
        print("1. 复制 .env.example 为 .env")
        print("2. 修改数据库配置")
        return False
    
    print("✓ .env 文件存在")
    
    # 读取并检查关键配置
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if var not in content or f'{var}=' not in content:
                missing_vars.append(var)
                print(f"✗ 缺少配置: {var}")
            else:
                # 获取配置值
                for line in content.split('\n'):
                    if line.startswith(f'{var}='):
                        value = line.split('=', 1)[1].strip()
                        if value:
                            print(f"✓ {var} 已配置")
                        else:
                            print(f"⚠ {var} 配置为空")
                            missing_vars.append(var)
                        break
        
        if missing_vars:
            print(f"\n需要配置: {', '.join(missing_vars)}")
            return False
        return True
        
    except Exception as e:
        print(f"✗ 读取.env文件失败: {e}")
        return False

def check_database_connection():
    """检查数据库连接"""
    print_section("4. 检查数据库连接")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from app.core.database import engine
        
        # 尝试连接
        with engine.connect() as conn:
            print("✓ 数据库连接成功")
            
            # 检查数据库表
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = ['admin_users', 'cargo_manifest']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"⚠ 缺少数据表: {', '.join(missing_tables)}")
                print("运行数据库迁移: alembic upgrade head")
                return False
            else:
                print(f"✓ 数据表完整 ({len(tables)} 个表)")
            
            return True
            
    except ImportError as e:
        print(f"✗ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("\n可能的原因:")
        print("1. MySQL服务未启动 - 运行: net start MySQL")
        print("2. 数据库不存在 - 创建数据库: CREATE DATABASE express_tracking")
        print("3. 用户名或密码错误 - 检查.env中的DATABASE_URL")
        print("4. 端口错误 - 默认MySQL端口是3306")
        return False

def check_port_availability():
    """检查端口是否可用"""
    print_section("5. 检查端口可用性")
    
    import socket
    
    port = 8000
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✗ 端口 {port} 已被占用")
            print("\n解决方案:")
            print(f"1. 查看占用进程: netstat -ano | findstr :{port}")
            print("2. 结束占用进程或修改run.py中的端口号")
            return False
        else:
            print(f"✓ 端口 {port} 可用")
            return True
    except Exception as e:
        print(f"⚠ 无法检查端口: {e}")
        return True

def check_static_files():
    """检查静态文件"""
    print_section("6. 检查静态文件")
    
    required_files = [
        'static/index.html',
        'static/admin/login.html',
        'static/admin/dashboard.html',
        'static/admin/js/admin-dashboard.js',
        'static/templates/manifest_upload_template.csv',
    ]
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            missing.append(file_path)
    
    if missing:
        print(f"\n缺少 {len(missing)} 个文件")
        return False
    return True

def check_app_structure():
    """检查应用结构"""
    print_section("7. 检查应用结构")
    
    required_dirs = [
        'app',
        'app/api',
        'app/api/v1',
        'app/core',
        'app/models',
        'app/schemas',
        'app/services',
    ]
    
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/api/v1/auth.py',
        'app/api/v1/manifest.py',
        'app/core/database.py',
        'app/core/auth.py',
        'run.py',
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ 不存在")
            all_ok = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_ok = False
    
    return all_ok

def test_import_app():
    """测试导入应用"""
    print_section("8. 测试导入应用")
    
    try:
        from app.main import app
        print("✓ 成功导入 FastAPI 应用")
        
        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"✓ 注册了 {len(routes)} 个路由")
        
        # 检查关键路由
        key_routes = ['/api/v1/auth/login', '/api/v1/admin/manifest/upload']
        for route in key_routes:
            if any(route in r for r in routes):
                print(f"✓ 路由存在: {route}")
            else:
                print(f"⚠ 路由缺失: {route}")
        
        return True
    except Exception as e:
        print(f"✗ 导入应用失败: {e}")
        print(f"\n错误详情:")
        import traceback
        traceback.print_exc()
        return False

def check_admin_user():
    """检查管理员用户"""
    print_section("9. 检查管理员用户")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from app.core.database import SessionLocal
        from app.models.admin_user import AdminUser
        
        db = SessionLocal()
        try:
            admin_count = db.query(AdminUser).count()
            if admin_count > 0:
                print(f"✓ 存在 {admin_count} 个管理员用户")
                
                # 显示用户名
                users = db.query(AdminUser).all()
                for user in users:
                    print(f"  - {user.username}")
                return True
            else:
                print("⚠ 没有管理员用户")
                print("\n创建管理员:")
                print("python create_admin_user.py")
                return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"⚠ 无法检查管理员用户: {e}")
        return True  # 不阻止继续

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  快递追踪系统 - 服务器启动诊断")
    print("=" * 60)
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("配置文件", check_env_file),
        ("数据库连接", check_database_connection),
        ("端口可用性", check_port_availability),
        ("静态文件", check_static_files),
        ("应用结构", check_app_structure),
        ("应用导入", test_import_app),
        ("管理员用户", check_admin_user),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 检查 {name} 时出错: {e}")
            results.append((name, False))
    
    # 总结
    print_section("诊断总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n通过检查: {passed}/{total}")
    print()
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("✓ 所有检查通过！可以启动服务器")
        print("\n启动命令: python run.py")
    else:
        print("✗ 存在问题，请根据上述提示修复")
        print("\n常见问题解决:")
        print("1. 缺少依赖: pip install -r requirements.txt")
        print("2. 数据库问题: net start MySQL")
        print("3. 配置问题: 检查 .env 文件")
        print("4. 端口占用: 修改 run.py 中的端口")
    
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
