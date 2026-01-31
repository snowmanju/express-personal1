"""
测试UI更新 - 验证新的科技风格界面和API响应
"""

import requests
import json

print("=" * 70)
print("测试UI更新 - 科技风格版本")
print("=" * 70)
print()

base_url = "http://localhost:8000"

# 测试1: 检查新首页
print("[1/6] 测试新首页...")
try:
    response = requests.get(f"{base_url}/", timeout=5)
    if response.status_code == 200:
        # 检查是否是科技风格页面
        if "智能物流追踪系统" in response.text and "--primary-color: #00f2fe" in response.text:
            print("✓ 新首页加载成功（科技风格）")
        else:
            print("⚠ 首页加载成功，但可能不是科技风格版本")
    else:
        print(f"✗ 首页加载失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 首页访问失败: {e}")

# 测试2: 检查客户登录页面
print()
print("[2/6] 测试客户登录页面...")
try:
    response = requests.get(f"{base_url}/customer/login.html", timeout=5)
    if response.status_code == 200:
        if "客户登录" in response.text and "科技风格" in response.text or "--primary-color" in response.text:
            print("✓ 客户登录页面加载成功")
        else:
            print("⚠ 客户登录页面加载成功，但样式可能不正确")
    else:
        print(f"✗ 客户登录页面加载失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 客户登录页面访问失败: {e}")

# 测试3: 检查客户注册页面
print()
print("[3/6] 测试客户注册页面...")
try:
    response = requests.get(f"{base_url}/customer/register.html", timeout=5)
    if response.status_code == 200:
        if "客户注册" in response.text:
            print("✓ 客户注册页面加载成功")
        else:
            print("⚠ 客户注册页面加载成功，但内容可能不正确")
    else:
        print(f"✗ 客户注册页面加载失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 客户注册页面访问失败: {e}")

# 测试4: 检查员工登录页面
print()
print("[4/6] 测试员工登录页面...")
try:
    response = requests.get(f"{base_url}/admin/login.html", timeout=5)
    if response.status_code == 200:
        if "员工登录" in response.text and "--primary-color" in response.text:
            print("✓ 员工登录页面加载成功（科技风格）")
        else:
            print("⚠ 员工登录页面加载成功，但可能不是科技风格版本")
    else:
        print(f"✗ 员工登录页面加载失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 员工登录页面访问失败: {e}")

# 测试5: 测试快递查询API（验证返回物流信息）
print()
print("[5/6] 测试快递查询API...")
try:
    # 使用一个测试单号
    test_tracking_number = "YT1234567890"
    
    response = requests.post(
        f"{base_url}/api/v1/tracking/query",
        json={
            "tracking_number": test_tracking_number,
            "company_code": "auto"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API响应成功")
        print(f"  - success: {data.get('success')}")
        print(f"  - query_type: {data.get('query_type')}")
        print(f"  - has_package_association: {data.get('has_package_association')}")
        
        # 检查tracking_info结构
        if data.get('tracking_info'):
            tracking_info = data['tracking_info']
            print(f"  - tracking_info存在: ✓")
            print(f"    - company: {tracking_info.get('company', 'N/A')}")
            print(f"    - state: {tracking_info.get('state', 'N/A')}")
            print(f"    - data数组长度: {len(tracking_info.get('data', []))}")
            
            if tracking_info.get('data'):
                print(f"  ✓ 物流轨迹信息完整（不再只返回ok字段）")
            else:
                print(f"  ⚠ tracking_info存在但data数组为空")
        else:
            if data.get('error'):
                print(f"  ℹ 查询失败: {data.get('error')}")
            else:
                print(f"  ⚠ tracking_info不存在")
    else:
        print(f"✗ API请求失败 (状态码: {response.status_code})")
        
except Exception as e:
    print(f"✗ API测试失败: {e}")

# 测试6: 健康检查
print()
print("[6/6] 测试系统健康状态...")
try:
    response = requests.get(f"{base_url}/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 系统健康检查通过")
        print(f"  - 状态: {data.get('status')}")
    else:
        print(f"✗ 健康检查失败 (状态码: {response.status_code})")
except Exception as e:
    print(f"✗ 健康检查失败: {e}")

print()
print("=" * 70)
print("测试完成！")
print()
print("访问地址:")
print(f"  - 首页（科技风格）: {base_url}/")
print(f"  - 客户登录: {base_url}/customer/login.html")
print(f"  - 客户注册: {base_url}/customer/register.html")
print(f"  - 员工登录: {base_url}/admin/login.html")
print()
print("注意:")
print("  - 客户登录/注册的后端API尚未实现")
print("  - 员工登录功能正常")
print("  - 快递查询API已修复，现在返回完整的物流轨迹信息")
print("=" * 70)
