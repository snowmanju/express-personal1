#!/usr/bin/env python3
"""
API集成属性测试
API Integration Property Tests

**Feature: express-tracking-website, Property 9: API配置完整性**
**验证需求: Requirements 4.2, 4.3**
"""

import sys
import os
import json
import hashlib
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

from hypothesis import given, strategies as st, settings, assume
import pytest
import httpx

# 导入被测试的模块
from app.services.kuaidi100_client import Kuaidi100Client, Kuaidi100APIError


# Hypothesis策略定义
@st.composite
def api_config_strategy(draw):
    """生成API配置参数的策略"""
    return {
        'customer': draw(st.text(
            alphabet='ABCDEF0123456789',
            min_size=32, max_size=32
        )),
        'key': draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=8, max_size=20
        )),
        'secret': draw(st.text(
            alphabet='abcdef0123456789',
            min_size=32, max_size=32
        )),
        'userid': draw(st.text(
            alphabet='abcdef0123456789',
            min_size=32, max_size=32
        )),
        'api_url': draw(st.just('https://poll.kuaidi100.com/poll/query.do'))
    }


@st.composite
def tracking_query_strategy(draw):
    """生成快递查询参数的策略"""
    return {
        'tracking_number': draw(st.text(
            alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=8, max_size=30
        )),
        'company_code': draw(st.sampled_from([
            'auto', 'shentong', 'ems', 'shunfeng', 'yuantong', 
            'yunda', 'zhongtong', 'huitongkuaidi', 'jingdong'
        ])),
        'phone': draw(st.one_of(
            st.none(),
            st.text(alphabet='0123456789', min_size=4, max_size=4)
        ))
    }


@st.composite
def api_response_strategy(draw):
    """生成API响应数据的策略"""
    success = draw(st.booleans())
    
    if success:
        return {
            'result': True,
            'returnCode': '200',
            'message': 'ok',
            'com': draw(st.sampled_from(['shentong', 'ems', 'shunfeng', 'yuantong'])),
            'nu': draw(st.text(
                alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                min_size=8, max_size=30
            )),
            'state': draw(st.sampled_from(['0', '1', '2', '3', '10'])),
            'data': draw(st.lists(
                st.fixed_dictionaries({
                    'time': st.text(min_size=19, max_size=19),  # YYYY-MM-DD HH:MM:SS
                    'ftime': st.text(min_size=19, max_size=19),
                    'context': st.text(min_size=10, max_size=100),
                    'location': st.text(min_size=5, max_size=50)
                }),
                min_size=1, max_size=10
            ))
        }
    else:
        return {
            'result': False,
            'returnCode': draw(st.sampled_from(['500', '501', '502', '503'])),
            'message': draw(st.text(min_size=5, max_size=50))
        }


