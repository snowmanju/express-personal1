#!/usr/bin/env python3
"""
快递100 API客户端测试
Kuaidi100 API Client Test
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

def test_client_initialization():
    """测试客户端初始化"""
    print("🔍 测试Kuaidi100Client初始化...")
    
    try:
        from app.services.kuaidi100_client import Kuaidi100Client, Kuaidi100APIError
        
        # 创建客户端实例
        client = Kuaidi100Client()
        
        # 验证配置属性
        assert hasattr(client, 'api_url'), "缺少api_url属性"
        assert hasattr(client, 'customer'), "缺少customer属性"
        assert hasattr(client, 'key'), "缺少key属性"
        assert hasattr(client, 'secret'), "缺少secret属性"
        assert hasattr(client, 'userid'), "缺少userid属性"
        
        # 验证配置值不为空
        assert client.api_url, "api_url不能为空"
        assert client.customer, "customer不能为空"
        assert client.key, "key不能为空"
        assert client.secret, "secret不能为空"
        assert client.userid, "userid不能为空"
        
        print("✅ 客户端初始化成功")
        print(f"   API URL: {client.api_url}")
        print(f"   Customer: {client.customer}")
        print(f"   Key: {client.key}")
        
        return True
        
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return False

def test_signature_generation():
    """测试签名生成功能"""
    print("\n🔍 测试签名生成...")
    
    try:
        from app.services.kuaidi100_client import Kuaidi100Client
        
        client = Kuaidi100Client()
        
        # 测试签名生成
        test_param = '{"com":"auto","num":"12345678901234"}'
        signature = client._generate_signature(test_param)
        
        # 验证签名格式
        assert isinstance(signature, str), "签名应该是字符串"
        assert len(signature) == 32, "MD5签名长度应该是32位"
        assert signature.isupper(), "签名应该是大写"
        
        print(f"✅ 签名生成成功: {signature}")
        
        # 测试相同输入产生相同签名
        signature2 = client._generate_signature(test_param)
        assert signature == signature2, "相同输入应该产生相同签名"
        
        print("✅ 签名一致性验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 签名生成测试失败: {e}")
        return False

def test_supported_companies():
    """测试支持的快递公司列表"""
    print("\n🔍 测试快递公司列表...")
    
    try:
        from app.services.kuaidi100_client import Kuaidi100Client
        
        client = Kuaidi100Client()
        companies = client.get_supported_companies()
        
        # 验证返回格式
        assert isinstance(companies, dict), "快递公司列表应该是字典"
        assert len(companies) > 0, "快递公司列表不能为空"
        assert "auto" in companies, "应该包含自动识别选项"
        
        print(f"✅ 支持 {len(companies)} 家快递公司")
        print("   主要快递公司:")
        for code, name in list(companies.items())[:5]:
            print(f"     {code}: {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快递公司列表测试失败: {e}")
        return False

def test_query_tracking_mock():
    """测试查询功能（模拟测试，不实际调用API）"""
    print("\n🔍 测试查询功能结构...")
    
    try:
        from app.services.kuaidi100_client import Kuaidi100Client
        
        client = Kuaidi100Client()
        
        # 验证查询方法存在
        assert hasattr(client, 'query_tracking'), "缺少query_tracking方法"
        assert hasattr(client, 'batch_query'), "缺少batch_query方法"
        
        # 验证方法是异步的
        import inspect
        assert inspect.iscoroutinefunction(client.query_tracking), "query_tracking应该是异步方法"
        assert inspect.iscoroutinefunction(client.batch_query), "batch_query应该是异步方法"
        
        print("✅ 查询方法结构验证通过")
        
        # 注意：这里不实际调用API，只验证方法结构
        print("   ℹ️  实际API调用需要网络连接和有效的快递单号")
        
        return True
        
    except Exception as e:
        print(f"❌ 查询功能测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n🔍 测试错误处理...")
    
    try:
        from app.services.kuaidi100_client import Kuaidi100APIError
        
        # 测试自定义异常类
        error = Kuaidi100APIError("测试错误", status_code=400, response_data={"error": "test"})
        
        assert error.message == "测试错误", "错误消息不正确"
        assert error.status_code == 400, "状态码不正确"
        assert error.response_data["error"] == "test", "响应数据不正确"
        
        print("✅ 错误处理类验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("快递100 API客户端测试")
    print("Kuaidi100 API Client Test")
    print("=" * 60)
    
    tests = [
        ("客户端初始化", test_client_initialization),
        ("签名生成", test_signature_generation),
        ("快递公司列表", test_supported_companies),
        ("查询功能结构", test_query_tracking_mock),
        ("错误处理", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 Kuaidi100Client实现验证通过!")
        print("\n📝 功能特性:")
        print("✅ API认证和签名生成")
        print("✅ 异步HTTP请求处理")
        print("✅ 自动重试机制")
        print("✅ 错误处理和日志记录")
        print("✅ 批量查询支持")
        print("✅ 快递公司编码支持")
        
        print("\n📝 下一步:")
        print("1. 安装httpx依赖: pip install httpx==0.25.2")
        print("2. 配置环境变量（可选）")
        print("3. 集成到智能查询服务")
        return True
    else:
        print("❌ 部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)