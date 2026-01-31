"""
CSV处理组件 (CSVProcessor)
负责解析CSV和Excel文件，支持UTF-8编码和列名标准化
"""

import pandas as pd
import io
import os
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Iterator
from dataclasses import dataclass

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class PreviewRow:
    """预览行数据类"""
    row_number: int
    data: Dict[str, Any]
    valid: bool
    errors: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ProcessingStatistics:
    """处理统计数据类"""
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    data: Optional[pd.DataFrame] = None
    errors: List[str] = None
    total_rows: int = 0
    statistics: Optional[ProcessingStatistics] = None
    preview_data: Optional[List[PreviewRow]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.statistics is None:
            self.statistics = ProcessingStatistics()


class CSVProcessor:
    """
    CSV处理器类
    使用pandas解析CSV和Excel文件，支持UTF-8编码和列名标准化
    包含性能优化：流式处理、批量操作、内存优化和处理时间监控
    """
    
    # 标准模板格式的列名映射
    TEMPLATE_COLUMNS = {
        '理货日期': 'manifest_date',
        '快递单号': 'tracking_number',
        '集包单号': 'package_number',
        '长度': 'length',
        '宽度': 'width',
        '高度': 'height',
        '重量': 'weight',
        '货物代码': 'goods_code',
        '客户代码': 'customer_code',
        '运输代码': 'transport_code'
    }
    
    # 性能优化配置
    CHUNK_SIZE = 1000  # 流式处理的块大小
    BATCH_SIZE = 500   # 数据库批量操作的批次大小
    
    def __init__(self):
        """初始化CSV处理器"""
        self.processing_time = 0.0  # 处理时间监控
    
    def parse_csv(self, file_content: bytes, use_streaming: bool = False) -> ProcessingResult:
        """
        解析CSV文件（支持流式处理）
        
        Args:
            file_content: CSV文件二进制内容
            use_streaming: 是否使用流式处理（适用于大文件）
            
        Returns:
            ProcessingResult: 解析结果
        """
        result = ProcessingResult(success=False)
        start_time = time.time()
        
        try:
            # 检查文件大小，决定是否使用流式处理
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > 5 or use_streaming:
                logger.info(f"文件大小 {file_size_mb:.2f}MB，使用流式处理")
                return self._parse_csv_streaming(file_content)
            
            # 首先尝试UTF-8编码
            logger.info("开始解析CSV文件，尝试UTF-8编码")
            df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
            logger.info(f"CSV文件解析成功，共{len(df)}行")
        except UnicodeDecodeError as e:
            logger.warning(f"UTF-8编码失败，尝试GBK编码: {str(e)}")
            try:
                # 如果UTF-8失败，尝试GBK编码
                df = pd.read_csv(io.BytesIO(file_content), encoding='gbk')
                logger.info(f"CSV文件使用GBK编码解析成功，共{len(df)}行")
            except Exception as e:
                error_msg = f"CSV文件编码错误: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result
        except Exception as e:
            if "No columns to parse from file" in str(e):
                error_msg = "CSV文件内容为空"
                logger.error(error_msg)
                result.errors.append(error_msg)
            else:
                error_msg = f"CSV文件解析失败: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
            return result
        
        # 检查数据框是否为空
        if df.empty:
            error_msg = "CSV文件内容为空"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        result.success = True
        result.data = df
        result.total_rows = len(df)
        
        # 记录处理时间
        self.processing_time = time.time() - start_time
        logger.info(f"CSV解析耗时: {self.processing_time:.2f}秒")
        
        return result
    
    def _parse_csv_streaming(self, file_content: bytes) -> ProcessingResult:
        """
        使用流式处理解析大型CSV文件
        
        Args:
            file_content: CSV文件二进制内容
            
        Returns:
            ProcessingResult: 解析结果
        """
        result = ProcessingResult(success=False)
        start_time = time.time()
        
        try:
            # 使用chunksize参数进行流式读取
            logger.info(f"开始流式解析CSV文件，块大小: {self.CHUNK_SIZE}")
            
            chunks = []
            total_rows = 0
            
            # 首先尝试UTF-8编码
            try:
                chunk_iterator = pd.read_csv(
                    io.BytesIO(file_content), 
                    encoding='utf-8',
                    chunksize=self.CHUNK_SIZE
                )
            except UnicodeDecodeError:
                logger.warning("UTF-8编码失败，尝试GBK编码")
                chunk_iterator = pd.read_csv(
                    io.BytesIO(file_content), 
                    encoding='gbk',
                    chunksize=self.CHUNK_SIZE
                )
            
            # 逐块处理
            for chunk in chunk_iterator:
                chunks.append(chunk)
                total_rows += len(chunk)
                logger.debug(f"已处理 {total_rows} 行")
            
            # 合并所有块
            if chunks:
                df = pd.concat(chunks, ignore_index=True)
                logger.info(f"流式解析完成，共{len(df)}行")
                
                result.success = True
                result.data = df
                result.total_rows = len(df)
            else:
                error_msg = "CSV文件内容为空"
                logger.error(error_msg)
                result.errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"流式解析CSV文件失败: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        # 记录处理时间
        self.processing_time = time.time() - start_time
        logger.info(f"流式CSV解析耗时: {self.processing_time:.2f}秒")
        
        return result
    
    def parse_excel(self, file_content: bytes) -> ProcessingResult:
        """
        解析Excel文件（优化内存使用）
        
        Args:
            file_content: Excel文件二进制内容
            
        Returns:
            ProcessingResult: 解析结果
        """
        result = ProcessingResult(success=False)
        start_time = time.time()
        
        try:
            # 使用pandas读取Excel文件
            logger.info("开始解析Excel文件")
            
            # 优化：只读取第一个工作表，使用engine参数优化性能
            df = pd.read_excel(
                io.BytesIO(file_content),
                sheet_name=0,  # 只读取第一个工作表
                engine='openpyxl'  # 使用openpyxl引擎
            )
            logger.info(f"Excel文件解析成功，共{len(df)}行")
        except Exception as e:
            if "No columns to parse from file" in str(e):
                error_msg = "Excel文件内容为空"
                logger.error(error_msg)
                result.errors.append(error_msg)
            else:
                error_msg = f"Excel文件解析失败: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)
            return result
        
        # 检查数据框是否为空
        if df.empty:
            error_msg = "Excel文件内容为空"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result
        
        result.success = True
        result.data = df
        result.total_rows = len(df)
        
        # 记录处理时间
        self.processing_time = time.time() - start_time
        logger.info(f"Excel解析耗时: {self.processing_time:.2f}秒")
        
        return result
    
    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名以匹配模板格式
        
        Args:
            df: 原始数据框
            
        Returns:
            pd.DataFrame: 标准化后的数据框
        """
        # 创建列名映射
        column_mapping = {}
        
        for col in df.columns:
            # 去除空格并查找匹配的标准列名
            clean_col = str(col).strip()
            if clean_col in self.TEMPLATE_COLUMNS:
                column_mapping[col] = clean_col
        
        # 重命名列
        df_normalized = df.rename(columns=column_mapping)
        
        # 只保留已知的标准列
        known_columns = [col for col in df_normalized.columns if col in self.TEMPLATE_COLUMNS.keys()]
        
        if known_columns:
            return df_normalized[known_columns]
        else:
            return df_normalized
    
    def process_file(self, file_content: bytes, filename: str, preview_only: bool = False, 
                     data_validator=None, manifest_storage=None) -> ProcessingResult:
        """
        处理文件（CSV或Excel）- 包含性能监控
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            preview_only: 是否仅预览模式（不持久化数据）
            data_validator: 数据验证器实例
            manifest_storage: 清单存储器实例
            
        Returns:
            ProcessingResult: 处理结果
        """
        # 开始计时
        start_time = time.time()
        
        # 根据文件扩展名选择解析方法
        file_ext = os.path.splitext(filename.lower())[1]
        
        if file_ext == '.csv':
            result = self.parse_csv(file_content)
        elif file_ext in ['.xlsx', '.xls']:
            result = self.parse_excel(file_content)
        else:
            result = ProcessingResult(success=False)
            result.errors.append(f"不支持的文件格式: {file_ext}")
            return result
        
        # 如果解析失败，直接返回
        if not result.success or result.data is None:
            return result
        
        # 进行列名标准化
        result.data = self.normalize_columns(result.data)
        
        # 如果提供了数据验证器，进行数据验证和处理
        if data_validator:
            result = self._process_with_validation(
                result, 
                data_validator, 
                manifest_storage, 
                preview_only
            )
        
        # 记录总处理时间
        total_time = time.time() - start_time
        logger.info(f"文件处理总耗时: {total_time:.2f}秒")
        
        return result
    
    def _process_with_validation(self, parse_result: ProcessingResult, 
                                 data_validator, manifest_storage, 
                                 preview_only: bool) -> ProcessingResult:
        """
        使用验证器处理数据
        
        Args:
            parse_result: 解析结果
            data_validator: 数据验证器实例
            manifest_storage: 清单存储器实例
            preview_only: 是否仅预览模式
            
        Returns:
            ProcessingResult: 处理结果
        """
        df = parse_result.data
        
        # 验证列结构
        logger.info("开始验证列结构")
        column_errors = data_validator.validate_columns(df)
        if column_errors:
            parse_result.success = False
            parse_result.errors.extend(column_errors)
            logger.error(f"列结构验证失败: {', '.join(column_errors)}")
            return parse_result
        
        logger.info("列结构验证通过")
        
        # 重置重复检查状态
        data_validator.reset_duplicate_check()
        
        # 验证每一行
        validation_results = []
        valid_records = []
        record_creation_failed_count = 0  # 跟踪记录创建失败的数量
        
        logger.info(f"开始验证{len(df)}行数据")
        
        for idx, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                row_number = idx + 2  # Excel行号（从2开始，因为第1行是标题）
                
                validation_result = data_validator.validate_row(row_dict, row_number)
                validation_results.append(validation_result)
                
                if validation_result.is_valid:
                    # 如果在保存模式且提供了存储器，准备记录
                    if not preview_only and manifest_storage:
                        try:
                            record = manifest_storage.create_manifest_record_from_dict(row_dict)
                            valid_records.append(record)
                        except Exception as e:
                            # 记录创建失败，记录错误但继续处理其他行
                            error_msg = f"第{row_number}行记录创建失败: {str(e)}"
                            logger.warning(error_msg)
                            validation_result.is_valid = False
                            validation_result.errors.append(error_msg)
                            record_creation_failed_count += 1
                else:
                    # 记录验证失败的行
                    logger.debug(f"第{row_number}行验证失败: {', '.join(validation_result.errors)}")
                    
            except Exception as e:
                # 行处理异常，记录错误但继续处理其他行
                error_msg = f"处理第{idx + 2}行时发生错误: {str(e)}"
                logger.error(error_msg)
                validation_results.append(
                    type('ValidationResult', (), {
                        'row_number': idx + 2,
                        'is_valid': False,
                        'errors': [error_msg],
                        'data': {}
                    })()
                )
        
        # 统计信息 - 确保准确性
        total_rows = len(validation_results)
        valid_rows = sum(1 for r in validation_results if r.is_valid)
        invalid_rows = total_rows - valid_rows
        
        logger.info(f"数据验证完成: 总行数={total_rows}, 有效行={valid_rows}, 无效行={invalid_rows}")
        
        # 验证统计准确性：total_rows 应该等于 valid_rows + invalid_rows
        if total_rows != valid_rows + invalid_rows:
            logger.error(f"统计不一致: total_rows({total_rows}) != valid_rows({valid_rows}) + invalid_rows({invalid_rows})")
        
        parse_result.statistics = ProcessingStatistics(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows
        )
        
        # 预览模式：返回详细的行信息
        if preview_only:
            preview_data = []
            # 返回前20行作为预览（或全部如果少于20行）
            sample_size = min(20, len(validation_results))
            for validation_result in validation_results[:sample_size]:
                preview_row = PreviewRow(
                    row_number=validation_result.row_number,
                    data=validation_result.data,
                    valid=validation_result.is_valid,
                    errors=validation_result.errors
                )
                preview_data.append(preview_row)
            
            parse_result.preview_data = preview_data
            parse_result.success = True
            logger.info(f"预览模式处理完成，返回{len(preview_data)}行预览数据")
        
        # 保存模式：持久化数据
        else:
            if manifest_storage and valid_records:
                logger.info(f"开始保存{len(valid_records)}条有效记录到数据库")
                try:
                    storage_result = manifest_storage.save_manifest_records(valid_records)
                    
                    if storage_result.success:
                        parse_result.statistics.inserted = storage_result.inserted
                        parse_result.statistics.updated = storage_result.updated
                        parse_result.statistics.skipped = storage_result.skipped
                        
                        # 验证存储统计准确性：valid_rows 应该等于 inserted + updated + skipped
                        expected_stored = storage_result.inserted + storage_result.updated + storage_result.skipped
                        if len(valid_records) != expected_stored:
                            logger.warning(f"存储统计不一致: valid_records({len(valid_records)}) != inserted({storage_result.inserted}) + updated({storage_result.updated}) + skipped({storage_result.skipped})")
                        
                        parse_result.success = True
                        logger.info(f"数据保存成功: 插入={storage_result.inserted}, 更新={storage_result.updated}, 跳过={storage_result.skipped}")
                    else:
                        parse_result.success = False
                        parse_result.errors.extend(storage_result.errors)
                        logger.error(f"数据保存失败: {', '.join(storage_result.errors)}")
                except Exception as e:
                    # 存储异常，记录错误
                    error_msg = f"数据库操作异常: {str(e)}"
                    logger.error(error_msg)
                    parse_result.success = False
                    parse_result.errors.append(error_msg)
            else:
                # 没有有效记录或没有存储器
                parse_result.success = True
                logger.info("保存模式处理完成，没有有效记录需要保存")
        
        return parse_result
    
    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式列表
        
        Returns:
            List[str]: 支持的文件格式
        """
        return ['.csv', '.xlsx', '.xls']
    
    def verify_statistics_accuracy(self, statistics: ProcessingStatistics, 
                                   validation_results: List = None,
                                   valid_records_count: int = None) -> Tuple[bool, List[str]]:
        """
        验证统计信息的准确性
        
        Args:
            statistics: 处理统计信息
            validation_results: 验证结果列表（可选）
            valid_records_count: 有效记录数量（可选）
            
        Returns:
            Tuple[bool, List[str]]: (是否准确, 错误消息列表)
        """
        errors = []
        
        # 验证1: total_rows 应该等于 valid_rows + invalid_rows
        if statistics.total_rows != statistics.valid_rows + statistics.invalid_rows:
            errors.append(
                f"总行数不匹配: total_rows({statistics.total_rows}) != "
                f"valid_rows({statistics.valid_rows}) + invalid_rows({statistics.invalid_rows})"
            )
        
        # 验证2: 如果提供了validation_results，验证计数是否匹配
        if validation_results is not None:
            expected_total = len(validation_results)
            if statistics.total_rows != expected_total:
                errors.append(
                    f"总行数与验证结果不匹配: total_rows({statistics.total_rows}) != "
                    f"validation_results_count({expected_total})"
                )
            
            expected_valid = sum(1 for r in validation_results if r.is_valid)
            if statistics.valid_rows != expected_valid:
                errors.append(
                    f"有效行数与验证结果不匹配: valid_rows({statistics.valid_rows}) != "
                    f"expected_valid({expected_valid})"
                )
        
        # 验证3: 在保存模式下，valid_rows 应该等于 inserted + updated + skipped
        if statistics.inserted > 0 or statistics.updated > 0 or statistics.skipped > 0:
            stored_total = statistics.inserted + statistics.updated + statistics.skipped
            
            # 如果提供了valid_records_count，使用它进行验证
            expected_stored = valid_records_count if valid_records_count is not None else statistics.valid_rows
            
            if stored_total != expected_stored:
                errors.append(
                    f"存储统计不匹配: inserted({statistics.inserted}) + "
                    f"updated({statistics.updated}) + skipped({statistics.skipped}) = "
                    f"{stored_total} != expected({expected_stored})"
                )
        
        # 验证4: 所有计数应该是非负数
        if statistics.total_rows < 0:
            errors.append(f"总行数不能为负数: {statistics.total_rows}")
        if statistics.valid_rows < 0:
            errors.append(f"有效行数不能为负数: {statistics.valid_rows}")
        if statistics.invalid_rows < 0:
            errors.append(f"无效行数不能为负数: {statistics.invalid_rows}")
        if statistics.inserted < 0:
            errors.append(f"插入数不能为负数: {statistics.inserted}")
        if statistics.updated < 0:
            errors.append(f"更新数不能为负数: {statistics.updated}")
        if statistics.skipped < 0:
            errors.append(f"跳过数不能为负数: {statistics.skipped}")
        
        # 验证5: valid_rows 不能超过 total_rows
        if statistics.valid_rows > statistics.total_rows:
            errors.append(
                f"有效行数不能超过总行数: valid_rows({statistics.valid_rows}) > "
                f"total_rows({statistics.total_rows})"
            )
        
        # 验证6: invalid_rows 不能超过 total_rows
        if statistics.invalid_rows > statistics.total_rows:
            errors.append(
                f"无效行数不能超过总行数: invalid_rows({statistics.invalid_rows}) > "
                f"total_rows({statistics.total_rows})"
            )
        
        is_accurate = len(errors) == 0
        
        if not is_accurate:
            logger.error(f"统计准确性验证失败: {'; '.join(errors)}")
        else:
            logger.debug("统计准确性验证通过")
        
        return is_accurate, errors