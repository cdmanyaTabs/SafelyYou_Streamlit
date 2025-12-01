import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from usage_transformation import process_data, deduplicate_output

# Page configuration
st.set_page_config(
    page_title="SafelyYou Custom App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_api_key(api_key):
    """
    Validate API key by making a test API call.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if API key is valid, False otherwise
    """
    if not api_key or not api_key.strip():
        return False
    
    try:
        # Use a lightweight endpoint that doesn't require parameters
        url = "https://integrators.prod.api.tabsplatform.com/v3/events/types?limit=1"
        headers = {
            "Authorization": api_key.strip()
        }
        response = requests.get(url, headers=headers, timeout=10)
        # Accept any 2xx status code as success
        is_valid = 200 <= response.status_code < 300
        if not is_valid:
            print(f"API key validation failed: Status {response.status_code}")
        return is_valid
    except Exception as e:
        print(f"API key validation exception: {str(e)}")
        return False

def show_authentication():
    """Display authentication screen for API key input."""
    st.title("🔐 SafelyYou Custom App - Authentication")
    st.markdown("---")
    
    st.info("Please enter your Tabs API key to access the application.")
    
    # API key input
    api_key = st.text_input(
        "API Key",
        type="password",
        key="api_key_input",
        help="Enter your Tabs API key",
        placeholder="Enter your API key here"
    )
    
    # Submit button
    if st.button("Submit", type="primary", key="submit_api_key"):
        if api_key and api_key.strip():
            with st.spinner("Validating API key..."):
                if check_api_key(api_key):
                    st.session_state['tabs_api_key'] = api_key.strip()
                    st.session_state['authenticated'] = True
                    st.success("✓ API key validated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Invalid API key. Please check your API key and try again.")
        else:
            st.warning("Please enter an API key.")
    
    st.markdown("---")
    st.caption("Contact your Tabs account manager via Slack if you need assistance.")

def load_uploaded_files(uploaded_files_dict, use_api_for_usage_bt=False):
    """
    Load uploaded CSV files into DataFrames.
    
    Args:
        uploaded_files_dict: Dictionary with keys matching usage_transformation.py structure:
            - 'usage_bt': Usage BT Report CSV (ignored if use_api_for_usage_bt=True)
            - 'customer_mapping': Customer Mapping CSV
            - 'community_quantity': Community Quantity Data Report CSV
            - 'business_quantity': Business Quantity Data Report CSV
            - 'minimum_report': Minimum Report CSV
            - 'combo_product_report': Combo Product Report CSV (tab-delimited)
        use_api_for_usage_bt: If True, generate Usage BT Report from API instead of loading from file
    
    Returns:
        dict: Dictionary of DataFrames matching usage_transformation.py structure
    """
    from usage_transformation import generate_usage_bt_report_from_api
    
    dataframes = {}
    
    try:
        # Load or generate Usage BT Report
        if use_api_for_usage_bt:
            dataframes['usage_bt'] = generate_usage_bt_report_from_api()
        elif uploaded_files_dict.get('usage_bt'):
            uploaded_files_dict['usage_bt'].seek(0)
            dataframes['usage_bt'] = pd.read_csv(uploaded_files_dict['usage_bt'])
        
        # Load Customer Mapping
        if uploaded_files_dict.get('customer_mapping'):
            uploaded_files_dict['customer_mapping'].seek(0)
            dataframes['customer_mapping'] = pd.read_csv(uploaded_files_dict['customer_mapping'])
        
        # Load Community Quantity Data Report
        if uploaded_files_dict.get('community_quantity'):
            uploaded_files_dict['community_quantity'].seek(0)
            dataframes['community_quantity'] = pd.read_csv(uploaded_files_dict['community_quantity'])
        
        # Load Business Quantity Data Report
        if uploaded_files_dict.get('business_quantity'):
            uploaded_files_dict['business_quantity'].seek(0)
            dataframes['business_quantity'] = pd.read_csv(uploaded_files_dict['business_quantity'])
        
        # Load Minimum Report
        if uploaded_files_dict.get('minimum_report'):
            uploaded_files_dict['minimum_report'].seek(0)
            dataframes['minimum_report'] = pd.read_csv(uploaded_files_dict['minimum_report'])
        
        # Load Combo Product Report (tab-delimited)
        if uploaded_files_dict.get('combo_product_report'):
            uploaded_files_dict['combo_product_report'].seek(0)
            dataframes['combo_product_report'] = pd.read_csv(
                uploaded_files_dict['combo_product_report'], 
                delimiter='\t'
            )
        
    except Exception as e:
        raise Exception(f"Error loading files: {str(e)}")
    
    return dataframes

# Usage Transformation Page
def page_usage_transformation():
    st.title("📊 SafelyYou Usage Transformation")
    st.markdown("---")
    
    # Main content area
    st.header("Usage Transformation Processing")
    st.write("Upload the required CSV files to process usage transformation. All 6 files are required before processing.")
    st.write("Contact your Tabs account manager via Slack if you have any questions.")
    
    st.markdown("---")
    
    # File uploaders in a grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Usage BT Report")
        use_api_for_usage_bt = st.checkbox(
            "Generate from Tabs API instead of uploading file",
            key="use_api_for_usage_bt",
            help="Check this to generate Usage BT Report from Tabs API (requires API key in session state)"
        )
        
        if not use_api_for_usage_bt:
            usage_bt_file = st.file_uploader(
                "Upload Usage BT Report CSV",
                type=['csv'],
                key="usage_bt",
                help="Upload the Usage BT Report CSV file"
            )
            if usage_bt_file is not None:
                st.success(f"✓ Uploaded: {usage_bt_file.name}")
                st.session_state['usage_bt_file'] = usage_bt_file
        else:
            st.info("ℹ️ Usage BT Report will be generated from Tabs API")
            if 'tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False):
                st.warning("⚠️ API key not found. Please authenticate using the authentication page.")
                if st.button("Go to Authentication", key="go_to_auth"):
                    st.session_state['authenticated'] = False
                    st.rerun()
        
        st.subheader("2. Customer Mapping")
        customer_mapping_file = st.file_uploader(
            "Upload Customer Mapping CSV",
            type=['csv'],
            key="customer_mapping",
            help="Upload the Customer Mapping CSV file"
        )
        if customer_mapping_file is not None:
            st.success(f"✓ Uploaded: {customer_mapping_file.name}")
            st.session_state['customer_mapping_file'] = customer_mapping_file
        
        st.subheader("3. Community Quantity Data Report")
        community_quantity_file = st.file_uploader(
            "Upload Community Quantity Data Report CSV",
            type=['csv'],
            key="community_quantity",
            help="Upload the Community Quantity Data Report CSV file"
        )
        if community_quantity_file is not None:
            st.success(f"✓ Uploaded: {community_quantity_file.name}")
            st.session_state['community_quantity_file'] = community_quantity_file
    
    with col2:
        st.subheader("4. Business Quantity Data Report")
        business_quantity_file = st.file_uploader(
            "Upload Business Quantity Data Report CSV",
            type=['csv'],
            key="business_quantity",
            help="Upload the Business Quantity Data Report CSV file"
        )
        if business_quantity_file is not None:
            st.success(f"✓ Uploaded: {business_quantity_file.name}")
            st.session_state['business_quantity_file'] = business_quantity_file
        
        st.subheader("5. Minimum Report")
        minimum_report_file = st.file_uploader(
            "Upload Minimum Report CSV",
            type=['csv'],
            key="minimum_report",
            help="Upload the Minimum Report CSV file"
        )
        if minimum_report_file is not None:
            st.success(f"✓ Uploaded: {minimum_report_file.name}")
            st.session_state['minimum_report_file'] = minimum_report_file
        
        st.subheader("6. Combo Product Report")
        combo_product_report_file = st.file_uploader(
            "Upload Combo Product Report CSV (Tab-delimited)",
            type=['csv'],
            key="combo_product_report",
            help="Upload the Combo Product Report CSV file (tab-delimited format)"
        )
        if combo_product_report_file is not None:
            st.success(f"✓ Uploaded: {combo_product_report_file.name}")
            st.session_state['combo_product_report_file'] = combo_product_report_file
    
    # Process button
    st.markdown("---")
    if st.button("Process Files", type="primary", key="process_button"):
        # Check if using API for Usage BT Report
        use_api_for_usage_bt = st.session_state.get('use_api_for_usage_bt', False)
        
        # Validate all required files are uploaded (skip usage_bt if using API)
        required_files = {
            'usage_bt': None if use_api_for_usage_bt else st.session_state.get('usage_bt_file'),
            'customer_mapping': st.session_state.get('customer_mapping_file'),
            'community_quantity': st.session_state.get('community_quantity_file'),
            'business_quantity': st.session_state.get('business_quantity_file'),
            'minimum_report': st.session_state.get('minimum_report_file'),
            'combo_product_report': st.session_state.get('combo_product_report_file')
        }
        
        # Check API key if using API
        if use_api_for_usage_bt and ('tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False)):
            st.error("API key not found or not authenticated. Cannot generate Usage BT Report from API.")
            if st.button("Go to Authentication", key="go_to_auth_from_process"):
                st.session_state['authenticated'] = False
                st.rerun()
        else:
            missing_files = [key for key, file in required_files.items() if file is None and not (key == 'usage_bt' and use_api_for_usage_bt)]
            
            if missing_files:
                st.error(f"Please upload all required files. Missing: {', '.join(missing_files)}")
            else:
                try:
                    # Step 1: Load files
                    with st.spinner("Step 1/3: Loading CSV files..."):
                        dataframes = load_uploaded_files(required_files, use_api_for_usage_bt=use_api_for_usage_bt)
                        st.success(f"✓ Loaded {len(dataframes)} files successfully")
                    
                    # Step 2: Process data
                    with st.spinner("Step 2/3: Processing data transformation..."):
                        output_df = process_data(dataframes)
                        if output_df is not None and not output_df.empty:
                            st.success(f"✓ Processed {len(output_df)} rows")
                        else:
                            st.warning("⚠ No data processed. Output is empty.")
                            output_df = None
                    
                    # Step 3: Deduplicate output
                    if output_df is not None and not output_df.empty:
                        with st.spinner("Step 3/3: Deduplicating output..."):
                            original_count = len(output_df)
                            output_df = deduplicate_output(output_df)
                            final_count = len(output_df)
                            if original_count != final_count:
                                st.info(f"✓ Removed {original_count - final_count} duplicate row(s)")
                            else:
                                st.success("✓ No duplicates found")
                        
                        # Store results in session state
                        st.session_state['processing_results'] = output_df
                        
                        # Display success message
                        st.success(f"✅ Processing completed successfully! Output: {len(output_df)} rows")
                    else:
                        st.error("Processing failed. No output data available.")
                
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
    
    # Display output if processing was completed
    if st.session_state.get('processing_results') is not None:
        output_df = st.session_state['processing_results']
        
        if not output_df.empty:
            st.markdown("---")
            st.subheader("📥 Download Output File")
            
            st.info(f"**Output Statistics:** Rows: {len(output_df)} | Columns: {len(output_df.columns)}")
            
            # Display preview
            with st.expander("Preview Output Data (first 20 rows)"):
                st.dataframe(output_df.head(20))
            
            # Convert to CSV
            csv_output = output_df.to_csv(index=False)
            
            # Download button
            st.download_button(
                label="Download Output CSV",
                data=csv_output,
                file_name="output.csv",
                mime="text/csv",
                key="download_output"
            )

# Flat BT Upload Page
def page_flat_bt_upload():
    st.title("📤 Flat BT Upload")
    st.markdown("---")
    
    # Main content area
    st.header("Upload Billing Terms")
    st.write("Upload a CSV file containing billing terms to create obligations in Tabs.")
    st.write("Contact your Tabs account manager via Slack if you have any questions.")
    
    st.markdown("---")
    
    # File uploader
    st.subheader("Billing Terms CSV File")
    bt_file = st.file_uploader(
        "Upload Billing Terms CSV file",
        type=['csv'],
        key="flat_bt_file",
        help="Upload the CSV file containing billing terms data"
    )
    
    if bt_file is not None:
        st.success(f"✓ Uploaded: {bt_file.name}")
        
        # Show preview
        try:
            bt_file.seek(0)
            preview_df = pd.read_csv(bt_file)
            st.info(f"**File Preview:** {len(preview_df)} rows, {len(preview_df.columns)} columns")
            with st.expander("Preview CSV Data (first 10 rows)"):
                st.dataframe(preview_df.head(10))
        except Exception as e:
            st.warning(f"Could not preview file: {str(e)}")
    
    # Upload button
    st.markdown("---")
    if st.button("Upload Billing Terms", type="primary", key="upload_bt_button"):
        # Access file from session state (managed by file_uploader widget)
        uploaded_file = st.session_state.get('flat_bt_file')
        if uploaded_file is None:
            st.error("Please upload a CSV file first.")
        elif 'tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False):
            st.error("API key not found or not authenticated. Please authenticate first.")
        else:
            try:
                from api import push_bt
                
                # Reset file pointer
                uploaded_file.seek(0)
                
                with st.spinner("Uploading billing terms to Tabs API..."):
                    # Call push_bt function
                    result = push_bt(uploaded_file, merchant_name='safelyyou')
                    
                    # Display results
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                        
                        # Check for success
                        if 200 <= status_code < 300:
                            st.success(f"✅ Billing terms uploaded successfully!")
                            
                            # Try to get obligation IDs from response
                            try:
                                result_data = result.json()
                                obligation_ids = result_data.get('billingTermIds', [])
                                
                                if obligation_ids:
                                    st.info(f"Created {len(obligation_ids)} obligation(s)")
                                    
                                    # Show obligation IDs
                                    with st.expander("View Created Obligation IDs"):
                                        for idx, ob_id in enumerate(obligation_ids, 1):
                                            st.write(f"{idx}. {ob_id}")
                                else:
                                    st.info("Upload completed, but no obligation IDs returned.")
                            except:
                                st.info("Upload completed successfully.")
                            
                            # Show errors if any
                            try:
                                result_data = result.json()
                                errors = result_data.get('errors', [])
                                if errors:
                                    with st.expander("⚠️ View Errors/Warnings"):
                                        for error in errors:
                                            st.warning(error)
                            except:
                                pass
                        else:
                            st.error(f"Upload failed with status code: {status_code}")
                            
                            # Show errors if available
                            try:
                                result_data = result.json()
                                errors = result_data.get('errors', [])
                                if errors:
                                    with st.expander("View Errors"):
                                        for error in errors:
                                            st.error(error)
                            except:
                                pass
                    else:
                        st.warning("Upload completed, but could not parse response details.")
                        
            except Exception as e:
                st.error(f"Error during upload: {str(e)}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

# Main app with navigation
def main():
    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Usage Transformation'
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 SafelyYou")
        st.markdown("---")
        
        # Page selection
        page = st.radio(
            "Navigation",
            ["Usage Transformation", "Flat BT Upload"],
            index=0 if st.session_state['current_page'] == 'Usage Transformation' else 1,
            key="page_selector"
        )
        
        # Update current page
        st.session_state['current_page'] = page
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", key="logout_button"):
            st.session_state['authenticated'] = False
            st.session_state['tabs_api_key'] = None
            st.session_state['current_page'] = 'Usage Transformation'
            st.rerun()
        
        st.markdown("---")
        st.caption("Contact your Tabs account manager via Slack if you need assistance.")
    
    # Route to appropriate page
    if st.session_state['current_page'] == 'Usage Transformation':
        page_usage_transformation()
    elif st.session_state['current_page'] == 'Flat BT Upload':
        page_flat_bt_upload()
 
if __name__ == "__main__":
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False):
        show_authentication()
    else:
        main()
