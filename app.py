import streamlit as st
import pandas as pd
import re
import io
from typing import Tuple, Optional, List

def parse_error_message(error_msg: str) -> dict:
    """
    Parse the error message to extract individual field values.
    Expected format: 01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL  
    """
    # Remove leading/trailing whitespace
    error_msg = error_msg.strip()
    
    # Split by '/' but handle the fact that some fields might be empty
    # The pattern should match the structure: BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE
    parts = error_msg.split('/')
    
    if len(parts) < 13:
        raise ValueError(f"Invalid error message format. Expected at least 13 parts separated by '/', got {len(parts)}")
    
    # Map the parts to field names
    fields = {
        'BK': parts[0].strip(),
        'KONTOBEZ_SOLL': parts[1].strip() if parts[1].strip() else ' ',
        'KONTOBEZ_HABEN': parts[2].strip() if parts[2].strip() else ' ',
        'BUCHART': parts[3].strip(),
        'BETRAGSART': parts[4].strip(),
        'FORDART': parts[5].strip() if parts[5].strip() else '  ',
        'ZAHLART': parts[6].strip(),
        'GG_KONTOBEZ_SOLL': parts[7].strip() if parts[7].strip() else ' ',
        'GG_KONTOBEZ_HABEN': parts[8].strip() if parts[8].strip() else ' ',
        'BBZBETRART': parts[9].strip() if parts[9].strip() else '  ',
        'KZVORRUECK': parts[10].strip() if parts[10].strip() else ' ',
        'FLREVERSED': parts[11].strip() if parts[11].strip() else ' ',
        'LART': parts[12].strip(),
        'SOURCE': parts[13].strip() if len(parts) > 13 else ''
    }
    
    return fields

def determine_be_fields(kontobez_soll: str, kontobez_haben: str) -> Tuple[str, str, str]:
    """
    Determine BE_TYPE, BEC1, BEC2 based on KONTOBEZ_SOLL and KONTOBEZ_HABEN values.
    """
    # Check for 'S' in either field
    if kontobez_soll == 'S' or kontobez_haben == 'S':
        return "CLAIM", "CLAIM ERROR", "ERROR"
    
    # Check for 'V' in either field
    elif kontobez_haben == 'V' or kontobez_soll == 'V':
        return "PAYMENT", "CONTRACT ERROR", "ERROR"
    
    # For any other values
    else:
        return "REBOOKING", "OTHER ACC ERROR", "ERROR"

def validate_field_lengths(fields: dict) -> List[str]:
    """
    Validate that each field does not exceed maximum character length.
    Returns list of validation errors.
    """
    errors = []
    max_lengths = {
        'BK': 4,
        'KONTOBEZ_SOLL': 1,
        'KONTOBEZ_HABEN': 1,
        'BUCHART': 2,
        'BETRAGSART': 2,
        'FORDART': 2,
        'ZAHLART': 2,
        'GG_KONTOBEZ_SOLL': 1,
        'GG_KONTOBEZ_HABEN': 1,
        'BBZBETRART': 2,
        'KZVORRUECK': 1,
        'FLREVERSED': 1,
        'LART': 7,
        'SOURCE': 10
    }
    
    for field, max_len in max_lengths.items():
        if len(fields.get(field, '')) > max_len:
            errors.append(f"{field} exceeds maximum length of {max_len} characters")
    
    # Validate SOURCE values
    valid_sources = ['BUBASIS', 'BUBAZUSATZ', 'LEIAUFGL']
    if fields.get('SOURCE') and fields['SOURCE'] not in valid_sources:
        errors.append(f"SOURCE must be one of: {', '.join(valid_sources)}")
    
    # Validate that either KONTOBEZ_SOLL or KONTOBEZ_HABEN has a value
    if not fields.get('KONTOBEZ_SOLL', '').strip() and not fields.get('KONTOBEZ_HABEN', '').strip():
        errors.append("Either KONTOBEZ_SOLL or KONTOBEZ_HABEN must contain a value")
    
    return errors

