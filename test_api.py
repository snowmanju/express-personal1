#!/usr/bin/env python3
"""
快递100 API测试脚本
"""

import asyncio
import json
import hashlib
import httpx

async def test_kuaidi100_api():
    """测试快递100 API"""
    
    # API配置
    api_url = "https://poll.kuaidi100.com/poll/query.do"
    customer = "3564B6CF145FA93724CE18C1FB149036"
    key = "fypLxFrg3636"
    
    # 测试数据
    tracking_number = "YT8834090695021"
    company_code = "yuantong"
    
    print(f"🔍 测试快递单号: {tracking_number}")
    print(f"📦 快递公司: {company_code}")
    print(f"🌐 API地址: {api_url}")
    print(f"👤 客户标识: {customer}")
    print(f"🔑 授权密钥: {key}")
    print("-" * 50)
    
    # 构建查询参数
    param_data = {
        "com": company_code,
        "num": tracking_number
    }
    
    param = json.dumps(param_data, separators=(',', ':'), ensure_ascii=False)
    print(f"📋 查询参数: {param}")
    
    # 生成签名
    sign_string = param + key + customer
    signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
    print(f"✍️  签名字符串: {sign_string}")
    print(f"🔐 生成签名: {signature}")
    
    # 构建请求数据
    request_data = {
        "customer": customer,
        "sign": signature,
        "param": param
    }
    
    print(f"📤 请求数据: {request_data}")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("🚀 发送API请求...")
            response = await client.post(
                api_url,
                data=request_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print(f"📊 HTTP状态码: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            response_text = response.text
            print(f"📄 原始响应: {response_text}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"📦 解析后数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    if response_data.get('result'):
                        print("✅ 查询成功!")
                        tracks = response_data.get('data', [])
                        print(f"🚛 物流轨迹数量: {len(tracks)}")
                        for i, track in enumerate(tracks):
                            print(f"  {i+1}. {track.get('ftime', '')} - {track.get('context', '')}")
                    else:
                        print("❌ 查询失败!")
                        print(f"错误信息: {response_data.get('message', '未知错误')}")
                        print(f"返回码: {response_data.get('returnCode', '')}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_kuaidi100_api())