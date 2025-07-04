# GL Batch Abend Process Application

## Overview

This is a Python Streamlit application designed to process General Ledger (GL) batch error messages and update BUKO (Business Object Configuration) files. The application automates the parsing of error messages, applies business rules to determine configuration fields, and maintains proper formatting while preventing duplicates.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **UI Components**: Form inputs, data tables, file upload/download widgets
- **User Interface**: Simple web-based interface for error message processing and configuration viewing

### Backend Architecture
- **Language**: Python 3.11+
- **Core Logic**: Error message parsing, field validation, business rule application
- **File Processing**: Text file reading/writing for BUKO configuration files
- **Data Processing**: Pandas for data manipulation and validation

### Development Environment
- **IDE**: VS Code with Python extensions
- **Container**: Dev container configuration for consistent development environment
- **Debugging**: Configured launch settings for Streamlit application

## Key Components

### 1. Error Message Parser
- Parses structured error messages with 13+ fields separated by '/'
- Extracts fields: BK, KONTOBEZ_SOLL, KONTOBEZ_HABEN, BUCHART, BETRAGSART, etc.
- Handles empty fields with appropriate default values

### 2. Business Rules Engine
- Determines BE_TYPE, BEC1, BEC2 based on KONTOBEZ_SOLL and KONTOBEZ_HABEN values
- Implements conditional logic:
  - If 'S' in either field: BE_TYPE="CLAIM", BEC1="CLAIM ERROR", BEC2="ERROR"
  - If 'V' in either field: (logic appears incomplete in current code)

### 3. Validation System
- Field length validation (each field has specific max character limits)
- Format compliance checking
- Duplicate detection to prevent redundant entries
- Business rule enforcement

### 4. Configuration Management
- Reads existing BUKO configuration files
- Appends new entries without creating blank rows
- Maintains file integrity and proper formatting
- Provides search functionality across all configuration fields

### 5. File Operations
- Upload/download functionality for BUKO files
- Text file processing with proper encoding
- Export capabilities for updated configurations

## Data Flow

1. **Input**: User provides error message in specified format
2. **Parsing**: Error message is split and mapped to field structure
3. **Processing**: Business rules applied to determine BE_TYPE, BEC1, BEC2
4. **Validation**: Field lengths, formats, and business rules validated
5. **Integration**: New entry appended to existing BUKO file
6. **Output**: Updated configuration file with new entry and download link

## External Dependencies

### Python Packages
- `streamlit`: Web application framework
- `pandas`: Data manipulation and analysis
- `re`: Regular expression operations
- `io`: Input/output operations
- `typing`: Type hints for better code clarity

### File Dependencies
- BUKO configuration files (text format)
- Error message input (structured text format)

## Deployment Strategy

### Local Development
- Python virtual environment setup
- Streamlit development server on port 8501
- VS Code tasks for easy application launch

### Container Deployment
- Dev container configuration with Python 3.11
- Automated dependency installation
- Port forwarding for web access
- Streamlit server configuration with CORS disabled

### Production Considerations
- Application runs on Streamlit's built-in server
- File-based configuration storage
- No database dependencies for simplified deployment

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 04, 2025. Initial setup