def format_output_line(be_type: str, bec1: str, bec2: str, fields: dict) -> str:
    """
    Format the output line with proper spacing according to specifications.
    """
    # Format each field with proper padding
    formatted_be_type = be_type.ljust(20)  # Max 20 chars
    formatted_bec1 = bec1.ljust(20)        # Max 20 chars
    formatted_bec2 = bec2.ljust(20)        # Max 20 chars
    formatted_bk = fields['BK'].ljust(4)   # Max 4 chars
    
    # Handle KONTOBEZ fields (1 char each, no padding)
    kontobez_soll = fields['KONTOBEZ_SOLL'] if fields['KONTOBEZ_SOLL'].strip() else ' '
    kontobez_haben = fields['KONTOBEZ_HABEN'] if fields['KONTOBEZ_HABEN'].strip() else ' '
    
    # BUCHART (2 chars, no padding)
    buchart = fields['BUCHART'].ljust(2)
    
    # BETRAGSART (2 chars, pad with space if needed)
    betragsart = fields['BETRAGSART'].ljust(2)
    
    # FORDART (2 chars)
    fordart = fields['FORDART'].ljust(2)
    
    # ZAHLART (2 chars)
    zahlart = fields['ZAHLART'].ljust(2)
    
    # GG_KONTOBEZ fields (1 char each)
    gg_kontobez_soll = fields.get('GG_KONTOBEZ_SOLL', ' ')
    gg_kontobez_haben = fields.get('GG_KONTOBEZ_HABEN', ' ')
    
    # BBZBETRART (2 chars)
    bbzbetrart = fields.get('BBZBETRART', '  ').ljust(2)
    
    # KZVORRUECK (1 char)
    kzvorrueck = fields.get('KZVORRUECK', ' ')
    
    # FLREVERSED (1 char)
    flreversed = fields.get('FLREVERSED', ' ')
    
    # LART (7 chars, pad with spaces)
    lart = fields['LART'].ljust(7)
    
    # SOURCE (10 chars, pad with spaces)
    source = fields['SOURCE'].ljust(10)
    
    # Construct the final formatted line
    # Note: No additional space between BUCHART and BETRAGSART as per requirements
    formatted_line = (
        f"{formatted_be_type}{formatted_bec1}{formatted_bec2}"
        f"{formatted_bk}{kontobez_soll}{kontobez_haben}{buchart}{betragsart}"
        f"{fordart}{zahlart}{gg_kontobez_soll}{gg_kontobez_haben}"
        f"{bbzbetrart}{kzvorrueck}{flreversed}{lart}{source}"
    )
    
    return formatted_line

def check_duplicates(new_entry_fields: dict, existing_lines: List[str]) -> List[int]:
    """
    Check for duplicate entries based on fields from KONTOBEZ_SOLL to SOURCE.
    Returns list of row numbers where duplicates are found.
    """
    duplicates = []
    
    # Create comparison string for new entry (from KONTOBEZ_SOLL to SOURCE)
    new_comparison = (
        f"{new_entry_fields.get('KONTOBEZ_SOLL', ' ')}"
        f"{new_entry_fields.get('KONTOBEZ_HABEN', ' ')}"
        f"{new_entry_fields.get('BUCHART', '')}"
        f"{new_entry_fields.get('BETRAGSART', '')}"
        f"{new_entry_fields.get('FORDART', '  ')}"
        f"{new_entry_fields.get('ZAHLART', '')}"
        f"{new_entry_fields.get('GG_KONTOBEZ_SOLL', ' ')}"
        f"{new_entry_fields.get('GG_KONTOBEZ_HABEN', ' ')}"
        f"{new_entry_fields.get('BBZBETRART', '  ')}"
        f"{new_entry_fields.get('KZVORRUECK', ' ')}"
        f"{new_entry_fields.get('FLREVERSED', ' ')}"
        f"{new_entry_fields.get('LART', '')}"
        f"{new_entry_fields.get('SOURCE', '')}"
    )
    
    # Check against existing lines
    for i, line in enumerate(existing_lines, 1):
        if len(line.strip()) > 60:  # Ensure line has enough content
            # Extract the comparison part from existing line (skip BE_TYPE, BEC1, BEC2)
            existing_comparison = line[60:].strip()  # Skip first 60 chars (BE_TYPE + BEC1 + BEC2)
            
            if existing_comparison == new_comparison.strip():
                duplicates.append(i)
    
    return duplicates

def load_buko_file(uploaded_file) -> List[str]:
    """
    Load the BUKO file and return list of lines.
    """
    content = uploaded_file.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8')
    
    lines = content.splitlines()
    return lines

