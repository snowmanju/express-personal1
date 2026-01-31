# Requirements Document

## Introduction

This specification defines the requirements for implementing real CSV file upload functionality to replace the current mock implementation in the express tracking website's admin backend. The system currently returns simulated responses for CSV file uploads, but needs to process actual CSV files with manifest data including tracking numbers, package information, dimensions, and shipping codes.

## Glossary

- **CSV_Processor**: The system component responsible for parsing and validating CSV files
- **Manifest_Record**: A single row of shipping data containing tracking number, dimensions, codes, and metadata
- **Preview_Mode**: A processing mode that validates and displays data without persisting to storage
- **Save_Mode**: A processing mode that validates, processes, and persists data to storage
- **Template_Format**: The standardized CSV structure with columns: 理货日期,快递单号,集包单号,长度,宽度,高度,重量,货物代码,客户代码,运输代码
- **Admin_Backend**: The authenticated administrative interface for managing manifest data
- **File_Validator**: The component responsible for validating file format, size, and structure

## Requirements

### Requirement 1: File Format Support

**User Story:** As an admin user, I want to upload CSV and Excel files containing manifest data, so that I can import shipping records into the system.

#### Acceptance Criteria

1. WHEN a user uploads a CSV file (.csv), THE CSV_Processor SHALL parse it using the Template_Format
2. WHEN a user uploads an Excel file (.xlsx or .xls), THE CSV_Processor SHALL parse it using the Template_Format
3. WHEN a user uploads an unsupported file format, THE File_Validator SHALL reject it with a descriptive error message
4. WHEN a file exceeds 10MB in size, THE File_Validator SHALL reject it with a size limit error
5. THE CSV_Processor SHALL support UTF-8 encoding for Chinese characters in column headers and data

### Requirement 2: Data Validation and Processing

**User Story:** As an admin user, I want the system to validate uploaded data against business rules, so that only valid manifest records are processed.

#### Acceptance Criteria

1. WHEN processing any CSV row, THE CSV_Processor SHALL validate that required fields (快递单号, 理货日期, 运输代码, 客户代码, 货物代码) are not empty
2. WHEN processing dimension fields (长度, 宽度, 高度, 重量), THE CSV_Processor SHALL validate they are positive numeric values
3. WHEN processing date fields (理货日期), THE CSV_Processor SHALL validate they follow a recognizable date format
4. WHEN processing tracking numbers (快递单号), THE CSV_Processor SHALL validate they contain only alphanumeric characters
5. WHEN validation fails for any row, THE CSV_Processor SHALL record specific error messages for that row
6. THE CSV_Processor SHALL continue processing valid rows even when some rows contain errors

### Requirement 3: Preview and Save Modes

**User Story:** As an admin user, I want to preview uploaded data before saving it, so that I can verify the data is correct before committing changes.

#### Acceptance Criteria

1. WHEN preview_only parameter is true, THE CSV_Processor SHALL validate and return preview data without persisting to storage
2. WHEN preview_only parameter is false, THE CSV_Processor SHALL validate, process, and persist valid records to storage
3. WHEN in Preview_Mode, THE CSV_Processor SHALL return a sample of processed rows with validation status
4. WHEN in Save_Mode, THE CSV_Processor SHALL return processing statistics without detailed row data
5. THE CSV_Processor SHALL maintain identical validation logic between Preview_Mode and Save_Mode

### Requirement 4: Error Reporting and Statistics

**User Story:** As an admin user, I want detailed feedback on upload results, so that I can understand what data was processed and fix any issues.

#### Acceptance Criteria

1. WHEN processing completes, THE CSV_Processor SHALL return statistics including total_rows, valid_rows, invalid_rows, and skipped counts
2. WHEN in Preview_Mode, THE CSV_Processor SHALL return detailed error messages for each invalid row
3. WHEN validation errors occur, THE CSV_Processor SHALL provide specific field-level error descriptions
4. WHEN duplicate tracking numbers are detected, THE CSV_Processor SHALL report them as validation errors
5. THE CSV_Processor SHALL distinguish between data format errors and business rule violations in error messages

### Requirement 5: Template Download Support

**User Story:** As an admin user, I want to download a CSV template file, so that I can understand the required format for uploads.

#### Acceptance Criteria

1. THE Admin_Backend SHALL provide an endpoint to download the CSV template file
2. WHEN a template download is requested, THE Admin_Backend SHALL return the file at static/templates/manifest_upload_template.csv
3. THE template file SHALL contain the correct column headers in Template_Format
4. THE template file SHALL include sample data rows demonstrating proper formatting
5. THE template download SHALL not require file processing, only file serving

### Requirement 6: Authentication and Security

**User Story:** As a system administrator, I want CSV upload functionality to be secure and authenticated, so that only authorized users can import data.

#### Acceptance Criteria

1. WHEN accessing the upload endpoint, THE Admin_Backend SHALL require valid Bearer token authentication
2. WHEN authentication fails, THE Admin_Backend SHALL return a 401 Unauthorized response
3. WHEN file processing encounters system errors, THE Admin_Backend SHALL log detailed error information
4. WHEN processing completes, THE Admin_Backend SHALL log the operation with username and filename
5. THE Admin_Backend SHALL validate file content before processing to prevent malicious uploads

### Requirement 7: Data Persistence and Storage

**User Story:** As an admin user, I want uploaded manifest data to be stored persistently, so that it can be searched and managed through the admin interface.

#### Acceptance Criteria

1. WHEN in Save_Mode, THE CSV_Processor SHALL store valid Manifest_Records to the database
2. WHEN storing records, THE CSV_Processor SHALL include timestamps for created_at and updated_at fields
3. WHEN duplicate tracking numbers exist, THE CSV_Processor SHALL update existing records with new data
4. WHEN storing fails for individual records, THE CSV_Processor SHALL continue processing remaining records
5. THE CSV_Processor SHALL maintain referential integrity for customer codes and transport codes

### Requirement 8: Performance and Scalability

**User Story:** As an admin user, I want CSV uploads to process efficiently, so that I can upload large manifest files without timeouts.

#### Acceptance Criteria

1. WHEN processing files up to 10MB, THE CSV_Processor SHALL complete within 30 seconds
2. WHEN processing large files, THE CSV_Processor SHALL use streaming or batch processing to manage memory usage
3. WHEN multiple users upload simultaneously, THE Admin_Backend SHALL handle concurrent requests without data corruption
4. WHEN processing very large files, THE CSV_Processor SHALL provide progress feedback if possible
5. THE CSV_Processor SHALL optimize database operations using batch inserts where appropriate