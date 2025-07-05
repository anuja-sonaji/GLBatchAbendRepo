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
    
    # Check if the message is empty
    if not error_msg:
        raise ValueError("Error message cannot be empty")
    
    # Split by '/' but handle the fact that some fields might be empty
    # The pattern should match the structure: BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE
    parts = error_msg.split('/')
    
    if len(parts) < 13:
        # Provide more detailed error information
        sample_format = "01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL"
        current_parts = f"'{error_msg}'" if len(error_msg) < 100 else f"'{error_msg[:100]}...'"
        raise ValueError(f"""Invalid error message format. 

Expected format: {sample_format}

Your input: {current_parts}
Parts found: {len(parts)} (need at least 13)

Please ensure your error message:
1. Contains forward slashes (/) as field separators
2. Has at least 13 fields separated by '/'
3. Follows the pattern: BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE

If some fields are empty, leave them blank but keep the slashes (e.g., 'field1//field3' for empty middle field).""")
    
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

def extract_existing_configurations(lines: List[str]) -> List[dict]:
    """
    Extract all existing configurations from BUKO file with all field information.
    Returns list of configuration dictionaries.
    """
    configurations = []
    
    for line_num, line in enumerate(lines, 1):
        if len(line.strip()) > 60:  # Ensure line has enough content
            try:
                # Extract all fields based on the format specification
                be_type = line[0:20].strip()
                bec1 = line[20:40].strip()
                bec2 = line[40:60].strip()
                bk = line[60:64].strip()
                kontobez_soll = line[64:65] if len(line) > 64 else ' '
                kontobez_haben = line[65:66] if len(line) > 65 else ' '
                buchart = line[66:68].strip() if len(line) > 66 else ''
                betragsart = line[68:70].strip() if len(line) > 68 else ''
                fordart = line[70:72].strip() if len(line) > 70 else ''
                zahlart = line[72:74].strip() if len(line) > 72 else ''
                gg_kontobez_soll = line[74:75] if len(line) > 74 else ' '
                gg_kontobez_haben = line[75:76] if len(line) > 75 else ' '
                bbzbetrart = line[76:78].strip() if len(line) > 76 else ''
                kzvorrueck = line[78:79] if len(line) > 78 else ' '
                flreversed = line[79:80] if len(line) > 79 else ' '
                lart = line[80:87].strip() if len(line) > 80 else ''
                source = line[87:97].strip() if len(line) > 87 else ''
                
                if be_type and bec1 and bec2:
                    config_dict = {
                        'BE_TYPE': be_type,
                        'BEC1': bec1,
                        'BEC2': bec2,
                        'BK': bk,
                        'KONTOBEZ_SOLL': kontobez_soll,
                        'KONTOBEZ_HABEN': kontobez_haben,
                        'BUCHART': buchart,
                        'BETRAGSART': betragsart,
                        'FORDART': fordart,
                        'ZAHLART': zahlart,
                        'GG_KONTOBEZ_SOLL': gg_kontobez_soll,
                        'GG_KONTOBEZ_HABEN': gg_kontobez_haben,
                        'BBZBETRART': bbzbetrart,
                        'KZVORRUECK': kzvorrueck,
                        'FLREVERSED': flreversed,
                        'LART': lart,
                        'SOURCE': source,
                        'Line_Number': line_num,
                        'Full_Line': line
                    }
                    
                    configurations.append(config_dict)
                        
            except IndexError:
                continue  # Skip malformed lines
    
    return configurations

def search_configurations(configurations: List[dict], search_term: Optional[str] = None) -> List[dict]:
    """
    Search configurations by any field value.
    If search_term is None or empty, returns all configurations.
    """
    if not search_term or search_term.strip() == "":
        return configurations
    
    search_term = search_term.upper().strip()
    filtered_configs = []
    
    for config in configurations:
        # Search through all string fields
        searchable_fields = ['BE_TYPE', 'BEC1', 'BEC2', 'BK', 'KONTOBEZ_SOLL', 'KONTOBEZ_HABEN', 
                           'BUCHART', 'BETRAGSART', 'FORDART', 'ZAHLART', 
                           'GG_KONTOBEZ_SOLL', 'GG_KONTOBEZ_HABEN', 'BBZBETRART',
                           'KZVORRUECK', 'FLREVERSED', 'LART', 'SOURCE']
        
        for field in searchable_fields:
            if search_term in str(config.get(field, '')).upper():
                filtered_configs.append(config)
                break  # Avoid duplicates
    
    return filtered_configs

def apply_advanced_filters(configurations: List[dict], filters: dict) -> List[dict]:
    """
    Apply multiple filter criteria to configurations.
    """
    filtered_configs = configurations.copy()
    
    for field, value in filters.items():
        if value and value != "All":
            filtered_configs = [config for config in filtered_configs if config.get(field, '') == value]
    
    return filtered_configs

