"""
Property-Based Tests for File Format Processing

**Feature: csv-file-upload, Property 1: File Format Processing**
**Validates: Requirements 1.1, 1.2**

For any valid CSV or Excel file with the template format, 
the CSV_Processor should successfully parse it and extract the data into the expected structure.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import io
import pandas as pd
from app.services.csv_processor import CSVProcessor


# Template columns as defined in the spec
TEMPLATE_COLUMNS = [
    '理货日期', '快递单号', '集包单号', '长度', '宽度', 
    '高度', '重量', '货物代码', '客户代码', '运输代码'
]


@st.composite
def valid_manifest_row(draw):
    """Generate a valid manifest data row"""
    return {
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



@st.composite
def valid_csv_file_content(draw):
    """Generate valid CSV file content with template format"""
    num_rows = draw(st.integers(min_value=1, max_value=50))
    rows = [draw(valid_manifest_row()) for _ in range(num_rows)]
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=TEMPLATE_COLUMNS)
    
    # Convert to CSV bytes with UTF-8 encoding
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_content = csv_buffer.getvalue().encode('utf-8')
    
    return csv_content, num_rows


@st.composite
def valid_excel_file_content(draw):
    """Generate valid Excel file content with template format"""
    num_rows = draw(st.integers(min_value=1, max_value=50))
    rows = [draw(valid_manifest_row()) for _ in range(num_rows)]
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=TEMPLATE_COLUMNS)
    
    # Convert to Excel bytes
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_content = excel_buffer.getvalue()
    
    return excel_content, num_rows


class TestFileFormatProcessingProperties:
    """
    Property-based tests for file format processing
    **Feature: csv-file-upload, Property 1: File Format Processing**
    """
    
    @given(file_data=valid_csv_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_csv_parsing_success(self, file_data):
        """
        Property: Any valid CSV file with template format should be successfully parsed
        **Validates: Requirements 1.1**
        """
        file_content, expected_rows = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"CSV parsing should succeed, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Parsed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
        
        # Property: DataFrame should have data
        assert len(result.data) == expected_rows, \
            f"DataFrame should have {expected_rows} rows, got {len(result.data)}"
    
    @given(file_data=valid_excel_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_excel_parsing_success(self, file_data):
        """
        Property: Any valid Excel file with template format should be successfully parsed
        **Validates: Requirements 1.2**
        """
        file_content, expected_rows = file_data
        processor = CSVProcessor()
        
        # Parse the Excel file
        result = processor.parse_excel(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"Excel parsing should succeed, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Parsed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
        
        # Property: DataFrame should have data
        assert len(result.data) == expected_rows, \
            f"DataFrame should have {expected_rows} rows, got {len(result.data)}"
    
    @given(file_data=valid_csv_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_csv_column_preservation(self, file_data):
        """
        Property: CSV parsing should preserve all template columns
        **Validates: Requirements 1.1**
        """
        file_content, _ = file_data
        processor = CSVProcessor()
        
        # Parse the CSV file
        result = processor.parse_csv(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"CSV parsing should succeed, errors: {result.errors}"
        
        # Property: All template columns should be present
        parsed_columns = set(result.data.columns)
        expected_columns = set(TEMPLATE_COLUMNS)
        
        assert expected_columns.issubset(parsed_columns), \
            f"Missing columns: {expected_columns - parsed_columns}"
    
    @given(file_data=valid_excel_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_excel_column_preservation(self, file_data):
        """
        Property: Excel parsing should preserve all template columns
        **Validates: Requirements 1.2**
        """
        file_content, _ = file_data
        processor = CSVProcessor()
        
        # Parse the Excel file
        result = processor.parse_excel(file_content)
        
        # Property: Parsing should succeed
        assert result.success, f"Excel parsing should succeed, errors: {result.errors}"
        
        # Property: All template columns should be present
        parsed_columns = set(result.data.columns)
        expected_columns = set(TEMPLATE_COLUMNS)
        
        assert expected_columns.issubset(parsed_columns), \
            f"Missing columns: {expected_columns - parsed_columns}"
    
    @given(file_data=valid_csv_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_process_file_csv_integration(self, file_data):
        """
        Property: process_file should successfully handle CSV files
        **Validates: Requirements 1.1**
        """
        file_content, expected_rows = file_data
        processor = CSVProcessor()
        
        # Process the file
        result = processor.process_file(file_content, "test.csv")
        
        # Property: Processing should succeed
        assert result.success, f"CSV processing should succeed, errors: {result.errors}"
        
        # Property: Data should be extracted
        assert result.data is not None, "Processed data should not be None"
        
        # Property: Row count should match
        assert result.total_rows == expected_rows, \
            f"Expected {expected_rows} rows, got {result.total_rows}"
    
    @given(file_data=valid_excel_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_process_file_excel_integration(self, file_data):
        """
        Property: process_file should successfully handle Excel files
        **Validates: Requirements 1.2**
        """
        file_content, expected_rows = file_data
        processor = CSVProcessor()
        
        # Test both .xlsx and .xls extensions
        for extension in ['.xlsx', '.xls']:
            result = processor.process_file(file_content, f"test{extension}")
            
            # Property: Processing should succeed
            assert result.success, f"Excel processing should succeed for {extension}, errors: {result.errors}"
            
            # Property: Data should be extracted
            assert result.data is not None, f"Processed data should not be None for {extension}"
            
            # Property: Row count should match
            assert result.total_rows == expected_rows, \
                f"Expected {expected_rows} rows for {extension}, got {result.total_rows}"
    
    @given(file_data=valid_csv_file_content())
    @settings(max_examples=100, deadline=None)
    def test_property_column_normalization(self, file_data):
        """
        Property: Column normalization should preserve template columns
        **Validates: Requirements 1.1, 1.2**
        """
        file_content, _ = file_data
        processor = CSVProcessor()
        
        # Parse and normalize
        result = processor.process_file(file_content, "test.csv")
        
        # Property: Processing should succeed
        assert result.success, f"Processing should succeed, errors: {result.errors}"
        
        # Property: Normalized columns should match template
        normalized_columns = set(result.data.columns)
        expected_columns = set(TEMPLATE_COLUMNS)
        
        # All expected columns should be present
        assert expected_columns.issubset(normalized_columns), \
            f"Missing columns after normalization: {expected_columns - normalized_columns}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
