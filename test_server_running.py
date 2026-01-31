"""
测试服务器是否正常运行
"""

import requests
import sys

print("=" * 70)
print("测试服务器状态")
print("=" * 70)
print()

base_url = "http://localhost:8000"

# 测试1: 健康检查
print("[1/4] 测试健康检查端点...")
try:
    response = requests.get(f"{base_url}/health", timeout=5)
    if response.status_code == 200:
        print("✓ 健康检查通过")
        data = response.json()
        print(f"  状态: {data.get('status', 'unknown')}")
    else:
        print(f"✗ 健康检查失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 无法连接服务器: {e}")
    print()
    print("请确保服务器正在运行:")
    print("  python run.py")
    sys.exit(1)

# 测试2: 前台页面
print()
print("[2/4] 测试前台页面...")
try:
    response = requests.get(f"{base_url}/", timeout=5)
    if response.status_code == 200:
        print("✓ 前台页面可访问")
        print(f"  URL: {base_url}/")
    else:
        print(f"⚠ 前台页面返回状态码: {response.status_code}")
except Exception as e:
    print(f"✗ 前台页面访问失败: {e}")

# 测试3: 管理后台登录页面
print()
print("[3/4] 测试管理后台登录页面...")
try:
    response = requests.get(f"{base_url}/admin/login.html", timeout=5)
    if response.status_code == 200:
        print("✓ 管理后台登录页面可访问")
        print(f"  URL: {base_url}/admin/login.html")
    else:
        print(f"⚠ 登录页面返回状态码: {response.status_code}")
except Exception as e:
    print(f"✗ 登录页面访问失败: {e}")

# 测试4: API文档
print()
print("[4/4] 测试API文档...")
try:
    response = requests.get(f"{base_url}/api/v1/openapi.json", timeout=5)
    if response.status_code == 200:
        print("✓ API文档可访问")
        print(f"  Swagger UI: {base_url}/api/v1/docs")
        print(f"  ReDoc: {base_url}/api/v1/redoc")
    else:
        print(f"⚠ API文档返回状态码: {response.status_code}")
except Exception as e:
    print(f"✗ API文档访问失败: {e}")

print()
print("=" * 70)
print("✓ 服务器测试完成！")
print()
print("登录信息:")
print("  URL: http://localhost:8000/admin/login.html")
print("  用户名: admin")
print("  密码: admin123")
print("=" * 70)
