"""
测试特定快递单号的查询
"""

import requests
import json

tracking_number = "JT5452262832783"
base_url = "http://localhost:8000"

print("=" * 70)
print(f"测试快递单号: {tracking_number}")
print("=" * 70)
print()

try:
    response = requests.post(
        f"{base_url}/api/v1/tracking/query",
        json={
            "tracking_number": tracking_number,
            "company_code": "auto"
        },
        timeout=15
    )
    
    print(f"HTTP状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        print("=" * 70)
        print("响应分析:")
        print("=" * 70)
        print(f"success: {data.get('success')}")
        print(f"query_type: {data.get('query_type')}")
        print(f"has_package_association: {data.get('has_package_association')}")
        print()
        
        if data.get('tracking_info'):
            tracking_info = data['tracking_info']
            print("tracking_info 内容:")
            print(f"  - com: {tracking_info.get('com')}")
            print(f"  - company: {tracking_info.get('company')}")
            print(f"  - state: {tracking_info.get('state')}")
            print(f"  - nu: {tracking_info.get('nu')}")
            print(f"  - data数组长度: {len(tracking_info.get('data', []))}")
            print()
            
            if tracking_info.get('data'):
                print("物流轨迹（前3条）:")
                for i, item in enumerate(tracking_info['data'][:3]):
                    print(f"  [{i+1}] {item.get('time')} - {item.get('context')}")
            else:
                print("⚠ data数组为空")
        else:
            print("⚠ tracking_info 不存在")
            if data.get('error'):
                print(f"错误信息: {data.get('error')}")
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
