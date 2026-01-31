"""
直接测试快递100 API
"""

import hashlib
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 配置
KUAIDI100_API_URL = os.getenv("KUAIDI100_API_URL", "https://poll.kuaidi100.com/poll/query.do")
KUAIDI100_CUSTOMER = os.getenv("KUAIDI100_CUSTOMER")
KUAIDI100_KEY = os.getenv("KUAIDI100_KEY")

tracking_number = "JT5452262832783"
company_code = "auto"

print("=" * 70)
print("直接测试快递100 API")
print("=" * 70)
print()
print(f"API URL: {KUAIDI100_API_URL}")
print(f"Customer: {KUAIDI100_CUSTOMER}")
print(f"Key: {KUAIDI100_KEY[:10]}...")
print(f"快递单号: {tracking_number}")
print(f"快递公司: {company_code}")
print()

# 构建查询参数
param_data = {
    "com": company_code,
    "num": tracking_number
}

param = json.dumps(param_data, separators=(',', ':'), ensure_ascii=False)
print(f"param: {param}")

# 生成签名
sign_string = param + KUAIDI100_KEY + KUAIDI100_CUSTOMER
signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
print(f"signature: {signature}")
print()

# 构建请求数据
request_data = {
    "customer": KUAIDI100_CUSTOMER,
    "sign": signature,
    "param": param
}

print("发送请求...")
print()

try:
    response = requests.post(
        KUAIDI100_API_URL,
        data=request_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15
    )
    
    print(f"HTTP状态码: {response.status_code}")
    print()
    
    print("原始响应:")
    print(response.text)
    print()
    
    try:
        response_data = response.json()
        print("JSON响应:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        print()
        
        print("=" * 70)
        print("响应分析:")
        print("=" * 70)
        print(f"result: {response_data.get('result')}")
        print(f"returnCode: {response_data.get('returnCode')}")
        print(f"message: {response_data.get('message')}")
        print()
        
        if response_data.get('result'):
            print("✓ 查询成功")
            print(f"com: {response_data.get('com')}")
            print(f"nu: {response_data.get('nu')}")
            print(f"state: {response_data.get('state')}")
            print(f"data数组长度: {len(response_data.get('data', []))}")
            
            if response_data.get('data'):
                print()
                print("物流轨迹（前3条）:")
                for i, item in enumerate(response_data['data'][:3]):
                    print(f"  [{i+1}] {item.get('time')} - {item.get('context')}")
        else:
            print("✗ 查询失败")
            print(f"错误消息: {response_data.get('message')}")
            print(f"返回代码: {response_data.get('returnCode')}")
            
    except json.JSONDecodeError:
        print("⚠ 响应不是有效的JSON")
        
except Exception as e:
    print(f"请求失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
