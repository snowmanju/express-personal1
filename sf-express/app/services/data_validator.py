"""
数据验证组件 (DataValidator)
负责验证CSV数据的业务规则和数据完整性
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class RowValidationResult:
    """行验证结果数据类"""
    row_number: int
    is_valid: bool
    errors: List[str]
    data: Dict[str, Any]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataValidator:
    """
    数据验证器类
    验证CSV数据的业务规则和数据完整性
    """
    
    # 必填字段
    REQUIRED_FIELDS = {
        '快递单号': 'tracking_number',
        '理货日期': 'manifest_date',
        '运输代码': 'transport_code',
        '客户代码': 'customer_code',
        '货物代码': 'goods_code'
    }
    
    # 可选字段
    OPTIONAL_FIELDS = {
        '集包单号': 'package_number',
        '长度': 'length',
        '宽度': 'width',
        '高度': 'height',
        '重量': 'weight'
    }
    
    # 所有字段
    ALL_FIELDS = {**REQUIRED_FIELDS, **OPTIONAL_FIELDS}
    
    # 数据验证规则
    VALIDATION_RULES = {
        'tracking_number': {
            'required': True,
            'type': 'string',
            'max_length': 50,
            'pattern': r'^[A-Za-z0-9]+$'  # 只允许字母数字
        },
        'manifest_date': {
            'required': True,
            'type': 'date',
            'formats': ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
        },
        'transport_code': {
            'required': True,
            'type': 'string',
            'max_length': 20
        },
        'customer_code': {
            'required': True,
            'type': 'string',
            'max_length': 20
        },
        'goods_code': {
            'required': True,
            'type': 'string',
            'max_length': 20
        },
        'package_number': {
            'required': False,
            'type': 'string',
            'max_length': 50
        },
        'length': {
            'required': False,
            'type': 'numeric',
            'min': 0,
            'max': 999999.99
        },
        'width': {
            'required': False,
            'type': 'numeric',
            'min': 0,
            'max': 999999.99
        },
        'height': {
            'required': False,
            'type': 'numeric',
            'min': 0,
            'max': 999999.99
        },
        'weight': {
            'required': False,
            'type': 'numeric',
            'min': 0,
            'max': 999999.999
        }
    }
    
    def __init__(self):
        """初始化数据验证器"""
        self.seen_tracking_numbers = set()
    
    def validate_required_fields(self, row_data: Dict[str, Any]) -> List[str]:
        """
        验证必填字段
        
        Args:
            row_data: 行数据字典
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for field_name in self.REQUIRED_FIELDS.keys():
            if field_name not in row_data or pd.isna(row_data[field_name]) or str(row_data[field_name]).strip() == '':
                errors.append(f"{field_name} 不能为空")
        
        return errors
    
    def validate_data_types(self, row_data: Dict[str, Any]) -> List[str]:
        """
        验证数据类型和格式
        
        Args:
            row_data: 行数据字典
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for field_name, field_value in row_data.items():
            if field_name not in self.ALL_FIELDS:
                continue
            
            # 如果字段为空且非必填，跳过验证
            if pd.isna(field_value) or str(field_value).strip() == '':
                continue
            
            # 获取英文字段名和验证规则
            eng_field = self.ALL_FIELDS[field_name]
            rules = self.VALIDATION_RULES.get(eng_field, {})
            field_type = rules.get('type', 'string')
            
            if field_type == 'string':
                # 字符串验证
                str_value = str(field_value).strip()
                max_length = rules.get('max_length')
                pattern = rules.get('pattern')
                
                if max_length and len(str_value) > max_length:
                    errors.append(f"{field_name} 长度超过{max_length}个字符")
                
                if pattern and not re.match(pattern, str_value):
                    if field_name == '快递单号':
                        errors.append(f"{field_name} 只能包含字母和数字")
                    else:
                        errors.append(f"{field_name} 格式不正确")
                        
            elif field_type == 'date':
                # 日期验证
                if not self._validate_date_format(field_value, rules.get('formats', ['%Y-%m-%d'])):
                    errors.append(f"{field_name} 日期格式不正确，支持格式: YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY, DD/MM/YYYY")
                    
            elif field_type == 'numeric':
                # 数值验证
                try:
                    numeric_value = float(str(field_value))
                    
                    # Check for NaN or infinity
                    if not (numeric_value == numeric_value):  # NaN check (NaN != NaN)
                        errors.append(f"{field_name} 必须是有效数字")
                        return errors
                    
                    if numeric_value == float('inf') or numeric_value == float('-inf'):
                        errors.append(f"{field_name} 必须是有效数字")
                        return errors
                    
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    
                    if min_val is not None and numeric_value < min_val:
                        errors.append(f"{field_name} 不能小于{min_val}")
                    
                    if max_val is not None and numeric_value > max_val:
                        errors.append(f"{field_name} 不能大于{max_val}")
                    
                    if numeric_value < 0:
                        errors.append(f"{field_name} 必须是正数")
                        
                except (ValueError, TypeError):
                    errors.append(f"{field_name} 必须是有效数字")
        
        return errors
    
    def validate_business_rules(self, row_data: Dict[str, Any]) -> List[str]:
        """
        验证业务规则
        
        Args:
            row_data: 行数据字典
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        # 检查快递单号重复
        if '快递单号' in row_data and not pd.isna(row_data['快递单号']):
            tracking_number = str(row_data['快递单号']).strip()
            if tracking_number in self.seen_tracking_numbers:
                errors.append(f"快递单号 {tracking_number} 重复")
            else:
                self.seen_tracking_numbers.add(tracking_number)
        
        return errors
    
    def validate_row(self, row_data: Dict[str, Any], row_number: int) -> RowValidationResult:
        """
        验证单行数据
        
        Args:
            row_data: 行数据字典
            row_number: 行号（从1开始）
            
        Returns:
            RowValidationResult: 行验证结果
        """
        all_errors = []
        
        try:
            # 验证必填字段
            required_errors = self.validate_required_fields(row_data)
            if required_errors:
                all_errors.extend(required_errors)
                logger.debug(f"第{row_number}行必填字段验证失败: {', '.join(required_errors)}")
            
            # 验证数据类型
            type_errors = self.validate_data_types(row_data)
            if type_errors:
                all_errors.extend(type_errors)
                logger.debug(f"第{row_number}行数据类型验证失败: {', '.join(type_errors)}")
            
            # 验证业务规则
            business_errors = self.validate_business_rules(row_data)
            if business_errors:
                all_errors.extend(business_errors)
                logger.debug(f"第{row_number}行业务规则验证失败: {', '.join(business_errors)}")
                
        except Exception as e:
            # 验证过程中发生异常，记录错误但不中断处理
            error_msg = f"验证过程发生异常: {str(e)}"
            all_errors.append(error_msg)
            logger.error(f"第{row_number}行验证异常: {str(e)}")
        
        return RowValidationResult(
            row_number=row_number,
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            data=row_data
        )
    
    def validate_columns(self, df: pd.DataFrame) -> List[str]:
        """
        验证数据框的列结构
        
        Args:
            df: 数据框
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        columns = set(df.columns.tolist())
        
        # 检查必填字段
        required_fields = set(self.REQUIRED_FIELDS.keys())
        missing_fields = required_fields - columns
        
        if missing_fields:
            errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        return errors
    
    def reset_duplicate_check(self):
        """重置重复检查状态"""
        self.seen_tracking_numbers.clear()
    
    def _validate_date_format(self, date_value: Any, formats: List[str]) -> bool:
        """
        验证日期格式
        
        Args:
            date_value: 日期值
            formats: 支持的日期格式列表
            
        Returns:
            bool: 是否为有效日期格式
        """
        if isinstance(date_value, (date, datetime)):
            return True
        
        date_str = str(date_value).strip()
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False