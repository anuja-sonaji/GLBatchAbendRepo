# GL Batch Abend Process Application

A Python Streamlit application for processing General Ledger batch error messages and updating BUKO configuration files with proper validation and formatting.

## Overview

This application processes error messages from GL batch operations and generates properly formatted entries for BUKO (Business Object Configuration) files. It provides validation, duplicate detection, and configuration viewing capabilities.

## Features

### 🔄 Error Message Processing
- Parse error messages in the specified format
- Automatically determine BE_TYPE, BEC1, and BEC2 based on business rules
- Validate field lengths and formats
- Generate properly formatted output entries
- Detect duplicate configurations
- Append new entries to existing BUKO files

### 🔍 Configuration Viewer
- View all existing configurations from BUKO files
- Search across all fields (BE_TYPE, BEC1, BEC2, SOURCE, LART, etc.)
- Display comprehensive field information
- Export and download updated files

### ✅ Validation Features
- Field length validation
- Format compliance checking
- Duplicate detection
- Business rule enforcement

## Prerequisites

- Python 3.11 or higher
- VS Code
- Git (optional)

## Installation & Setup

### 1. Clone or Download the Project

```bash
# If using Git
git clone <repository-url>
cd gl-batch-abend-process

# Or download and extract the project files
```

### 2. Set up Python Environment

#### Option A: Using Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Option B: Using Conda (if installed)
```bash
conda create -n gl-batch-app python=3.11
conda activate gl-batch-app
```

### 3. Install Dependencies

```bash
pip install streamlit pandas
```

### 4. Configure Streamlit (Optional)

Create a `.streamlit/config.toml` file (already included):
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

## Running the Application

### Method 1: Using Terminal in VS Code

1. Open VS Code
2. Open the project folder (`File` → `Open Folder`)
3. Open terminal in VS Code (`Terminal` → `New Terminal`)
4. Activate your virtual environment (if using one)
5. Run the application:

```bash
streamlit run app.py --server.port 5000
```

### Method 2: Using VS Code Python Extension

1. Install the Python extension for VS Code
2. Open `app.py` in VS Code
3. Press `F5` or go to `Run` → `Start Debugging`
4. Select "Python File" when prompted

### Method 3: Using VS Code Tasks (Advanced)

Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Streamlit App",
            "type": "shell",
            "command": "streamlit",
            "args": ["run", "app.py", "--server.port", "5000"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}
```

Then use `Ctrl+Shift+P` → `Tasks: Run Task` → `Run Streamlit App`

## Usage Guide

### Processing Error Messages

1. Navigate to the "🔄 Process Error Message" tab
2. Enter your error message in the specified format:
   ```
   BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE
   ```
   
   Example: `01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL`

3. Upload your AI_AgentBuko.txt file
4. Click "🔄 Process Error Message"
5. Review the processed output and download the updated file

### Viewing Existing Configurations

1. Navigate to the "🔍 View Existing Configurations" tab
2. Upload your BUKO file
3. Use the search functionality to find specific configurations
4. Click "Show All" to view all configurations
5. Use the checkbox to view full formatted lines

## Field Specifications

| Field | Max Length | Description |
|-------|------------|-------------|
| BE_TYPE | 20 | Business Entity Type (auto-determined) |
| BEC1 | 20 | Business Entity Code 1 (auto-determined) |
| BEC2 | 20 | Business Entity Code 2 (auto-determined) |
| BK | 4 | Business Key (confirmed value '01BC') |
| KONTOBEZ_SOLL | 1 | Account Reference Debit |
| KONTOBEZ_HABEN | 1 | Account Reference Credit |
| BUCHART | 2 | Booking Type |
| BETRAGSART | 2 | Amount Type |
| FORDART | 2 | Claim Type |
| ZAHLART | 2 | Payment Type |
| GG_KONTOBEZ_SOLL | 1 | Counter Account Reference Debit |
| GG_KONTOBEZ_HABEN | 1 | Counter Account Reference Credit |
| BBZBETRART | 2 | Additional Amount Type |
| KZVORRUECK | 1 | Advance/Return Indicator |
| FLREVERSED | 1 | Reversal Flag |
| LART | 7 | Process Type |
| SOURCE | 10 | Source System (BUBASIS, BUBAZUSATZ, LEIAUFGL) |

## Business Rules

### BE_TYPE Determination
- If `KONTOBEZ_SOLL = 'S'` or `KONTOBEZ_HABEN = 'S'` → BE_TYPE = "CLAIM"
- If `KONTOBEZ_SOLL = 'V'` or `KONTOBEZ_HABEN = 'V'` → BE_TYPE = "PAYMENT"
- For other values → BE_TYPE = "REBOOKING"

### BEC1 and BEC2 Assignment
- **CLAIM**: BEC1 = "CLAIM ERROR", BEC2 = "ERROR"
- **PAYMENT**: BEC1 = "CONTRACT ERROR", BEC2 = "ERROR"
- **REBOOKING**: BEC1 = "OTHER ACC ERROR", BEC2 = "ERROR"

## Validation Rules

1. **Field Length**: Each field must not exceed its maximum character length
2. **Required Fields**: Either KONTOBEZ_SOLL or KONTOBEZ_HABEN must contain a value
3. **SOURCE Values**: Must be one of BUBASIS, BUBAZUSATZ, or LEIAUFGL
4. **Duplicate Detection**: Configurations are checked for duplicates based on fields from KONTOBEZ_SOLL to SOURCE

## File Structure

```
gl-batch-abend-process/
├── app.py                 # Main application file
├── README.md             # This file
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── pyproject.toml        # Python dependencies
├── uv.lock              # Lock file
└── attached_assets/      # Sample files
    ├── AI Agent_BUKO_*.txt
    └── GLBatchAbendProcess_*.txt
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   streamlit run app.py --server.port 8501
   ```

2. **Module Not Found**
   ```bash
   pip install streamlit pandas
   ```

3. **Permission Errors**
   - Ensure you have write permissions in the project directory
   - Run VS Code as administrator if needed (Windows)

### Error Messages

- **"Invalid error message format"**: Check that your input follows the exact format with proper '/' separators
- **"Field exceeds maximum length"**: Verify that each field value doesn't exceed its character limit
- **"Either KONTOBEZ_SOLL or KONTOBEZ_HABEN must contain a value"**: Ensure at least one of these fields has a value

## Support

For issues or questions:
1. Check the validation error messages in the application
2. Verify your input format matches the specification
3. Ensure your BUKO file is properly formatted
4. Review the field specifications and business rules

## Version Information

- **Application Version**: 1.0
- **Python**: 3.11+
- **Streamlit**: Latest
- **Pandas**: Latest

---

**Note**: This application processes sensitive financial data. Always ensure you have proper authorization before processing production BUKO files and follow your organization's data handling policies.