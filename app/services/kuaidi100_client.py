"""
快递100 API客户端
Kuaidi100 API Client for express tracking services
"""

import hashlib
import json
import time
import logging
import os
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class Kuaidi100APIError(Exception):
    """快递100 API异常类"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class Kuaidi100Client:
    """
    快递100 API客户端类
    
    提供快递查询功能，包括签名生成、请求重试机制和错误处理
    """
    
    def __init__(self):
        """初始化客户端配置"""
        # 直接从环境变量获取配置，避免依赖config模块
        self.api_url = os.getenv("KUAIDI100_API_URL", "https://poll.kuaidi100.com/poll/query.do")
        self.customer = os.getenv("KUAIDI100_CUSTOMER", "3564B6CF145FA93724CE18C1FB149036")
        self.key = os.getenv("KUAIDI100_KEY", "fypLxFrg3636")
        self.secret = os.getenv("KUAIDI100_SECRET", "8fa1052ba57e4d9ca0427938a77e2e30")
        self.userid = os.getenv("KUAIDI100_USERID", "a1ffc21f3de94cf5bdd908faf3bbc81d")
        
        # 验证必需的配置参数
        self._validate_config()
        
        # HTTP客户端配置
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0  # 初始重试延迟（秒）
        
    def _validate_config(self) -> None:
        """验证API配置参数的完整性"""
        required_configs = {
            'customer': self.customer,
            'key': self.key,
            'secret': self.secret,
            'userid': self.userid,
            'api_url': self.api_url
        }
        
        missing_configs = [name for name, value in required_configs.items() if not value]
        
        if missing_configs:
            raise ValueError(f"缺少必需的快递100 API配置参数: {', '.join(missing_configs)}")
    
    def _generate_signature(self, param: str) -> str:
        """
        生成API请求签名
        
        Args:
            param: JSON格式的查询参数字符串
            
        Returns:
            MD5签名字符串（大写）
        """
        # 签名算法: MD5(param + key + customer).toUpperCase()
        sign_string = param + self.key + self.customer
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
        
        logger.debug(f"Generated signature for param: {param[:50]}...")
        return signature
    
    async def _make_request(self, data: Dict[str, Any], retry_count: int = 0) -> Dict[str, Any]:
        """
        发送HTTP请求到快递100 API
        
        Args:
            data: 请求数据
            retry_count: 当前重试次数
            
        Returns:
            API响应数据
            
        Raises:
            Kuaidi100APIError: API请求失败时抛出
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                # 记录请求日志
                logger.info(f"快递100 API请求: {self.api_url}, 状态码: {response.status_code}")
                
                # 检查HTTP状态码
                if response.status_code != 200:
                    # 提供用户友好的HTTP错误消息
                    if response.status_code == 400:
                        error_msg = "请求参数错误，请检查快递单号格式"
                    elif response.status_code == 401:
                        error_msg = "API认证失败，请检查配置"
                    elif response.status_code == 403:
                        error_msg = "API访问被拒绝，请检查权限配置"
                    elif response.status_code == 404:
                        error_msg = "API服务不可用"
                    elif response.status_code == 429:
                        error_msg = "请求过于频繁，请稍后重试"
                    elif response.status_code >= 500:
                        error_msg = "服务器错误，请稍后重试"
                    else:
                        error_msg = f"HTTP请求失败，状态码: {response.status_code}"
                    
                    raise Kuaidi100APIError(error_msg, status_code=response.status_code)
                
                # 解析JSON响应
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    raise Kuaidi100APIError("服务器响应格式错误，请稍后重试")
                
                # 检查API响应状态
                # 快递100 API成功时返回 status="200" 和 message="ok"，没有result字段
                status = response_data.get('status', '')
                message = response_data.get('message', '')
                
                # 判断是否成功：status为"200"或message为"ok"
                if status == "200" or (message == "ok" and response_data.get('data')):
                    # 查询成功
                    return response_data
                
                # 查询失败，处理错误
                error_msg = message if message and message != "ok" else response_data.get('returnCode', '未知错误')
                return_code = response_data.get('returnCode', '')
                
                # 提供更友好的错误消息
                if '不存在' in error_msg or '过期' in error_msg:
                    friendly_msg = f"快递单号不存在或已过期: {error_msg}"
                elif '签名错误' in error_msg:
                    friendly_msg = f"API配置错误: {error_msg}"
                elif '参数错误' in error_msg:
                    friendly_msg = f"查询参数错误: {error_msg}"
                elif '繁忙' in error_msg or '重试' in error_msg:
                    friendly_msg = f"服务繁忙: {error_msg}"
                else:
                    friendly_msg = f"查询失败: {error_msg}"
                
                raise Kuaidi100APIError(friendly_msg, response_data=response_data)
                
        except httpx.TimeoutException:
            error_msg = "网络请求超时，请检查网络连接后重试"
            logger.warning(f"{error_msg}, 重试次数: {retry_count}")
            
            if retry_count < self.max_retries:
                # 指数退避重试
                delay = self.retry_delay * (2 ** retry_count)
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                return await self._make_request(data, retry_count + 1)
            else:
                raise Kuaidi100APIError(error_msg)
                
        except httpx.RequestError as e:
            error_msg = "网络连接失败，请检查网络后重试"
            logger.warning(f"{error_msg}, 重试次数: {retry_count}")
            
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                return await self._make_request(data, retry_count + 1)
            else:
                raise Kuaidi100APIError(error_msg)
    
    async def query_tracking(self, tracking_number: str, company_code: str = "auto", phone: Optional[str] = None) -> Dict[str, Any]:
        """
        查询快递信息
        
        Args:
            tracking_number: 快递单号
            company_code: 快递公司编码，默认为"auto"自动识别
            phone: 手机号后四位（可选，某些快递公司需要）
            
        Returns:
            包含快递信息的字典
            
        Raises:
            Kuaidi100APIError: 查询失败时抛出
        """
        # 构建查询参数
        param_data = {
            "com": company_code,
            "num": tracking_number
        }
        
        # 添加可选的手机号参数
        if phone:
            param_data["phone"] = phone
        
        # 转换为JSON字符串
        param = json.dumps(param_data, separators=(',', ':'), ensure_ascii=False)
        
        # 生成签名
        signature = self._generate_signature(param)
        
        # 构建请求数据
        request_data = {
            "customer": self.customer,
            "sign": signature,
            "param": param
        }
        
        logger.info(f"查询快递单号: {tracking_number}, 快递公司: {company_code}")
        
        try:
            # 发送请求
            response_data = await self._make_request(request_data)
            
            # 处理成功响应
            result = {
                "success": True,
                "tracking_number": tracking_number,
                "company_code": company_code,
                "company_name": response_data.get("com", ""),
                "status": response_data.get("state", ""),
                "tracks": response_data.get("data", []),
                "query_time": int(time.time()),
                "raw_response": response_data
            }
            
            logger.info(f"快递查询成功: {tracking_number}, 状态: {result['status']}")
            return result
            
        except Kuaidi100APIError as e:
            logger.error(f"快递查询失败: {tracking_number}, 错误: {e.message}")
            
            # 返回失败结果
            return {
                "success": False,
                "tracking_number": tracking_number,
                "company_code": company_code,
                "error": e.message,
                "error_code": getattr(e, 'status_code', None),
                "query_time": int(time.time())
            }
            
        except Exception as e:
            # 处理未预期的异常，提供用户友好的错误消息
            logger.error(f"快递查询发生未预期错误: {tracking_number}, 异常: {str(e)}")
            
            # 返回通用错误消息，不暴露系统内部异常信息
            return {
                "success": False,
                "tracking_number": tracking_number,
                "company_code": company_code,
                "error": "系统异常，请稍后重试",
                "query_time": int(time.time())
            }
    
    async def batch_query(self, tracking_numbers: list[str], company_code: str = "auto") -> Dict[str, Any]:
        """
        批量查询快递信息
        
        Args:
            tracking_numbers: 快递单号列表
            company_code: 快递公司编码
            
        Returns:
            包含所有查询结果的字典
        """
        results = []
        
        for tracking_number in tracking_numbers:
            try:
                result = await self.query_tracking(tracking_number, company_code)
                results.append(result)
            except Exception as e:
                logger.error(f"批量查询中单号 {tracking_number} 失败: {str(e)}")
                results.append({
                    "success": False,
                    "tracking_number": tracking_number,
                    "error": str(e),
                    "query_time": int(time.time())
                })
        
        return {
            "total": len(tracking_numbers),
            "success_count": sum(1 for r in results if r.get("success")),
            "failed_count": sum(1 for r in results if not r.get("success")),
            "results": results
        }
    
    def get_supported_companies(self) -> Dict[str, str]:
        """
        获取支持的快递公司列表
        
        Returns:
            快递公司编码和名称的映射字典
        """
        # 常用快递公司编码映射
        return {
            "auto": "自动识别",
            "shentong": "申通快递",
            "ems": "EMS",
            "shunfeng": "顺丰速运",
            "yuantong": "圆通速递",
            "yunda": "韵达速递",
            "zhongtong": "中通快递",
            "huitongkuaidi": "百世快递",
            "tiantian": "天天快递",
            "jingdong": "京东快递",
            "debangwuliu": "德邦快递",
            "zhaijisong": "宅急送",
            "fedex": "FedEx",
            "ups": "UPS",
            "dhl": "DHL"
        }