class TestAPIConfigurationIntegrity:
    """API配置完整性属性测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 保存原始环境变量
        self.original_env = {}
        env_vars = ['KUAIDI100_CUSTOMER', 'KUAIDI100_KEY', 'KUAIDI100_SECRET', 'KUAIDI100_USERID', 'KUAIDI100_API_URL']
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 恢复原始环境变量
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    @given(api_config_strategy())
    @settings(max_examples=10, deadline=None)
    def test_api_configuration_completeness(self, api_config):
        """
        **Feature: express-tracking-website, Property 9: API配置完整性**
        
        属性: 对于任何完整的API配置参数集合，客户端应该能够成功初始化，
        并且所有认证参数都应该正确设置和可访问
        **验证需求: Requirements 4.2**
        """
        # 设置环境变量
        os.environ['KUAIDI100_CUSTOMER'] = api_config['customer']
        os.environ['KUAIDI100_KEY'] = api_config['key']
        os.environ['KUAIDI100_SECRET'] = api_config['secret']
        os.environ['KUAIDI100_USERID'] = api_config['userid']
        os.environ['KUAIDI100_API_URL'] = api_config['api_url']
        
        # 创建客户端实例
        client = Kuaidi100Client()
        
        # 验证所有配置参数都正确设置
        assert client.customer == api_config['customer'], \
            f"Customer配置不匹配: {client.customer} != {api_config['customer']}"
        
        assert client.key == api_config['key'], \
            f"Key配置不匹配: {client.key} != {api_config['key']}"
        
        assert client.secret == api_config['secret'], \
            f"Secret配置不匹配: {client.secret} != {api_config['secret']}"
        
        assert client.userid == api_config['userid'], \
            f"UserID配置不匹配: {client.userid} != {api_config['userid']}"
        
        assert client.api_url == api_config['api_url'], \
            f"API URL配置不匹配: {client.api_url} != {api_config['api_url']}"
        
        # 验证配置验证方法不抛出异常
        try:
            client._validate_config()
        except ValueError:
            pytest.fail("完整的配置参数不应该导致验证失败")
    
    @given(
        api_config_strategy(),
        tracking_query_strategy()
    )
    @settings(max_examples=10, deadline=None)
    def test_signature_generation_consistency(self, api_config, query_params):
        """
        **Feature: express-tracking-website, Property 9: API配置完整性**
        
        属性: 对于任何API配置和查询参数组合，签名生成应该是确定性的，
        相同的输入应该产生相同的MD5签名，且签名格式应该符合规范
        **验证需求: Requirements 4.2**
        """
        # 设置环境变量
        os.environ['KUAIDI100_CUSTOMER'] = api_config['customer']
        os.environ['KUAIDI100_KEY'] = api_config['key']
        os.environ['KUAIDI100_SECRET'] = api_config['secret']
        os.environ['KUAIDI100_USERID'] = api_config['userid']
        os.environ['KUAIDI100_API_URL'] = api_config['api_url']
        
        client = Kuaidi100Client()
        
        # 构建查询参数
        param_data = {
            "com": query_params['company_code'],
            "num": query_params['tracking_number']
        }
        
        if query_params['phone']:
            param_data["phone"] = query_params['phone']
        
        param = json.dumps(param_data, separators=(',', ':'), ensure_ascii=False)
        
        # 生成签名
        signature1 = client._generate_signature(param)
        signature2 = client._generate_signature(param)
        
        # 验证签名一致性
        assert signature1 == signature2, \
            f"相同输入应该产生相同签名: {signature1} != {signature2}"
        
        # 验证签名格式
        assert isinstance(signature1, str), "签名应该是字符串类型"
        assert len(signature1) == 32, f"MD5签名长度应该是32位: {len(signature1)}"
        assert signature1.isupper(), "签名应该是大写格式"
        assert all(c in '0123456789ABCDEF' for c in signature1), \
            f"签名应该只包含十六进制字符: {signature1}"
        
        # 验证签名算法正确性
        expected_sign_string = param + api_config['key'] + api_config['customer']
        expected_signature = hashlib.md5(expected_sign_string.encode('utf-8')).hexdigest().upper()
        
        assert signature1 == expected_signature, \
            f"签名算法不正确: {signature1} != {expected_signature}"
    
    @given(
        api_config_strategy(),
        tracking_query_strategy(),
        api_response_strategy()
    )
    @settings(max_examples=10, deadline=None)
    def test_request_parameter_integrity(self, api_config, query_params, mock_response):
        """
        **Feature: express-tracking-website, Property 9: API配置完整性**
        
        属性: 对于任何API调用，请求应该包含完整的认证参数（customer、sign、param），
        且参数格式应该符合快递100 API规范
        **验证需求: Requirements 4.2**
        """
        # 设置环境变量
        os.environ['KUAIDI100_CUSTOMER'] = api_config['customer']
        os.environ['KUAIDI100_KEY'] = api_config['key']
        os.environ['KUAIDI100_SECRET'] = api_config['secret']
        os.environ['KUAIDI100_USERID'] = api_config['userid']
        os.environ['KUAIDI100_API_URL'] = api_config['api_url']
        
        client = Kuaidi100Client()
        
        # 模拟HTTP响应
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        
        # 捕获实际的请求参数
        captured_request_data = {}
        
        def mock_post(*args, **kwargs):
            captured_request_data.update(kwargs.get('data', {}))
            return mock_http_response
        
        # 使用mock替换HTTP客户端
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # 执行查询 - 使用asyncio.run来运行异步函数
            import asyncio
            try:
                asyncio.run(client.query_tracking(
                    query_params['tracking_number'],
                    query_params['company_code'],
                    query_params['phone']
                ))
            except Exception:
                # 忽略可能的API错误，我们只关心请求参数
                pass
        
        # 验证请求参数完整性
        assert 'customer' in captured_request_data, "请求应该包含customer参数"
        assert 'sign' in captured_request_data, "请求应该包含sign参数"
        assert 'param' in captured_request_data, "请求应该包含param参数"
        
        # 验证customer参数正确
        assert captured_request_data['customer'] == api_config['customer'], \
            f"Customer参数不正确: {captured_request_data['customer']} != {api_config['customer']}"
        
        # 验证param参数格式
        param_str = captured_request_data['param']
        try:
            param_data = json.loads(param_str)
        except json.JSONDecodeError:
            pytest.fail(f"param参数不是有效的JSON: {param_str}")
        
        assert 'com' in param_data, "param应该包含com字段"
        assert 'num' in param_data, "param应该包含num字段"
        assert param_data['com'] == query_params['company_code'], \
            f"com字段不正确: {param_data['com']} != {query_params['company_code']}"
        assert param_data['num'] == query_params['tracking_number'], \
            f"num字段不正确: {param_data['num']} != {query_params['tracking_number']}"
        
        if query_params['phone']:
            assert 'phone' in param_data, "当提供phone参数时，param应该包含phone字段"
            assert param_data['phone'] == query_params['phone'], \
                f"phone字段不正确: {param_data['phone']} != {query_params['phone']}"
        
        # 验证签名正确性
        expected_signature = client._generate_signature(param_str)
        assert captured_request_data['sign'] == expected_signature, \
            f"签名不正确: {captured_request_data['sign']} != {expected_signature}"
    
    @given(api_response_strategy())
    @settings(max_examples=10, deadline=None)
    def test_json_response_parsing_integrity(self, mock_response):
        """
        **Feature: express-tracking-website, Property 9: API配置完整性**
        
        属性: 对于任何有效的JSON响应，系统应该正确解析并提取快递信息，
        返回的结果应该包含所有必要的字段和正确的数据类型
        **验证需求: Requirements 4.3**
        """
        # 使用默认配置创建客户端
        client = Kuaidi100Client()
        
        # 模拟HTTP响应
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        
        # 使用mock替换HTTP客户端
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_http_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # 执行查询 - 使用asyncio.run来运行异步函数
            import asyncio
            result = asyncio.run(client.query_tracking('TEST123456789', 'auto'))
        
        # 验证返回结果的基本结构
        assert isinstance(result, dict), "返回结果应该是字典类型"
        assert 'success' in result, "返回结果应该包含success字段"
        assert 'tracking_number' in result, "返回结果应该包含tracking_number字段"
        assert 'company_code' in result, "返回结果应该包含company_code字段"
        assert 'query_time' in result, "返回结果应该包含query_time字段"
        
        # 验证基本字段类型
        assert isinstance(result['success'], bool), "success字段应该是布尔类型"
        assert isinstance(result['tracking_number'], str), "tracking_number字段应该是字符串类型"
        assert isinstance(result['company_code'], str), "company_code字段应该是字符串类型"
        assert isinstance(result['query_time'], int), "query_time字段应该是整数类型"
        
        if mock_response.get('result'):
            # 成功响应的验证
            assert result['success'] is True, "API成功响应时success应该为True"
            assert 'company_name' in result, "成功响应应该包含company_name字段"
            assert 'status' in result, "成功响应应该包含status字段"
            assert 'tracks' in result, "成功响应应该包含tracks字段"
            assert 'raw_response' in result, "成功响应应该包含raw_response字段"
            
            # 验证解析的数据正确性
            assert result['company_name'] == mock_response.get('com', ''), \
                f"company_name解析不正确: {result['company_name']} != {mock_response.get('com', '')}"
            
            assert result['status'] == mock_response.get('state', ''), \
                f"status解析不正确: {result['status']} != {mock_response.get('state', '')}"
            
            assert result['tracks'] == mock_response.get('data', []), \
                f"tracks解析不正确: {result['tracks']} != {mock_response.get('data', [])}"
            
            assert result['raw_response'] == mock_response, \
                "raw_response应该包含完整的原始响应"
        else:
            # 失败响应的验证
            assert result['success'] is False, "API失败响应时success应该为False"
            assert 'error' in result, "失败响应应该包含error字段"
            assert isinstance(result['error'], str), "error字段应该是字符串类型"
    
    @given(st.lists(st.sampled_from(['customer', 'key', 'secret', 'userid']), min_size=1, max_size=4, unique=True))
    @settings(max_examples=5, deadline=None)
    def test_missing_configuration_detection(self, missing_configs):
        """
        **Feature: express-tracking-website, Property 9: API配置完整性**
        
        属性: 对于任何缺失的必需配置参数，系统应该在初始化时检测并报告配置错误
        **验证需求: Requirements 4.2**
        """
        # 设置所有配置为空值来模拟缺失配置
        config_mapping = {
            'customer': 'KUAIDI100_CUSTOMER',
            'key': 'KUAIDI100_KEY', 
            'secret': 'KUAIDI100_SECRET',
            'userid': 'KUAIDI100_USERID'
        }
        
        default_values = {
            'customer': '3564B6CF145FA93724CE18C1FB149036',
            'key': 'fypLxFrg3636',
            'secret': '8fa1052ba57e4d9ca0427938a77e2e30',
            'userid': 'a1ffc21f3de94cf5bdd908faf3bbc81d'
        }
        
        # 设置所有配置，但将缺失的配置设为空字符串
        for config_name, env_var in config_mapping.items():
            if config_name in missing_configs:
                os.environ[env_var] = ""  # 设置为空字符串
            else:
                os.environ[env_var] = default_values[config_name]
        
        # 验证缺失配置会导致初始化失败
        with pytest.raises(ValueError) as exc_info:
            Kuaidi100Client()
        
        error_message = str(exc_info.value)
        assert "缺少必需的快递100 API配置参数" in error_message, \
            f"错误消息应该指出缺少配置参数: {error_message}"
        
        # 验证错误消息包含所有缺失的配置项
        for missing_config in missing_configs:
            assert missing_config in error_message, \
                f"错误消息应该包含缺失的配置项 {missing_config}: {error_message}"


def main():
    """运行属性测试"""
    print("=" * 60)
    print("API集成配置完整性属性测试")
    print("API Integration Configuration Integrity Property Tests")
    print("=" * 60)
    
    # 运行测试
    import pytest
    
    # 运行特定的测试类
    exit_code = pytest.main([
        __file__ + "::TestAPIConfigurationIntegrity",
        "-v",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n🎉 所有属性测试通过!")
        print("✅ API配置完整性属性验证成功")
        print("\n📝 验证的属性:")
        print("- API配置参数完整性和正确性")
        print("- 签名生成的确定性和格式正确性")
        print("- 请求参数的完整性和格式规范")
        print("- JSON响应解析的正确性和完整性")
        print("- 缺失配置的检测和错误报告")
    else:
        print("\n❌ 部分属性测试失败")
    
    return exit_code == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)