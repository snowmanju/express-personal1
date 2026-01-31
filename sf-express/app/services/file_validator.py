"""
文件验证组件 (FileValidator)
负责验证上传文件的格式、大小和基本结构
"""

import os
import logging
from typing import List, Tuple
import pandas as pd
import io

# 配置日志记录器
logger = logging.getLogger(__name__)


class FileValidator:
    """
    文件验证器类
    验证文件格式、大小和基本结构
    """
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls'}
    
    # 文件大小限制 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    def __init__(self):
        """初始化文件验证器"""
        pass
    
    def validate_file_format(self, filename: str) -> bool:
        """
        验证文件格式是否支持
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否支持该格式
        """
        if not filename:
            return False
            
        # 获取文件扩展名
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in self.SUPPORTED_FORMATS
    
    def validate_file_size(self, file_content: bytes) -> bool:
        """
        验证文件大小是否在限制范围内
        
        Args:
            file_content: 文件二进制内容
            
        Returns:
            bool: 文件大小是否符合要求
        """
        return len(file_content) <= self.MAX_FILE_SIZE
    
    def validate_file_structure(self, file_content: bytes, filename: str) -> Tuple[bool, List[str]]:
        """
        验证文件结构是否正确（是否可读取、是否损坏）
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext == '.csv':
                # 尝试读取CSV文件
                try:
                    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8', nrows=1)
                except UnicodeDecodeError:
                    # 尝试其他编码
                    df = pd.read_csv(io.BytesIO(file_content), encoding='gbk', nrows=1)
            elif file_ext in ['.xlsx', '.xls']:
                # 尝试读取Excel文件
                df = pd.read_excel(io.BytesIO(file_content), nrows=1)
            else:
                errors.append(f"不支持的文件格式: {file_ext}")
                return False, errors
            
            # 检查是否为空文件
            if df.empty:
                errors.append("文件内容为空")
                return False, errors
                
        except Exception as e:
            if "No columns to parse from file" in str(e):
                errors.append("文件内容为空")
            elif "Unsupported format" in str(e) or "not supported" in str(e).lower():
                errors.append("文件格式不受支持或文件已损坏")
            else:
                errors.append(f"文件结构验证失败: {str(e)}")
            return False, errors
        
        return True, errors
    
    def validate(self, file_content: bytes, filename: str) -> Tuple[bool, List[str]]:
        """
        执行完整的文件验证
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 错误信息列表)
        """
        errors = []
        
        logger.info(f"开始验证文件: {filename}, 大小: {len(file_content)} bytes")
        
        # 验证文件格式
        if not self.validate_file_format(filename):
            error_msg = f"不支持的文件格式。支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        # 验证文件大小
        if not self.validate_file_size(file_content):
            size_mb = len(file_content) / (1024 * 1024)
            error_msg = f"文件大小超过限制。当前大小: {size_mb:.2f}MB，最大允许: {self.MAX_FILE_SIZE / (1024 * 1024)}MB"
            errors.append(error_msg)
            logger.error(error_msg)
        
        # 验证文件结构
        if not errors:  # 只有在格式和大小都正确时才验证结构
            is_valid, structure_errors = self.validate_file_structure(file_content, filename)
            if not is_valid:
                errors.extend(structure_errors)
                logger.error(f"文件结构验证失败: {', '.join(structure_errors)}")
            else:
                logger.info("文件验证通过")
        
        return len(errors) == 0, errors