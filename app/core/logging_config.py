"""
日志配置模块
Logging Configuration Module
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any
import json

class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON格式"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        
        return json.dumps(log_entry, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为彩色输出"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 格式化时间戳
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建日志消息
        log_message = (
            f"{color}[{timestamp}] {record.levelname:8s}{reset} "
            f"{record.name}:{record.lineno} - {record.getMessage()}"
        )
        
        # 添加异常信息
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_json_logging: bool = False,
    enable_file_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    设置应用程序日志配置
    
    Args:
        log_level: 日志级别
        log_dir: 日志文件目录
        enable_json_logging: 是否启用JSON格式日志
        enable_file_logging: 是否启用文件日志
        max_file_size: 日志文件最大大小
        backup_count: 日志文件备份数量
    """
    
    # 创建日志目录
    if enable_file_logging:
        os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if enable_json_logging:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    if enable_file_logging:
        # 应用日志文件
        app_file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "app.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_file_handler.setLevel(getattr(logging, log_level.upper()))
        app_file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(app_file_handler)
        
        # 错误日志文件
        error_file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "error.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_file_handler)
        
        # 访问日志文件（用于API请求）
        access_logger = logging.getLogger("access")
        access_file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "access.log"),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        access_file_handler.setLevel(logging.INFO)
        access_file_handler.setFormatter(JSONFormatter())
        access_logger.addHandler(access_file_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)

def log_request(
    method: str,
    url: str,
    status_code: int,
    response_time: float,
    user_id: str = None,
    ip_address: str = None,
    request_id: str = None
) -> None:
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        url: 请求URL
        status_code: 响应状态码
        response_time: 响应时间（秒）
        user_id: 用户ID
        ip_address: 客户端IP地址
        request_id: 请求ID
    """
    access_logger = logging.getLogger("access")
    
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "response_time": response_time,
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if request_id:
        log_data["request_id"] = request_id
    
    access_logger.info(json.dumps(log_data, ensure_ascii=False))

# 预定义的日志器
app_logger = get_logger("app")
api_logger = get_logger("api")
db_logger = get_logger("database")
auth_logger = get_logger("auth")
kuaidi100_logger = get_logger("kuaidi100")