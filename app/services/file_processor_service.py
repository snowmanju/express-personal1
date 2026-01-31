"""
文件处理服务 (FileProcessorService)
支持CSV和Excel文件解析，实现数据验证和预览功能
"""

import pandas as pd
import io
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date
import re
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from app.models.cargo_manifest import CargoManifest
from app.core.database import get_db


class FileProcessorService:
    """
    文件处理服务类
    支持CSV和Excel格式文件的解析、验证和预览
    """
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls'}
    
    # 必需字段映射 (中文字段名 -> 英文字段名)
    REQUIRED_FIELDS = {
        '快递单号': 'tracking_number',
        '理货日期': 'manifest_date', 
        '运输代码': 'transport_code',
        '客户代码': 'customer_code',
        '货物代码': 'goods_code'
    }
    
    # 可选字段映射
    OPTIONAL_FIELDS = {
        '集包单号': 'package_number',
        '重量': 'weight',
        '长度': 'length',
        '宽度': 'width', 
        '高度': 'height',
        '特殊费用': 'special_fee'
    }
    
    # 所有字段映射
    ALL_FIELDS = {**REQUIRED_FIELDS, **OPTIONAL_FIELDS}
    
    # 数据验证规则
    VALIDATION_RULES = {
        'tracking_number': {
            'required': True,
            'type': 'string',
            'max_length': 50,
            'pattern': r'^[A-Za-z0-9]+$'
        },
        'manifest_date': {
            'required': True,
            'type': 'date',
            'format': '%Y-%m-%d'
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
        'weight': {
            'required': False,
            'type': 'decimal',
            'min': 0,
            'max': 999999.999,
            'precision': 3
        },
        'length': {
            'required': False,
            'type': 'decimal',
            'min': 0,
            'max': 999999.99,
            'precision': 2
        },
        'width': {
            'required': False,
            'type': 'decimal',
            'min': 0,
            'max': 999999.99,
            'precision': 2
        },
        'height': {
            'required': False,
            'type': 'decimal',
            'min': 0,
            'max': 999999.99,
            'precision': 2
        },
        'special_fee': {
            'required': False,
            'type': 'decimal',
            'min': 0,
            'max': 99999999.99,
            'precision': 2
        }
    }

    def __init__(self, db: Session = None):
        """初始化文件处理服务"""
        self.db = db

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
        file_ext = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
        return file_ext in self.SUPPORTED_FORMATS

    def parse_file(self, file_content: bytes, filename: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        解析文件内容
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: (解析后的数据框, 错误信息列表)
        """
        errors = []
        
        # 验证文件格式
        if not self.validate_file_format(filename):
            errors.append(f"不支持的文件格式。支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
            return pd.DataFrame(), errors
        
        try:
            # 根据文件扩展名选择解析方法
            file_ext = '.' + filename.lower().split('.')[-1]
            
            if file_ext == '.csv':
                # 解析CSV文件
                df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
            elif file_ext in ['.xlsx', '.xls']:
                # 解析Excel文件
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                errors.append(f"不支持的文件格式: {file_ext}")
                return pd.DataFrame(), errors
                
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                if file_ext == '.csv':
                    df = pd.read_csv(io.BytesIO(file_content), encoding='gbk')
                else:
                    errors.append("文件编码错误，请使用UTF-8编码")
                    return pd.DataFrame(), errors
            except Exception as e:
                errors.append(f"文件解析失败: {str(e)}")
                return pd.DataFrame(), errors
        except Exception as e:
            # 检查是否是空文件错误
            if "No columns to parse from file" in str(e):
                errors.append("文件内容为空")
            else:
                errors.append(f"文件解析失败: {str(e)}")
            return pd.DataFrame(), errors
        
        # 验证数据框不为空
        if df.empty:
            errors.append("文件内容为空")
            return df, errors
        
        return df, errors

    def validate_columns(self, df: pd.DataFrame) -> List[str]:
        """
        验证文件列是否包含必需字段
        
        Args:
            df: 数据框
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        columns = set(df.columns.tolist())
        
        # 检查必需字段
        required_fields = set(self.REQUIRED_FIELDS.keys())
        missing_fields = required_fields - columns
        
        if missing_fields:
            errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 检查是否有未知字段
        all_known_fields = set(self.ALL_FIELDS.keys())
        unknown_fields = columns - all_known_fields
        
        if unknown_fields:
            errors.append(f"包含未知字段: {', '.join(unknown_fields)}")
        
        return errors

    def validate_row_data(self, row_data: Dict[str, Any], row_index: int) -> List[str]:
        """
        验证单行数据
        
        Args:
            row_data: 行数据字典
            row_index: 行索引
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for field_name, field_value in row_data.items():
            # 跳过未知字段
            if field_name not in self.ALL_FIELDS:
                continue
                
            # 获取英文字段名和验证规则
            eng_field = self.ALL_FIELDS[field_name]
            rules = self.VALIDATION_RULES.get(eng_field, {})
            
            # 检查必需字段
            if rules.get('required', False):
                if pd.isna(field_value) or str(field_value).strip() == '':
                    errors.append(f"第{row_index + 2}行 {field_name} 不能为空")
                    continue
            
            # 如果字段为空且非必需，跳过验证
            if pd.isna(field_value) or str(field_value).strip() == '':
                continue
            
            # 类型和格式验证
            field_type = rules.get('type', 'string')
            
            if field_type == 'string':
                # 字符串验证
                str_value = str(field_value).strip()
                max_length = rules.get('max_length')
                pattern = rules.get('pattern')
                
                if max_length and len(str_value) > max_length:
                    errors.append(f"第{row_index + 2}行 {field_name} 长度超过{max_length}个字符")
                
                if pattern and not re.match(pattern, str_value):
                    errors.append(f"第{row_index + 2}行 {field_name} 格式不正确")
                    
            elif field_type == 'date':
                # 日期验证
                try:
                    if isinstance(field_value, (date, datetime)):
                        # 已经是日期对象
                        pass
                    else:
                        # 尝试解析日期字符串
                        date_format = rules.get('format', '%Y-%m-%d')
                        datetime.strptime(str(field_value), date_format)
                except ValueError:
                    errors.append(f"第{row_index + 2}行 {field_name} 日期格式不正确，应为YYYY-MM-DD")
                    
            elif field_type == 'decimal':
                # 数值验证
                try:
                    decimal_value = Decimal(str(field_value))
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    
                    if min_val is not None and decimal_value < min_val:
                        errors.append(f"第{row_index + 2}行 {field_name} 不能小于{min_val}")
                    
                    if max_val is not None and decimal_value > max_val:
                        errors.append(f"第{row_index + 2}行 {field_name} 不能大于{max_val}")
                        
                except (InvalidOperation, ValueError):
                    errors.append(f"第{row_index + 2}行 {field_name} 必须是有效数字")
        
        return errors

    def convert_to_english_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将中文字段名转换为英文字段名
        
        Args:
            df: 原始数据框
            
        Returns:
            pd.DataFrame: 转换后的数据框
        """
        # 创建字段映射
        column_mapping = {}
        for col in df.columns:
            if col in self.ALL_FIELDS:
                column_mapping[col] = self.ALL_FIELDS[col]
        
        # 重命名列
        df_converted = df.rename(columns=column_mapping)
        
        # 只保留已知字段
        known_eng_fields = list(self.ALL_FIELDS.values())
        existing_fields = [col for col in df_converted.columns if col in known_eng_fields]
        
        return df_converted[existing_fields]

    def validate_and_preview(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        验证文件并生成预览数据
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            Dict[str, Any]: 验证结果和预览数据
        """
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'preview_data': [],
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'columns': []
        }
        
        # 解析文件
        df, parse_errors = self.parse_file(file_content, filename)
        if parse_errors:
            result['errors'].extend(parse_errors)
            return result
        
        # 验证列结构
        column_errors = self.validate_columns(df)
        if column_errors:
            result['errors'].extend(column_errors)
            return result
        
        # 记录列信息
        result['columns'] = df.columns.tolist()
        result['total_rows'] = len(df)
        
        # 验证每行数据
        valid_rows = 0
        preview_data = []
        
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            row_errors = self.validate_row_data(row_dict, index)
            
            # 准备预览数据
            preview_row = {
                'row_number': index + 2,  # Excel行号从2开始（第1行是标题）
                'data': row_dict,
                'errors': row_errors,
                'valid': len(row_errors) == 0
            }
            
            if len(row_errors) == 0:
                valid_rows += 1
            
            preview_data.append(preview_row)
            
            # 限制预览数据量（只显示前100行）
            if len(preview_data) >= 100:
                if len(df) > 100:
                    result['warnings'].append(f"文件包含{len(df)}行数据，预览仅显示前100行")
                break
        
        result['preview_data'] = preview_data
        result['valid_rows'] = valid_rows
        result['invalid_rows'] = result['total_rows'] - valid_rows
        
        # 如果有有效数据，标记为成功
        if valid_rows > 0:
            result['success'] = True
        else:
            result['errors'].append("文件中没有有效的数据行")
        
        return result

    def process_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        处理文件上传，执行增量更新
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")
        
        result = {
            'success': False,
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'errors': [],
            'skipped': 0
        }
        
        # 先验证和预览
        validation_result = self.validate_and_preview(file_content, filename)
        if not validation_result['success']:
            result['errors'] = validation_result['errors']
            return result
        
        # 解析文件并转换字段名
        df, _ = self.parse_file(file_content, filename)
        df_converted = self.convert_to_english_fields(df)
        
        # 处理每行数据
        for index, row in df_converted.iterrows():
            try:
                # 验证行数据
                row_dict = {}
                for col in df.columns:
                    if col in self.ALL_FIELDS:
                        row_dict[col] = row[self.ALL_FIELDS[col]] if self.ALL_FIELDS[col] in row.index else None
                
                row_errors = self.validate_row_data(row_dict, index)
                if row_errors:
                    result['skipped'] += 1
                    continue
                
                # 准备数据
                manifest_data = {}
                for eng_field in row.index:
                    if pd.notna(row[eng_field]) and str(row[eng_field]).strip() != '':
                        value = row[eng_field]
                        
                        # 类型转换
                        if eng_field == 'manifest_date':
                            if isinstance(value, (date, datetime)):
                                manifest_data[eng_field] = value.date() if isinstance(value, datetime) else value
                            else:
                                manifest_data[eng_field] = datetime.strptime(str(value), '%Y-%m-%d').date()
                        elif eng_field in ['weight', 'length', 'width', 'height', 'special_fee']:
                            manifest_data[eng_field] = Decimal(str(value))
                        else:
                            manifest_data[eng_field] = str(value).strip()
                
                # 检查是否已存在
                existing = self.db.query(CargoManifest).filter(
                    CargoManifest.tracking_number == manifest_data['tracking_number']
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in manifest_data.items():
                        if key != 'tracking_number':  # 不更新主键
                            setattr(existing, key, value)
                    result['updated'] += 1
                else:
                    # 插入新记录
                    new_manifest = CargoManifest(**manifest_data)
                    self.db.add(new_manifest)
                    result['inserted'] += 1
                
                result['total'] += 1
                
            except Exception as e:
                result['errors'].append(f"第{index + 2}行处理失败: {str(e)}")
                result['skipped'] += 1
        
        try:
            # 提交事务
            self.db.commit()
            result['success'] = True
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            result['errors'].append(f"数据库操作失败: {str(e)}")
            result['success'] = False
        
        return result