def main():
    st.set_page_config(
        page_title="GL Batch Abend Process",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ GL Batch Abend Process")
    st.markdown("Process error messages and update BUKO configuration files")
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["🔄 Process Error Message", "🔍 View Existing Configurations"])
    
    with tab2:
        st.subheader("📋 Existing BUKO Configurations")
        st.markdown("Upload a BUKO file to view all existing BEC1 and BEC2 configurations")
        
        # File upload for configuration viewing
        config_file = st.file_uploader(
            "Upload BUKO file to view configurations:",
            type=['txt'],
            key="config_viewer",
            help="Upload the BUKO file to analyze existing configurations"
        )
        
        if config_file:
            try:
                # Load and analyze the file
                config_lines = load_buko_file(config_file)
                configurations = extract_existing_configurations(config_lines)
                
                if configurations:
                    st.success(f"✅ Found {len(configurations)} configurations in the BUKO file")
                    
                    # Enhanced search functionality
                    st.markdown("### 🔍 Search & Filter Options")
                    
                    # Create search columns
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        search_term = st.text_input(
                            "🔎 Search configurations (any field):",
                            placeholder="Enter search term (e.g., 'PREMIUM', 'ERROR', 'CLAIM', 'BUBASIS')",
                            help="Search by any field value including BE_TYPE, BEC1, BEC2, SOURCE, LART, etc."
                        )
                    
                    with col2:
                        # Filter by BE_TYPE
                        be_types = sorted(set(config['BE_TYPE'] for config in configurations))
                        selected_be_type = st.selectbox(
                            "Filter by BE_TYPE:",
                            options=["All"] + be_types,
                            index=0
                        )
                    
                    with col3:
                        # Filter by SOURCE
                        sources = sorted(set(config['SOURCE'] for config in configurations if config['SOURCE']))
                        selected_source = st.selectbox(
                            "Filter by SOURCE:",
                            options=["All"] + sources,
                            index=0
                        )
                    
                    # Additional filter row
                    col4, col5, col6 = st.columns([1, 1, 2])
                    
                    with col4:
                        # Filter by BUCHART
                        buchart_values = sorted(set(config['BUCHART'] for config in configurations if config['BUCHART'].strip()))
                        selected_buchart = st.selectbox(
                            "Filter by BUCHART:",
                            options=["All"] + buchart_values,
                            index=0
                        )
                    
                    with col5:
                        # Filter by BETRAGSART
                        betragsart_values = sorted(set(config['BETRAGSART'] for config in configurations if config['BETRAGSART'].strip()))
                        selected_betragsart = st.selectbox(
                            "Filter by BETRAGSART:",
                            options=["All"] + betragsart_values,
                            index=0
                        )
                    
                    with col6:
                        # Action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        with col_btn1:
                            show_all = st.button("Show All", type="secondary")
                        with col_btn2:
                            clear_filters = st.button("Clear Filters", type="secondary")
                        with col_btn3:
                            apply_filters = st.button("Apply Filters", type="primary")
                    
                    # Apply search and filters
                    if search_term or show_all or apply_filters or selected_be_type != "All" or selected_source != "All" or selected_buchart != "All" or selected_betragsart != "All":
                        if clear_filters:
                            # Reset session state for filters
                            if 'filter_reset' not in st.session_state:
                                st.session_state.filter_reset = True
                                st.rerun()
                        
                        # Apply filters
                        filtered_configs = configurations.copy()
                        
                        # Apply text search
                        if search_term and not show_all:
                            filtered_configs = search_configurations(filtered_configs, search_term)
                        
                        # Apply BE_TYPE filter
                        if selected_be_type != "All":
                            filtered_configs = [config for config in filtered_configs if config['BE_TYPE'] == selected_be_type]
                        
                        # Apply SOURCE filter
                        if selected_source != "All":
                            filtered_configs = [config for config in filtered_configs if config['SOURCE'] == selected_source]
                        
                        # Apply BUCHART filter
                        if selected_buchart != "All":
                            filtered_configs = [config for config in filtered_configs if config['BUCHART'] == selected_buchart]
                        
                        # Apply BETRAGSART filter
                        if selected_betragsart != "All":
                            filtered_configs = [config for config in filtered_configs if config['BETRAGSART'] == selected_betragsart]
                        
                        if filtered_configs:
                            # Display results count and export options
                            col_result1, col_result2, col_result3 = st.columns([2, 1, 1])
                            
                            with col_result1:
                                st.info(f"📊 Displaying {len(filtered_configs)} of {len(configurations)} configurations")
                            
                            with col_result2:
                                # Export filtered results as CSV
                                if len(filtered_configs) > 0:
                                    config_data_export = []
                                    for config in filtered_configs:
                                        config_data_export.append({
                                            "Line #": config['Line_Number'],
                                            "BE_TYPE": config['BE_TYPE'],
                                            "BEC1": config['BEC1'],
                                            "BEC2": config['BEC2'],
                                            "BK": config['BK'],
                                            "KONTOBEZ_SOLL": config['KONTOBEZ_SOLL'],
                                            "KONTOBEZ_HABEN": config['KONTOBEZ_HABEN'],
                                            "BUCHART": config['BUCHART'],
                                            "BETRAGSART": config['BETRAGSART'],
                                            "FORDART": config['FORDART'],
                                            "ZAHLART": config['ZAHLART'],
                                            "GG_KONTOBEZ_SOLL": config['GG_KONTOBEZ_SOLL'],
                                            "GG_KONTOBEZ_HABEN": config['GG_KONTOBEZ_HABEN'],
                                            "BBZBETRART": config['BBZBETRART'],
                                            "KZVORRUECK": config['KZVORRUECK'],
                                            "FLREVERSED": config['FLREVERSED'],
                                            "LART": config['LART'],
                                            "SOURCE": config['SOURCE']
                                        })
                                    
                                    df_export = pd.DataFrame(config_data_export)
                                    csv_data = df_export.to_csv(index=False)
                                    
                                    st.download_button(
                                        label="📄 Export CSV",
                                        data=csv_data,
                                        file_name="buko_configurations_filtered.csv",
                                        mime="text/csv",
                                        type="secondary"
                                    )
                            
                            with col_result3:
                                # Quick filter toggle
                                show_details = st.checkbox("Show Details", value=True)
                            
                            # Create a comprehensive table for all fields
                            config_data = []
                            for config in filtered_configs:
                                config_data.append({
                                    "Line #": config['Line_Number'],
                                    "BE_TYPE": config['BE_TYPE'],
                                    "BEC1": config['BEC1'],
                                    "BEC2": config['BEC2'],
                                    "BK": config['BK'],
                                    "KONTOBEZ_SOLL": config['KONTOBEZ_SOLL'],
                                    "KONTOBEZ_HABEN": config['KONTOBEZ_HABEN'],
                                    "BUCHART": config['BUCHART'],
                                    "BETRAGSART": config['BETRAGSART'],
                                    "FORDART": config['FORDART'],
                                    "ZAHLART": config['ZAHLART'],
                                    "GG_KONTOBEZ_SOLL": config['GG_KONTOBEZ_SOLL'],
                                    "GG_KONTOBEZ_HABEN": config['GG_KONTOBEZ_HABEN'],
                                    "BBZBETRART": config['BBZBETRART'],
                                    "KZVORRUECK": config['KZVORRUECK'],
                                    "FLREVERSED": config['FLREVERSED'],
                                    "LART": config['LART'],
                                    "SOURCE": config['SOURCE']
                                })
                            
                            if config_data:
                                df = pd.DataFrame(config_data)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                
                                # Option to view full formatted lines
                                if st.checkbox("Show full formatted lines", key="show_full_lines"):
                                    st.subheader("Full Formatted Lines")
                                    for config in filtered_configs:
                                        st.text(f"Line {config['Line_Number']}: {config['Full_Line']}")
                        else:
                            st.warning(f"❌ No configurations found matching '{search_term}'")
                    
                    # Summary statistics
                    with st.expander("📊 Configuration Summary"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            unique_be_types = len(set(config['BE_TYPE'] for config in configurations))
                            st.metric("Unique BE_TYPE Categories", unique_be_types)
                        
                        with col2:
                            st.metric("Total Configurations", len(configurations))
                        
                        with col3:
                            unique_sources = len(set(config['SOURCE'] for config in configurations if config['SOURCE']))
                            st.metric("Unique SOURCE Values", unique_sources)
                        
                        # Show BE_TYPE distribution
                        st.markdown("**Configurations per BE_TYPE:**")
                        be_type_counts = {}
                        for config in configurations:
                            be_type = config['BE_TYPE']
                            be_type_counts[be_type] = be_type_counts.get(be_type, 0) + 1
                        
                        for be_type, count in sorted(be_type_counts.items()):
                            st.write(f"• **{be_type}**: {count} configurations")
                
                else:
                    st.warning("⚠️ No valid configurations found in the uploaded file")
                    
            except Exception as e:
                st.error(f"❌ Error analyzing file: {str(e)}")
    
    with tab1:
        st.subheader("📝 Error Message Processing")
        
        # Create two columns for inputs
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Error Message Input**")
            
            # Initialize error message in session state if not present
            if 'error_message' not in st.session_state:
                st.session_state.error_message = ""
            
            # Add sample message button
            col_input1, col_input2 = st.columns([3, 1])
            with col_input2:
                if st.button("📋 Use Sample", type="secondary", use_container_width=True):
                    st.session_state.error_message = "01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL"
                    st.rerun()
            
            error_message = st.text_area(
                "Enter the error message:",
                value=st.session_state.error_message,
                height=100,
                placeholder="Example: 01BC/S/ /UM/E /  /UM/ /K/  / / /AM34   /LEIAUFGL",
                help="Enter the error message with fields separated by forward slashes (/). Must contain at least 13 fields in the format: BK/KONTOBEZ_SOLL/KONTOBEZ_HABEN/BUCHART/BETRAGSART/FORDART/ZAHLART/GG_KONTOBEZ_SOLL/GG_KONTOBEZ_HABEN/BBZBETRART/KZVORRUECK/FLREVERSED/LART/SOURCE"
            )
            
            # Update session state with current error message
            st.session_state.error_message = error_message
            
            # Add format validation helper
            if error_message.strip():
                parts_count = len(error_message.split('/'))
                if parts_count < 13:
                    st.error(f"⚠️ Format check: Found {parts_count} fields, need at least 13. Make sure to use forward slashes (/) as separators.")
                else:
                    st.success(f"✅ Format check: Found {parts_count} fields (minimum 13 required)")
        
        with col2:
            st.markdown("**BUKO File Upload**")
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
                
                # Add to BUKO file
                updated_lines = existing_lines + [formatted_line]
                new_row_number = len(updated_lines)
                
                # Create download file
                updated_content = '\n'.join(updated_lines)
                
                # Store processing results in session state
                st.session_state.processing_results = {
                    'be_type': be_type,
                    'bec1': bec1,
                    'bec2': bec2,
                    'fields': fields,
                    'formatted_line': formatted_line,
                    'new_row_number': new_row_number,
                    'updated_content': updated_content,
                    'updated_lines': updated_lines,
                    'duplicate_rows': duplicate_rows
                }
                
            except ValueError as e:
                st.error(f"❌ Error parsing message: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
        
        # Display processing results if they exist in session state (only in this tab)
        if 'processing_results' in st.session_state:
            results = st.session_state.processing_results
            
            # Display results
            st.subheader("📊 Processing Results")
            
            # Show parsed fields
            with st.expander("🔍 Parsed Fields", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Determined Values:**")
                    st.write(f"BE_TYPE: `{results['be_type']}`")
                    st.write(f"BEC1: `{results['bec1']}`")
                    st.write(f"BEC2: `{results['bec2']}`")
                    st.write("")
                    st.write("**Core Fields:**")
                    st.write(f"BK: `{results['fields']['BK']}`")
                    st.write(f"KONTOBEZ_SOLL: `{results['fields']['KONTOBEZ_SOLL']}`")
                    st.write(f"KONTOBEZ_HABEN: `{results['fields']['KONTOBEZ_HABEN']}`")
                    st.write(f"BUCHART: `{results['fields']['BUCHART']}`")
                    st.write(f"BETRAGSART: `{results['fields']['BETRAGSART']}`")
                
                with col2:
                    st.write("**Additional Core Fields:**")
                    st.write(f"FORDART: `{results['fields']['FORDART']}`")
                    st.write(f"ZAHLART: `{results['fields']['ZAHLART']}`")
                    st.write(f"GG_KONTOBEZ_SOLL: `{results['fields']['GG_KONTOBEZ_SOLL']}`")
                    st.write(f"GG_KONTOBEZ_HABEN: `{results['fields']['GG_KONTOBEZ_HABEN']}`")
                    st.write(f"BBZBETRART: `{results['fields']['BBZBETRART']}`")
                    st.write(f"KZVORRUECK: `{results['fields']['KZVORRUECK']}`")
                    st.write(f"FLREVERSED: `{results['fields']['FLREVERSED']}`")
                
                with col3:
                    st.write("**Other Fields:**")
                    st.write(f"LART: `{results['fields']['LART']}`")
                    st.write(f"SOURCE: `{results['fields']['SOURCE']}`")
            
            # Show formatted output
            st.subheader("📄 Formatted Output")
            st.code(results['formatted_line'], language="text")
            
            st.success(f"✅ New entry added at row {results['new_row_number']}")
            
            # Download button
            st.download_button(
                label="📥 Download Updated BUKO File",
                data=results['updated_content'],
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
                preview_lines = results['updated_lines'][-10:]
                for i, line in enumerate(preview_lines, len(results['updated_lines']) - 9):
                    if i == results['new_row_number']:
                        st.success(f"Row {i}: {line}")
                    else:
                        st.text(f"Row {i}: {line}")
            
            # Clear results button
            if st.button("🧹 Clear Results & Start New", type="secondary"):
                del st.session_state.processing_results
                st.session_state.error_message = ""
                st.rerun()
    
    
    
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
