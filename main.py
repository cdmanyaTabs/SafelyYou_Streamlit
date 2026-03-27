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

def load_uploaded_files(uploaded_files_dict):
    """
    Load uploaded CSV files into DataFrames and generate Usage BT Report from API.
    
    Args:
        uploaded_files_dict: Dictionary with keys matching usage_transformation.py structure:
            - 'community_quantity': Community Quantity Data Report CSV
            - 'business_quantity': Business Quantity Data Report CSV
            - 'minimum_report': Minimum Report CSV
            - 'combo_product_report': Combo Product Report CSV (auto-detects comma or tab delimiter)
    
    Returns:
        dict: Dictionary of DataFrames matching usage_transformation.py structure
    """
    from usage_transformation import generate_usage_bt_report_from_api
    
    dataframes = {}
    
    try:
        # Always generate Usage BT Report from API
        dataframes['usage_bt'] = generate_usage_bt_report_from_api()
        
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
        
        # Load Combo Product Report (auto-detect delimiter)
        if uploaded_files_dict.get('combo_product_report'):
            uploaded_files_dict['combo_product_report'].seek(0)
            # Try tab-delimited first
            dataframes['combo_product_report'] = pd.read_csv(
                uploaded_files_dict['combo_product_report'], 
                delimiter='\t'
            )
            # If only 1 column detected, it's probably comma-delimited
            if len(dataframes['combo_product_report'].columns) == 1:
                uploaded_files_dict['combo_product_report'].seek(0)
                dataframes['combo_product_report'] = pd.read_csv(
                    uploaded_files_dict['combo_product_report'], 
                    delimiter=','
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
    st.write("Upload the required CSV files to process usage transformation. All 4 files are required before processing.")
    st.write("**Note:** Tabs Usage Products are automatically generated from the Tabs API.")
    st.write("Contact your Tabs account manager via Slack if you have any questions.")
    
    st.markdown("---")
    
    # File uploaders in a grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Tabs Usage Products")
        st.info("ℹ️ Usage BT Report will be automatically generated from Tabs API")
        if 'tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False):
            st.warning("⚠️ API key not found. Please authenticate using the authentication page.")
            if st.button("Go to Authentication", key="go_to_auth"):
                st.session_state['authenticated'] = False
                st.rerun()
        
        st.subheader("2. Product Minimums Report")
        minimum_report_file = st.file_uploader(
            "Upload Minimum Report CSV",
            type=['csv'],
            key="minimum_report",
            help="Upload the Minimum Report CSV file"
        )
        if minimum_report_file is not None:
            st.success(f"✓ Uploaded: {minimum_report_file.name}")
            st.session_state['minimum_report_file'] = minimum_report_file
        
    with col2:
        st.subheader("3. By Community Data Report")
        community_quantity_file = st.file_uploader(
            "Upload Community Quantity Data Report CSV",
            type=['csv'],
            key="community_quantity",
            help="Upload the Community Quantity Data Report CSV file"
        )
        if community_quantity_file is not None:
            st.success(f"✓ Uploaded: {community_quantity_file.name}")
            st.session_state['community_quantity_file'] = community_quantity_file
        
        st.subheader("4. By Business Unit Data Report")
        business_quantity_file = st.file_uploader(
            "Upload Business Quantity Data Report CSV",
            type=['csv'],
            key="business_quantity",
            help="Upload the Business Quantity Data Report CSV file"
        )
        if business_quantity_file is not None:
            st.success(f"✓ Uploaded: {business_quantity_file.name}")
            st.session_state['business_quantity_file'] = business_quantity_file
        
        st.subheader("5. Combination Product Report")
        combo_product_report_file = st.file_uploader(
            "Upload Combo Product Report CSV",
            type=['csv'],
            key="combo_product_report",
            help="Upload the Combo Product Report CSV file (comma or tab-delimited)"
        )
        if combo_product_report_file is not None:
            st.success(f"✓ Uploaded: {combo_product_report_file.name}")
            st.session_state['combo_product_report_file'] = combo_product_report_file
    
    # Process button
    st.markdown("---")
    if st.button("Process Files", type="primary", key="process_button"):
        # Validate all required files are uploaded
        required_files = {
            'community_quantity': st.session_state.get('community_quantity_file'),
            'business_quantity': st.session_state.get('business_quantity_file'),
            'minimum_report': st.session_state.get('minimum_report_file'),
            'combo_product_report': st.session_state.get('combo_product_report_file')
        }
        
        # Check API key
        if 'tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False):
            st.error("API key not found or not authenticated. Cannot generate Usage BT Report from API.")
            if st.button("Go to Authentication", key="go_to_auth_from_process"):
                st.session_state['authenticated'] = False
                st.rerun()
        else:
            missing_files = [key for key, file in required_files.items() if file is None]
            
            if missing_files:
                st.error(f"Please upload all required files. Missing: {', '.join(missing_files)}")
            else:
                try:
                    # Step 1: Load files
                    with st.spinner("Step 1/3: Loading CSV files and generating Usage BT Report from API..."):
                        dataframes = load_uploaded_files(required_files)
                        st.success(f"✓ Loaded {len(dataframes)} files successfully")
                    
                    # Step 2: Process data
                    with st.spinner("Step 2/3: Processing data transformation..."):
                        output_df, unmapped_customers = process_data(dataframes)
                        if output_df is not None and not output_df.empty:
                            st.success(f"✓ Processed {len(output_df)} rows")
                        else:
                            st.warning("⚠ No data processed. Output is empty.")
                            output_df = None
                        
                        # Store unmapped customers in session state
                        st.session_state['unmapped_customers'] = unmapped_customers if unmapped_customers else []
                    
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
            
            # Display unmapped customers if any
            unmapped_customers = st.session_state.get('unmapped_customers', [])
            if unmapped_customers and len(unmapped_customers) > 0:
                st.markdown("---")
                st.warning(f"⚠️ {len(unmapped_customers)} customer(s) could not be mapped and were excluded from output")
                
                with st.expander(f"View {len(unmapped_customers)} Unmapped Customers", expanded=False):
                    unmapped_df = pd.DataFrame(unmapped_customers)
                    st.dataframe(unmapped_df, use_container_width=True)
                    
                    # Allow download of unmapped customers
                    unmapped_csv = unmapped_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Unmapped Customers CSV",
                        data=unmapped_csv,
                        file_name="unmapped_customers.csv",
                        mime="text/csv",
                        key="download_unmapped"
                    )
            else:
                st.success("✅ All customers were successfully mapped!")

