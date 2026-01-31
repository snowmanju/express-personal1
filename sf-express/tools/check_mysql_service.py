"""
检查MySQL服务状态并提供启动指南
"""

import subprocess
import sys

print("=" * 70)
print("检查MySQL服务状态")
print("=" * 70)
print()

# 尝试查找MySQL服务
print("[1/2] 查找MySQL服务...")
try:
    # 使用wmic查询MySQL服务
    result = subprocess.run(
        ['wmic', 'service', 'where', 'name like "%mysql%"', 'get', 'name,state,startmode'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0 and result.stdout.strip():
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        if len(lines) > 1:  # 有标题行和数据行
            print("✓ 找到MySQL服务:")
            print()
            for line in lines:
                print(f"  {line}")
            print()
            
            # 检查是否有Running状态
            if 'Running' in result.stdout:
                print("✓ MySQL服务正在运行")
            else:
                print("⚠ MySQL服务未运行")
                print()
                print("请手动启动MySQL服务:")
                print("方法1 - 使用命令行 (以管理员身份运行):")
                print("  net start MySQL")
                print()
                print("方法2 - 使用服务管理器:")
                print("  1. 按 Win+R")
                print("  2. 输入: services.msc")
                print("  3. 找到MySQL服务")
                print("  4. 右键 -> 启动")
        else:
            print("✗ 未找到MySQL服务")
    else:
        print("✗ 未找到MySQL服务")
        print()
        print("请检查MySQL是否已安装:")
        print("1. 打开服务管理器: Win+R 输入 services.msc")
        print("2. 查找名称包含 'MySQL' 的服务")
        print("3. 如果没有找到，可能需要重新安装MySQL")
        
except Exception as e:
    print(f"✗ 查询失败: {e}")
    print()
    print("请手动检查:")
    print("1. 打开服务管理器: Win+R 输入 services.msc")
    print("2. 查找MySQL相关服务")

# 尝试连接MySQL
print()
print("[2/2] 测试MySQL连接...")
try:
    import pymysql
    
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='admin123',
        connect_timeout=3
    )
    print("✓ MySQL连接成功！")
    print()
    
    # 显示MySQL版本
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"  MySQL版本: {version[0]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 70)
    print("✓ MySQL服务正常！可以继续运行 setup_database.py")
    print("=" * 70)
    
except pymysql.err.OperationalError as e:
    error_code = e.args[0]
    print(f"✗ 无法连接MySQL (错误代码: {error_code})")
    print()
    
    if error_code == 2003:
        print("📋 MySQL服务未启动")
        print()
        print("启动方法:")
        print("1. 以管理员身份打开命令提示符")
        print("2. 运行: net start MySQL")
        print()
        print("或者:")
        print("1. 按 Win+R")
        print("2. 输入: services.msc")
        print("3. 找到MySQL服务并启动")
    elif error_code == 1045:
        print("📋 密码错误")
        print("  当前密码: admin123")
        print("  请确认MySQL root密码是否正确")
    else:
        print(f"📋 错误信息: {e}")
        
except Exception as e:
    print(f"✗ 连接测试失败: {e}")

print()
print("=" * 70)
