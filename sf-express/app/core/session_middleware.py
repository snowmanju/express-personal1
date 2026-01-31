"""
会话管理中间件 (Session Management Middleware)
处理会话超时检查和自动注销
"""

from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.session_service import session_service


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """
    会话超时中间件
    自动检查会话状态并处理超时情况
    """
    
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        # 不需要会话检查的路径
        self.excluded_paths = excluded_paths or [
            "/api/v1/admin/login",
            "/api/v1/tracking/query",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/static"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并检查会话状态
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 检查是否是需要会话验证的路径
        if self._should_check_session(request):
            session_check_result = await self._check_session(request)
            if session_check_result is not None:
                return session_check_result
        
        # 继续处理请求
        response = await call_next(request)
        
        # 在响应中添加会话信息头（如果有有效会话）
        if self._should_check_session(request):
            await self._add_session_headers(request, response)
        
        return response
    
    def _should_check_session(self, request: Request) -> bool:
        """
        判断是否需要检查会话
        
        Args:
            request: HTTP请求
            
        Returns:
            bool: 是否需要检查会话
        """
        path = request.url.path
        
        # 检查是否在排除路径中
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # 检查是否是管理员API路径
        return path.startswith("/api/v1/admin/") and path != "/api/v1/admin/login"
    
    async def _check_session(self, request: Request) -> Response:
        """
        检查会话状态
        
        Args:
            request: HTTP请求
            
        Returns:
            Optional[Response]: 如果会话无效返回错误响应，否则返回None
        """
        # 获取Authorization头
        authorization = request.headers.get("Authorization")
        
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "MISSING_TOKEN",
                        "message": "缺少认证令牌",
                        "should_redirect_to_login": True
                    }
                }
            )
        
        token = authorization.split(" ")[1]
        
        # 检查会话是否有效
        if not session_service.is_session_valid(token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "SESSION_EXPIRED",
                        "message": "会话已过期，请重新登录",
                        "should_redirect_to_login": True
                    }
                }
            )
        
        # 检查会话超时警告
        timeout_info = session_service.check_session_timeout_warning(token)
        
        if timeout_info["should_logout"]:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "SESSION_TIMEOUT",
                        "message": timeout_info["message"],
                        "should_redirect_to_login": True
                    }
                }
            )
        
        return None
    
    async def _add_session_headers(self, request: Request, response: Response) -> None:
        """
        在响应中添加会话信息头
        
        Args:
            request: HTTP请求
            response: HTTP响应
        """
        authorization = request.headers.get("Authorization")
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            
            # 获取会话剩余时间
            remaining_time = session_service.get_session_remaining_time(token)
            
            if remaining_time is not None:
                response.headers["X-Session-Remaining"] = str(remaining_time)
                
                # 检查是否需要警告
                timeout_info = session_service.check_session_timeout_warning(token)
                
                if timeout_info["should_warn"]:
                    response.headers["X-Session-Warning"] = "true"
                    response.headers["X-Session-Warning-Message"] = timeout_info["message"]