# Flat BT Upload Page
def page_flat_bt_upload():
    st.title("📤 Flat BT Upload")
    st.markdown("---")
    
    # Main content area
    st.header("Upload Billing Terms")
    st.write("Upload a CSV file containing billing terms to create obligations in Tabs. Here is a billing terms template file: https://docs.google.com/spreadsheets/d/1TsTDZ6KJKp5QTSD4kH1tUitjcPchtDqRiyaptkwm06c/edit?usp=sharing")
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
    
    # Session state management for validation tracking
    # Check if file changed - reset validation if different file
    if bt_file is not None:
        current_file_name = bt_file.name
        if st.session_state.get('validated_file_name') != current_file_name:
            st.session_state['validation_completed'] = False
            st.session_state['validation_results'] = None
            st.session_state['validated_file_name'] = current_file_name
    
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
        
        # Validate Customers button
        st.markdown("---")
        st.subheader("Step 1: Validate Customer Names")
        st.write("Check which customers in your CSV can be found in the system before creating obligations.")
        
        if st.button("🔍 Validate Customers", type="secondary", key="validate_customers_button"):
            uploaded_file = st.session_state.get('flat_bt_file')
            if uploaded_file is None:
                st.error("Please upload a CSV file first.")
            elif 'tabs_api_key' not in st.session_state or not st.session_state.get('authenticated', False):
                st.error("API key not found or not authenticated. Please authenticate first.")
            else:
                try:
                    from api import validate_bt_customers
                    
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    with st.spinner("Validating customer names..."):
                        # Call validation function
                        results = validate_bt_customers(uploaded_file)
                        
                        # Store results in session state
                        st.session_state['validation_completed'] = True
                        st.session_state['validation_results'] = results
                        
                except Exception as e:
                    st.error(f"Error during validation: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
        
        # Display validation results if available
        if st.session_state.get('validation_completed', False) and st.session_state.get('validation_results'):
            results = st.session_state['validation_results']
            
            st.markdown("---")
            st.subheader("Validation Results")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", results['total_rows'])
            with col2:
                st.metric("Customers Found", results['found_count'], 
                         delta=None if results['found_count'] == results['total_rows'] else "")
            with col3:
                st.metric("Not Found", results['unfound_count'],
                         delta=f"-{results['unfound_count']}" if results['unfound_count'] > 0 else "0")
            
            # Show unfound customers prominently if any
            if results['unfound_count'] > 0:
                st.error(f"⚠️ {results['unfound_count']} customer(s) could not be found in the system:")
                unfound_df = pd.DataFrame(results['unfound_customers'])
                st.dataframe(unfound_df, use_container_width=True)
                st.warning("**Note:** Rows with unfound customers will be skipped during upload. You can still proceed with the upload for the customers that were found.")
            else:
                st.success("✅ All customers found in the system!")
            
            # Show found customers in expander
            if results['found_count'] > 0:
                with st.expander(f"✓ View {results['found_count']} Found Customer(s)"):
                    found_df = pd.DataFrame(results['found_customers'])
                    st.dataframe(found_df, use_container_width=True)
            
            # Show any parsing errors
            if results.get('errors'):
                with st.expander("⚠️ View Validation Errors"):
                    for error in results['errors']:
                        st.warning(error)
    
    # Upload button
    st.markdown("---")
    st.subheader("Step 2: Upload Billing Terms")
    
    # Check if validation completed
    validation_completed = st.session_state.get('validation_completed', False)
    if not validation_completed and bt_file is not None:
        st.info("💡 Please validate customer names first before uploading billing terms.")
    
    # Show validation reminder if completed
    if validation_completed and st.session_state.get('validation_results'):
        results = st.session_state['validation_results']
        if results['unfound_count'] > 0:
            st.warning(f"⚠️ Reminder: {results['unfound_count']} customer(s) were not found and will be skipped.")
        else:
            st.success(f"✓ Validation passed - ready to create {results['found_count']} obligation(s)")
    
    # Disable button if validation not completed
    upload_button_disabled = not validation_completed
    
    if st.button("📤 Upload Billing Terms", type="primary", key="upload_bt_button", disabled=upload_button_disabled):
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
                
                # Create containers for progress display
                progress_container = st.container()
                status_container = st.container()
                
                with progress_container:
                    st.write("### Upload Progress")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                # Define callback for progress updates
                def progress_callback(current, total, customer_name, status, error_msg=None):
                    """Callback to update progress in real-time"""
                    progress = current / total if total > 0 else 0
                    progress_bar.progress(progress)
                    
                    if status == "success":
                        status_text.text(f"✅ {current}/{total}: {customer_name} - Success")
                    elif status == "failed":
                        status_text.text(f"❌ {current}/{total}: {customer_name} - Failed")
                    elif status == "processing":
                        status_text.text(f"⏳ {current}/{total}: Processing {customer_name}...")
                
                # Call push_bt function with progress callback
                result = push_bt(uploaded_file, merchant_name='safelyyou', progress_callback=progress_callback)
                
                # Clear progress display
                progress_bar.empty()
                status_text.empty()
                
                with status_container:
                    # Display results summary
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                        result_data = result.json()
                        
                        successful_count = result_data.get('successful_count', 0)
                        failed_count = result_data.get('failed_count', 0)
                        total_count = successful_count + failed_count
                        
                        # Show summary
                        st.write("### Upload Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total", total_count)
                        with col2:
                            st.metric("✅ Succeeded", successful_count)
                        with col3:
                            st.metric("❌ Failed", failed_count)
                        
                        # Show successful obligations
                        if successful_count > 0:
                            st.success(f"✅ Successfully uploaded {successful_count} billing term(s)")
                            
                            obligation_ids = result_data.get('billingTermIds', [])
                            if obligation_ids:
                                with st.expander(f"View {len(obligation_ids)} Created Obligation IDs"):
                                    for idx, ob_id in enumerate(obligation_ids, 1):
                                        st.write(f"{idx}. `{ob_id}`")
                        
                        # Show failed obligations
                        errors = result_data.get('errors', [])
                        if errors:
                            st.error(f"❌ {failed_count} billing term(s) failed to upload")
                            with st.expander(f"View {len(errors)} Error Details", expanded=True):
                                for idx, error in enumerate(errors, 1):
                                    # Parse error to extract row number and details
                                    if error.startswith("Row "):
                                        # Split into row number and error message
                                        parts = error.split(": ", 1)
                                        if len(parts) == 2:
                                            row_info = parts[0]
                                            error_details = parts[1]
                                            st.markdown(f"**{row_info}:**")
                                            # Display error details with proper formatting
                                            if "\n" in error_details:
                                                # Multi-line error with bullet points
                                                st.markdown(error_details)
                                            else:
                                                st.markdown(f"- {error_details}")
                                        else:
                                            st.markdown(f"**{idx}.** {error}")
                                    else:
                                        st.markdown(f"**{idx}.** {error}")
                                    
                                    # Add a subtle divider between errors
                                    if idx < len(errors):
                                        st.markdown("---")
                        
                        # Overall status message
                        if failed_count == 0 and successful_count > 0:
                            st.balloons()
                        elif successful_count == 0:
                            st.error("All billing terms failed to upload. Please check the errors above.")
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
