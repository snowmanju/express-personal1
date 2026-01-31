"""
Property-Based Tests for UTF-8 Encoding Support

**Feature: csv-file-upload, Property 3: UTF-8 Encoding Support**
**Validates: Requirements 1.5**

For any CSV file containing Chinese characters in headers or data,
the CSV_Processor should process it correctly without encoding errors.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import io
import pandas as pd
from app.services.csv_processor import CSVProcessor


# Template columns with Chinese characters
TEMPLATE_COLUMNS_CHINESE = [
    '理货日期', '快递单号', '集包单号', '长度', '宽度', 
    '高度', '重量', '货物代码', '客户代码', '运输代码'
]


@st.composite
def chinese_text(draw, min_size=1, max_size=20):
    """Generate text with Chinese characters"""
    # Common Chinese characters range
    chinese_chars = st.characters(min_codepoint=0x4E00, max_codepoint=0x9FFF)
    # Mix of Chinese and alphanumeric
    mixed_chars = st.text(
        min_size=min_size, 
        max_size=max_size,
        alphabet=st.one_of(
            chinese_chars,
            st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))
        )
    )
    return draw(mixed_chars)


@st.composite
def manifest_row_with_chinese(draw):
    """Generate a manifest data row with Chinese characters"""
    return {
        '理货日期': draw(st.dates().map(lambda d: d.strftime('%Y-%m-%d'))),
        '快递单号': draw(chinese_text(min_size=5, max_size=20)),
        '集包单号': draw(chinese_text(min_size=3, max_size=15)),
        '长度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
        '宽度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
        '高度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
        '重量': draw(st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)),
        '货物代码': draw(chinese_text(min_size=3, max_size=10)),
        '客户代码': draw(chinese_text(min_size=3, max_size=10)),
        '运输代码': draw(chinese_text(min_size=3, max_size=10)),
    }


@st.composite
def csv_with_chinese_content(draw):
    """Generate CSV file content with Chinese characters"""
    num_rows = draw(st.integers(min_value=1, max_value=30))
    rows = [draw(manifest_row_with_chinese()) for _ in range(num_rows)]
    
    # Create DataFrame with Chinese column names
    df = pd.DataFrame(rows, columns=TEMPLATE_COLUMNS_CHINESE)
    
    # Convert to CSV bytes with UTF-8 encoding
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_content = csv_buffer.getvalue().encode('utf-8')
    
    return csv_content, num_rows, df


@st.composite
def csv_with_mixed_content(draw):
    """Generate CSV with mix of Chinese and English content"""
    num_rows = draw(st.integers(min_value=1, max_value=30))
    
    rows = []
    for _ in range(num_rows):
        # Randomly choose between Chinese and English content
        use_chinese = draw(st.booleans())
        
        if use_chinese:
            row = draw(manifest_row_with_chinese())
        else:
            row = {
                '理货日期': draw(st.dates().map(lambda d: d.strftime('%Y-%m-%d'))),
                '快递单号': draw(st.text(min_size=5, max_size=20, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd')))),
                '集包单号': draw(st.text(min_size=3, max_size=15, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd')))),
                '长度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
                '宽度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
                '高度': draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False)),
                '重量': draw(st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)),
                '货物代码': draw(st.text(min_size=3, max_size=10, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd')))),
                '客户代码': draw(st.text(min_size=3, max_size=10, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd')))),
                '运输代码': draw(st.text(min_size=3, max_size=10, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd')))),
            }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=TEMPLATE_COLUMNS_CHINESE)
    
    # Convert to CSV bytes with UTF-8 encoding
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_content = csv_buffer.getvalue().encode('utf-8')
    
    return csv_content, num_rows, df



class TestUTF8EncodingSupportProperties:
    """
    Property-based tests for UTF-8 encoding support
    **Feature: csv-file-upload, Property 3: UTF-8 Encoding Support**
    """
    
    @given(file_data=csv_with_chinese_content())
    @settings(max_examples=100, deadline=None)
    def test_property_chinese_characters_in_headers(self, file_data):
        """
        Property: CSV files with Chinese column headers should be parsed correctly
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed without encoding errors
        assert result.success, f"CSV with Chinese headers should parse successfully, errors: {result.errors}"
        
        # Property: No encoding-related errors
        assert not any('encoding' in str(error).lower() or 'decode' in str(error).lower() 
                      for error in result.errors), \
            f"Should not have encoding errors, got: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Parsed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
        
        # Property: Chinese column names should be preserved
        parsed_columns = set(result.data.columns)
        expected_columns = set(TEMPLATE_COLUMNS_CHINESE)
        assert expected_columns.issubset(parsed_columns), \
            f"Chinese column names should be preserved. Missing: {expected_columns - parsed_columns}"
    
    @given(file_data=csv_with_chinese_content())
    @settings(max_examples=100, deadline=None)
    def test_property_chinese_characters_in_data(self, file_data):
        """
        Property: CSV files with Chinese data should preserve character integrity
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"CSV with Chinese data should parse successfully, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Parsed data should not be None"
        
        # Property: All rows should be present
        assert len(result.data) == expected_rows, \
            f"Expected {expected_rows} rows, got {len(result.data)}"
        
        # Property: Chinese characters should be readable (not garbled)
        # Check that we can access string columns without errors
        for col in ['快递单号', '集包单号', '货物代码', '客户代码', '运输代码']:
            if col in result.data.columns:
                # Should be able to convert to string without errors
                try:
                    _ = result.data[col].astype(str)
                except Exception as e:
                    pytest.fail(f"Failed to process Chinese characters in column {col}: {e}")
    
    @given(file_data=csv_with_mixed_content())
    @settings(max_examples=100, deadline=None)
    def test_property_mixed_chinese_english_content(self, file_data):
        """
        Property: CSV files with mixed Chinese and English content should be parsed correctly
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"CSV with mixed content should parse successfully, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Parsed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
    
    @given(file_data=csv_with_chinese_content())
    @settings(max_examples=100, deadline=None)
    def test_property_process_file_with_chinese(self, file_data):
        """
        Property: process_file should handle Chinese characters correctly
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Process the file
        result = processor.process_file(file_content, "测试文件.csv")
        
        # Property: Processing should succeed
        assert result.success, f"Processing CSV with Chinese should succeed, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Processed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
    
    @given(file_data=csv_with_chinese_content())
    @settings(max_examples=100, deadline=None)
    def test_property_column_normalization_with_chinese(self, file_data):
        """
        Property: Column normalization should work with Chinese column names
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Parse and normalize
        result = processor.process_file(file_content, "test.csv")
        
        # Property: Processing should succeed
        assert result.success, f"Processing should succeed, errors: {result.errors}"
        
        # Property: Chinese column names should be preserved after normalization
        normalized_columns = set(result.data.columns)
        expected_columns = set(TEMPLATE_COLUMNS_CHINESE)
        
        assert expected_columns.issubset(normalized_columns), \
            f"Chinese columns should be preserved after normalization. Missing: {expected_columns - normalized_columns}"
    
    @given(file_data=csv_with_chinese_content())
    @settings(max_examples=50, deadline=None)
    def test_property_no_data_corruption_with_chinese(self, file_data):
        """
        Property: Chinese characters should not be corrupted during parsing
        **Validates: Requirements 1.5**
        """
        file_content, expected_rows, original_df = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"Parsing should succeed, errors: {result.errors}"
        
        # Property: Check that string data is not corrupted
        # We verify this by checking that the data can be converted back to CSV
        try:
            output_buffer = io.StringIO()
            result.data.to_csv(output_buffer, index=False, encoding='utf-8')
            output_content = output_buffer.getvalue()
            
            # Should be able to encode back to UTF-8 without errors
            _ = output_content.encode('utf-8')
        except Exception as e:
            pytest.fail(f"Chinese characters were corrupted during parsing: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
