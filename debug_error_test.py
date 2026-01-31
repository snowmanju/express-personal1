#!/usr/bin/env python3
"""
Debug API error handling test
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

import httpx
from app.services.kuaidi100_client import Kuaidi100Client, Kuaidi100APIError

# 设置测试环境变量
os.environ['KUAIDI100_CUSTOMER'] = '3564B6CF145FA93724CE18C1FB149036'
os.environ['KUAIDI100_KEY'] = 'fypLxFrg3636'
os.environ['KUAIDI100_SECRET'] = '8fa1052ba57e4d9ca0427938a77e2e30'
os.environ['KUAIDI100_USERID'] = 'a1ffc21f3de94cf5bdd908faf3bbc81d'
os.environ['KUAIDI100_API_URL'] = 'https://poll.kuaidi100.com/poll/query.do'

def test_simple_network_error():
    """简单的网络错误测试"""
    client = Kuaidi100Client()
    
    # 记录重试次数
    retry_count = 0
    
    def mock_post_with_retries(*args, **kwargs):
        nonlocal retry_count
        retry_count += 1
        print(f"Mock post called, retry count: {retry_count}")
        raise httpx.TimeoutException("Request timeout")
    
    # 使用mock替换HTTP客户端
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = mock_post_with_retries
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        
        # 执行查询
        result = asyncio.run(client.query_tracking('TEST123456789', 'auto'))
        print(f"Result: {result}")
        print(f"Retry count: {retry_count}")
        print(f"Max retries: {client.max_retries}")

if __name__ == "__main__":
    test_simple_network_error()