def main():
    st.set_page_config(
        page_title="GL Batch Abend Process",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ GL Batch Abend Process")
    st.markdown("Process error messages and update BUKO configuration files")
    
    # Create two columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Error Message Input")
        error_message = st.text_area(
            "Enter the error message:",
            height=100,
            placeholder="Example: 01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL",
            help="Enter the error message in the format: BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE"
        )
    
    with col2:
        st.subheader("📁 BUKO File Upload")
        uploaded_file = st.file_uploader(
            "Upload AI_AgentBuko.txt file:",
            type=['txt'],
            help="Upload the existing BUKO configuration file that will be updated"
        )
    
    # Process button
    if st.button("🔄 Process Error Message", type="primary"):
        if not error_message.strip():
            st.error("❌ Please enter an error message")
            return
        
        if not uploaded_file:
            st.error("❌ Please upload the BUKO file")
            return
        
        try:
            # Load existing BUKO file
            existing_lines = load_buko_file(uploaded_file)
            st.success(f"✅ Loaded BUKO file with {len(existing_lines)} existing entries")
            
            # Parse error message
            with st.spinner("Parsing error message..."):
                fields = parse_error_message(error_message)
            
            # Validate field lengths
            validation_errors = validate_field_lengths(fields)
            if validation_errors:
                st.error("❌ Validation Errors:")
                for error in validation_errors:
                    st.error(f"• {error}")
                return
            
            # Determine BE_TYPE, BEC1, BEC2
            be_type, bec1, bec2 = determine_be_fields(
                fields['KONTOBEZ_SOLL'], 
                fields['KONTOBEZ_HABEN']
            )
            
            # Check for duplicates
            duplicate_rows = check_duplicates(fields, existing_lines)
            if duplicate_rows:
                st.warning(f"⚠️ Duplicate entries found at row(s): {', '.join(map(str, duplicate_rows))}")
                st.warning("The configuration may already exist in the BUKO file.")
                
                if not st.checkbox("Proceed anyway (add duplicate entry)"):
                    return
            
            # Format output line
            formatted_line = format_output_line(be_type, bec1, bec2, fields)
            
            # Display results
            st.subheader("📊 Processing Results")
            
            # Show parsed fields
            with st.expander("🔍 Parsed Fields", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Determined Values:**")
                    st.write(f"BE_TYPE: `{be_type}`")
                    st.write(f"BEC1: `{bec1}`")
                    st.write(f"BEC2: `{bec2}`")
                
                with col2:
                    st.write("**Core Fields:**")
                    st.write(f"BK: `{fields['BK']}`")
                    st.write(f"KONTOBEZ_SOLL: `{fields['KONTOBEZ_SOLL']}`")
                    st.write(f"KONTOBEZ_HABEN: `{fields['KONTOBEZ_HABEN']}`")
                    st.write(f"BUCHART: `{fields['BUCHART']}`")
                    st.write(f"BETRAGSART: `{fields['BETRAGSART']}`")
                
                with col3:
                    st.write("**Additional Fields:**")
                    st.write(f"LART: `{fields['LART']}`")
                    st.write(f"SOURCE: `{fields['SOURCE']}`")
            
            # Show formatted output
            st.subheader("📄 Formatted Output")
            st.code(formatted_line, language="text")
            
            # Add to BUKO file
            updated_lines = existing_lines + [formatted_line]
            new_row_number = len(updated_lines)
            
            st.success(f"✅ New entry added at row {new_row_number}")
            
            # Create download file
            updated_content = '\n'.join(updated_lines)
            
            st.download_button(
                label="📥 Download Updated BUKO File",
                data=updated_content,
                file_name="AI_Agent_BUKO_Updated.txt",
                mime="text/plain",
                type="primary"
            )
            
            # Show warning message
            st.warning("""
            ⚠️ **Important Note:**
            This may not be the latest version of the BUKO file. Please ensure that you have the most recent version. 
            You can copy the newly added entry into your latest BUKO file and rerun the GL.
            """)
            
            # Show preview of updated file
            with st.expander("👀 Preview Updated File (Last 10 entries)"):
                preview_lines = updated_lines[-10:]
                for i, line in enumerate(preview_lines, len(updated_lines) - 9):
                    if i == new_row_number:
                        st.success(f"Row {i}: {line}")
                    else:
                        st.text(f"Row {i}: {line}")
            
        except ValueError as e:
            st.error(f"❌ Error parsing message: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
    
    # Help section
    with st.expander("❓ Help & Format Information"):
        st.markdown("""
        ### Error Message Format
        The error message should follow this format:
        ```
        BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE
        ```
        
        ### Field Specifications
        - **BE_TYPE**: Max 20 characters (auto-determined)
        - **BEC1**: Max 20 characters (auto-determined)
        - **BEC2**: Max 20 characters (auto-determined)
        - **BK**: Max 4 characters, confirmed value '01BC'
        - **KONTOBEZ_SOLL**: Max 1 character
        - **KONTOBEZ_HABEN**: Max 1 character
        - **BUCHART**: Max 2 characters
        - **BETRAGSART**: Max 2 characters
        - **FORDART**: Max 2 characters
        - **ZAHLART**: Max 2 characters
        - **LART**: Max 7 characters
        - **SOURCE**: Max 10 characters (BUBASIS, BUBAZUSATZ, LEIAUFGL)
        
        ### Business Rules
        - Either KONTOBEZ_SOLL or KONTOBEZ_HABEN must contain a value
        - If KONTOBEZ_SOLL or KONTOBEZ_HABEN = 'S': BE_TYPE = "CLAIM"
        - If KONTOBEZ_SOLL or KONTOBEZ_HABEN = 'V': BE_TYPE = "PAYMENT"  
        - For other values: BE_TYPE = "REBOOKING"
        """)

if __name__ == "__main__":
    main()
