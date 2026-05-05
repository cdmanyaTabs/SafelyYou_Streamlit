import pandas as pd
from datetime import datetime, timedelta
import os
import numpy as np
import re
import logging
import sys

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Configure logging to console (shared with api.py)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console only
    ]
)

logger = logging.getLogger(__name__)

# Store original print function
_original_print = print

# Create a wrapper function that logs to file and prints to console
def log_print(*args, **kwargs):
    """
    Replacement for print() that logs to file and console.
    """
    message = ' '.join(str(arg) for arg in args)
    
    # Log to file
    logger.info(message)
    
    # Also print to console
    _original_print(message)

# Override built-in print to automatically log all print() calls to file
# This way all existing print() statements are automatically logged
print = log_print

# ============================================================================
# CONFIGURATION AND FILE PATHS
# ============================================================================

def get_file_paths():
    """
    Define the paths to all input CSV files.
    Update these paths according to your directory structure.
    """
    print("=" * 80)
    print("STEP 0: CONFIGURING FILE PATHS")
    print("=" * 80)
    
    file_paths = {
        'usage_bt': 'Usage_BT_Report.csv',
        'community_quantity': 'Community_Quantity_Data_Report.csv',
        'business_quantity': 'Business_Quantity_Data_Report.csv',
        'minimum_report': 'Minimum_Report.csv',
        'combo_product_report': 'combo_product_report.csv'
    }
    
    for key, path in file_paths.items():
        print(f"  [{key}] -> {path}")
    
    return file_paths

# ============================================================================
# DATA LOADING
# ============================================================================

def load_csv_files(file_paths, use_api_for_usage_bt=False):
    """
    Load all CSV files into DataFrames with error handling.
    
    Args:
        file_paths: Dictionary of file paths
        use_api_for_usage_bt: If True, generate Usage BT Report from API instead of loading from file
    
    Returns:
        dict: Dictionary of DataFrames
    """
    print("\n" + "=" * 80)
    print("STEP 1: LOADING CSV FILES")
    print("=" * 80)
    
    dataframes = {}
    
    try:
        if use_api_for_usage_bt:
            print("\n[1.1] Generating Usage BT Report from API...")
            dataframes['usage_bt'] = generate_usage_bt_report_from_api()
            print(f"      ✓ Generated successfully with shape: {dataframes['usage_bt'].shape}")
            print(f"      Columns: {list(dataframes['usage_bt'].columns)}")
        else:
            print("\n[1.1] Loading Usage BT Report CSV...")
            dataframes['usage_bt'] = pd.read_csv(file_paths['usage_bt'])
            print(f"      ✓ Loaded successfully with shape: {dataframes['usage_bt'].shape}")
            print(f"      Columns: {list(dataframes['usage_bt'].columns)}")
        
        print("\n[1.2] Loading Community Quantity Data Report CSV...")
        dataframes['community_quantity'] = pd.read_csv(file_paths['community_quantity'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['community_quantity'].shape}")
        print(f"      Columns: {list(dataframes['community_quantity'].columns)}")
        
        print("\n[1.3] Loading Business Quantity Data Report CSV...")
        dataframes['business_quantity'] = pd.read_csv(file_paths['business_quantity'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['business_quantity'].shape}")
        print(f"      Columns: {list(dataframes['business_quantity'].columns)}")
        
        print("\n[1.4] Loading Minimum Report CSV...")
        dataframes['minimum_report'] = pd.read_csv(file_paths['minimum_report'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['minimum_report'].shape}")
        print(f"      Columns: {list(dataframes['minimum_report'].columns)}")
        
        print("\n[1.5] Loading Combo Product Report CSV...")
        # Try tab-delimited first
        dataframes['combo_product_report'] = pd.read_csv(file_paths['combo_product_report'], delimiter='\t')
        # If only 1 column detected, it's probably comma-delimited
        if len(dataframes['combo_product_report'].columns) == 1:
            print("      ⚠ Only 1 column detected with tab delimiter, trying comma delimiter...")
            logging.info("[LOAD] Combo Product Report: Only 1 column with tab delimiter, retrying with comma")
            dataframes['combo_product_report'] = pd.read_csv(file_paths['combo_product_report'], delimiter=',')
            print(f"      ✓ Loaded successfully with COMMA delimiter")
            logging.info("[LOAD] Using COMMA delimiter")
        else:
            print(f"      ✓ Loaded successfully with TAB delimiter")
            logging.info("[LOAD] Using TAB delimiter")
        print(f"      Shape: {dataframes['combo_product_report'].shape}")
        print(f"      Columns: {list(dataframes['combo_product_report'].columns)}")
        logging.info(f"[LOAD] Combo Product Report Loaded")
        logging.info(f"[LOAD] Shape: {dataframes['combo_product_report'].shape}")
        logging.info(f"[LOAD] Columns: {list(dataframes['combo_product_report'].columns)}")
        
    except FileNotFoundError as e:
        print(f"      ✗ ERROR: File not found - {e}")
        raise
    except Exception as e:
        print(f"      ✗ ERROR: {e}")
        raise
    
    return dataframes

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_product_contains(product_name, keywords):
    """
    Check if product name contains any of the keywords (case-insensitive).
    """
    product_name = str(product_name).upper()
    return any(keyword.upper() in product_name for keyword in keywords)

def get_addon_variants():
    """
    Return all possible addon keyword variants.
    """
    return ['ADDON', 'ADD-ON', 'ADD ON']

def safe_convert_to_numeric(value):
    """
    Safely convert any value to numeric (float or int).
    Handles strings, NaN, None, and numpy types.
    
    Returns:
        float: Converted numeric value
        0: If conversion fails or value is NaN/None
    """
    try:
        # Handle None and NaN
        if value is None:
            return 0.0
        
        if pd.isna(value):
            return 0.0
        
        # Convert to string first to handle any type
        str_value = str(value).strip()
        
        # Handle empty strings
        if str_value == '' or str_value.lower() == 'nan':
            return 0.0
        
        # Try converting to float
        numeric_value = float(str_value)
        
        # Check if result is NaN
        if pd.isna(numeric_value):
            return 0.0
        
        return numeric_value
    
    except (ValueError, TypeError, AttributeError):
        return 0.0

def find_column_case_insensitive(df, column_name):
    """
    Find a column in a DataFrame by case-insensitive name matching.
    First tries exact match, then falls back to "starts with" matching.
    
    Args:
        df: pandas DataFrame
        column_name: The column name to search for (case-insensitive)
    
    Returns:
        str: The actual column name from the DataFrame if found, None otherwise
    """
    if df is None or len(df.columns) == 0:
        return None
    
    column_name_lower = str(column_name).lower().strip()
    
    # First pass: Try exact match
    for col in df.columns:
        if str(col).lower().strip() == column_name_lower:
            return col
    
    # Second pass: Try "starts with" match (for columns like "Active Date [TBD]")
    for col in df.columns:
        if str(col).lower().strip().startswith(column_name_lower):
            return col
    
    return None

def find_minimum_quantity_column(row):
    """
    Find the minimum quantity column name with flexible matching.
    Tries exact match, case-insensitive, and common variations.
    
    Args:
        row: pandas Series or dict-like object with column names
    
    Returns:
        str: Column name if found, None otherwise
    """
    # Get available columns
    if hasattr(row, 'index'):
        available_columns = list(row.index)
    elif hasattr(row, 'keys'):
        available_columns = list(row.keys())
    else:
        return None
    
    # Try exact match first
    exact_match = 'minimum quantity'
    if exact_match in available_columns:
        return exact_match
    
    # Try case-insensitive match
    for col in available_columns:
        if str(col).lower() == exact_match.lower():
            return col
    
    # Try common variations
    variations = [
        'Minimum Quantity',
        'minimum_quantity',
        'Minimum_Quantity',
        'MINIMUM QUANTITY',
        'min quantity',
        'Min Quantity',
        'min_quantity',
        'Min_Quantity'
    ]
    
    for variation in variations:
        if variation in available_columns:
            return variation
    
    # Try case-insensitive match for variations
    for col in available_columns:
        col_lower = str(col).lower().strip()
        for variation in variations:
            if col_lower == variation.lower():
                return col
    
    return None

def extract_product_keywords(product_name):
    """
    Extract key identifying keywords from product name.
    Returns list of keywords: [product_type, business_unit (if present)]
    
    Product types: RESPOND, AWARE, ADDON
    Business units: MC, AL, SNF
    """
    print(f"          [KEYWORD_EXTRACTION] Original product name: '{product_name}'")
    
    # Normalize: uppercase and replace special chars with spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(product_name).upper())
    normalized = ' '.join(normalized.split())  # Remove extra spaces
    print(f"          [KEYWORD_EXTRACTION] Normalized product name: '{normalized}'")
    
    keywords = []
    
    # Check for product type
    if 'RESPOND' in normalized:
        keywords.append('RESPOND')
        print(f"          [KEYWORD_EXTRACTION] Found product type: 'RESPOND'")
    elif 'AWARE' in normalized:
        keywords.append('AWARE')
        print(f"          [KEYWORD_EXTRACTION] Found product type: 'AWARE'")
    elif any(variant in normalized for variant in ['ADDON', 'ADD ON']):
        keywords.append('ADDON')
        print(f"          [KEYWORD_EXTRACTION] Found product type: 'ADDON'")
    else:
        print(f"          [KEYWORD_EXTRACTION] No product type found (RESPOND/AWARE/ADDON)")
    
    # Check for business unit type
    # Use word boundaries to avoid matching "MC" in "MCDONALDS" etc.
    words = normalized.split()
    print(f"          [KEYWORD_EXTRACTION] Split into words: {words}")
    if 'MC' in words:
        keywords.append('MC')
        print(f"          [KEYWORD_EXTRACTION] Found business unit: 'MC'")
    elif 'AL' in words:
        keywords.append('AL')
        print(f"          [KEYWORD_EXTRACTION] Found business unit: 'AL'")
    elif 'SNF' in words:
        keywords.append('SNF')
        print(f"          [KEYWORD_EXTRACTION] Found business unit: 'SNF'")
    else:
        print(f"          [KEYWORD_EXTRACTION] No business unit found (MC/AL/SNF)")
    
    print(f"          [KEYWORD_EXTRACTION] Final extracted keywords: {keywords}")
    return keywords

def fuzzy_match_product(usage_product_name, minimum_product_name, extracted_keywords):
    """
    Check if minimum_product_name contains all the extracted keywords.
    
    Args:
        usage_product_name: Product name from Usage BT Report
        minimum_product_name: Product name from Minimum Report
        extracted_keywords: Keywords extracted from usage_product_name
    
    Returns:
        bool: True if all keywords found in minimum_product_name
    """
    print(f"             [FUZZY_MATCH] Comparing:")
    print(f"                Usage product: '{usage_product_name}'")
    print(f"                Minimum product: '{minimum_product_name}'")
    print(f"                Extracted keywords: {extracted_keywords}")
    
    # Normalize minimum product name
    normalized_min = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(minimum_product_name).upper())
    normalized_min = ' '.join(normalized_min.split())
    print(f"             [FUZZY_MATCH] Normalized minimum product: '{normalized_min}'")
    
    # Check if all keywords are present
    all_found = True
    for keyword in extracted_keywords:
        print(f"             [FUZZY_MATCH] Checking keyword: '{keyword}'")
        # Special handling for ADDON variants
        if keyword == 'ADDON':
            found = any(variant in normalized_min for variant in ['ADDON', 'ADD ON'])
            if found:
                print(f"             [FUZZY_MATCH]   → Found 'ADDON' or 'ADD ON' in normalized string")
            else:
                print(f"             [FUZZY_MATCH]   → NOT found 'ADDON' or 'ADD ON' in normalized string")
                all_found = False
                break
        else:
            # For MC, AL, SNF - check as whole words
            if keyword in ['MC', 'AL', 'SNF']:
                words = normalized_min.split()
                print(f"             [FUZZY_MATCH]   → Split into words: {words}")
                found = keyword in words
                if found:
                    print(f"             [FUZZY_MATCH]   → Found '{keyword}' as whole word")
                else:
                    print(f"             [FUZZY_MATCH]   → NOT found '{keyword}' as whole word")
                    all_found = False
                    break
            else:
                # For RESPOND, AWARE - check substring
                found = keyword in normalized_min
                if found:
                    print(f"             [FUZZY_MATCH]   → Found '{keyword}' as substring")
                else:
                    print(f"             [FUZZY_MATCH]   → NOT found '{keyword}' as substring")
                    all_found = False
                    break
    
    print(f"             [FUZZY_MATCH] Final match result: {all_found}")
    return all_found

def parse_active_date(date_value, current_date=None):
    """
    Parse Active Date column value with flexible format handling.
    Handles common formats: MM/DD/YYYY, YYYY-MM-DD, DD/MM/YYYY, etc.
    
    Args:
        date_value: Date value from Active Date column (can be string, datetime, etc.)
        current_date: datetime object to compare against (defaults to datetime.now())
    
    Returns:
        datetime: Parsed datetime object, or None if invalid or cannot parse
    """
    if current_date is None:
        current_date = datetime.now()
    
    # Handle None and NaN
    if date_value is None or pd.isna(date_value):
        return None
    
    # If already a datetime object, return it
    if isinstance(date_value, datetime):
        return date_value
    
    # Convert to string
    date_str = str(date_value).strip()
    
    # Handle empty strings
    if date_str == '' or date_str.lower() == 'nan':
        return None
    
    # Try multiple common date formats explicitly first
    common_formats = [
        '%Y-%m-%d',           # 2025-09-01
        '%m/%d/%Y',           # 09/01/2025
        '%d/%m/%Y',           # 01/09/2025
        '%Y/%m/%d',           # 2025/09/01
        '%m-%d-%Y',           # 09-01-2025
        '%d-%m-%Y',           # 01-09-2025
        '%Y-%m-%d %H:%M:%S',  # 2025-09-01 00:00:00
        '%m/%d/%y',           # 09/01/25
        '%d/%m/%y',           # 01/09/25
    ]
    
    for fmt in common_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date
        except (ValueError, TypeError):
            continue
    
    # Fallback to pandas to_datetime (without deprecated parameter)
    try:
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        
        # Check if parsing was successful
        if pd.isna(parsed_date):
            return None
        
        # Convert to datetime object
        if isinstance(parsed_date, pd.Timestamp):
            return parsed_date.to_pydatetime()
        
        return parsed_date
    
    except (ValueError, TypeError, AttributeError):
        return None

# ============================================================================
# API-BASED USAGE BT REPORT GENERATION
# ============================================================================

def build_contract_lookup(contracts_response):
    """
    Build a dictionary mapping contractId to customerId from contracts API response.
    
    Args:
        contracts_response: JSON response from get_all_contracts() API
    
    Returns:
        dict: Dictionary mapping contract_id -> customer_id
    """
    contract_lookup = {}
    contracts_data = contracts_response.get("payload", {}).get("data", [])
    
    for contract in contracts_data:
        contract_id = contract.get("id")
        customer_id = contract.get("customerId")
        if contract_id and customer_id:
            contract_lookup[contract_id] = customer_id
    
    return contract_lookup

def build_event_type_lookup(event_types_df):
    """
    Build a dictionary mapping eventTypeId to eventTypeName.
    
    Args:
        event_types_df: DataFrame from get_event_ids() function
    
    Returns:
        dict: Dictionary mapping event_type_id -> event_type_name
    """
    event_type_lookup = {}
    
    TARGET_EVENT_TYPE_ID = "b04dc31f-9e7a-4e65-8f15-9a45e1555c7f"  # MC beds
    
    if not event_types_df.empty:
        for _, row in event_types_df.iterrows():
            event_type_id = row.get("id")
            event_type_name = row.get("name")
            if event_type_id and event_type_name:
                event_type_lookup[event_type_id] = event_type_name
    
    print(f"[DEBUG_EVENT_TYPES] Total event types in lookup: {len(event_type_lookup)}")
    if TARGET_EVENT_TYPE_ID in event_type_lookup:
        print(f"[DEBUG_EVENT_TYPES] ✓ Target event type {TARGET_EVENT_TYPE_ID} FOUND: '{event_type_lookup[TARGET_EVENT_TYPE_ID]}'")
    else:
        print(f"[DEBUG_EVENT_TYPES] ✗ Target event type {TARGET_EVENT_TYPE_ID} NOT FOUND in lookup")
        print(f"[DEBUG_EVENT_TYPES] Sample event types (first 10): {list(event_type_lookup.items())[:10]}")
    
    return event_type_lookup

def generate_usage_bt_report_from_api():
    """
    Generate Usage_BT_Report DataFrame from Tabs API.
    
    Fetches obligations, contracts, and event types from API and creates
    a DataFrame matching the structure of Usage_BT_Report.csv.
    
    Returns:
        pd.DataFrame: DataFrame with columns: 'customer ID', 'Product name', 'event type name'
    """
    print("\n" + "=" * 80)
    print("GENERATING USAGE BT REPORT FROM API")
    print("=" * 80)
    
    try:
        # Import API functions
        from api import get_all_billing_terms, get_all_contracts
        from api import get_event_ids, get_excluded_customer_ids
        
        # Step 1: Fetch billing terms
        print("\n[API] Fetching billing terms from Tabs API...")
        obligations_response = get_all_billing_terms()
        obligations_data = obligations_response.get("payload", {}).get("data", [])
        print(f"      ✓ Retrieved {len(obligations_data)} billing terms (UNIT type, date filtered)")
        
        # Step 2: Fetch event types (contract fetching now done in get_all_billing_terms)
        print("\n[API] Fetching event types from Tabs API...")
        event_types_df = get_event_ids()
        event_type_lookup = build_event_type_lookup(event_types_df)
        print(f"      ✓ Built event type lookup with {len(event_type_lookup)} event types")
        
        # Step 3: Build customer exclusion list
        print("\n[API] Building customer exclusion list...")
        excluded_customer_ids = get_excluded_customer_ids()
        print(f"      ✓ Found {len(excluded_customer_ids)} customers to exclude (with specified parent IDs)")
        
        # Step 4: Process billing terms and build report rows
        print("\n[API] Processing billing terms to build Usage BT Report...")
        report_rows = []
        skipped_count = 0
        
        # Debug target customer
        TARGET_DEBUG_CUSTOMER = "0184231f-2f82-4afa-8a38-e4417afed001"
        target_found_in_obligations = False
        
        for obligation in obligations_data:
            try:
                # Extract contractId and customerId (now directly available from billing terms)
                contract_id = obligation.get("contractId")
                customer_id = obligation.get("customerId")
                
                if not contract_id or not customer_id:
                    skipped_count += 1
                    continue
                
                # Debug: Check if this obligation is for target customer with target contract
                if str(customer_id) == "9e660ece-132a-47ec-bb89-df1161c5395e" and str(contract_id) == "5f8bb451-587a-41a1-add3-d9b5c9208326":
                    billing_schedule = obligation.get("billingSchedule", {})
                    print(f"\n[DEBUG_TARGET_OBLIGATION] ✓ Found obligation for customer 9e660ece-132a-47ec-bb89-df1161c5395e")
                    print(f"[DEBUG_TARGET_OBLIGATION] Contract ID: {contract_id}")
                    print(f"[DEBUG_TARGET_OBLIGATION] Obligation ID: {obligation.get('id')}")
                    print(f"[DEBUG_TARGET_OBLIGATION] Product Name: {billing_schedule.get('name')}")
                    print(f"[DEBUG_TARGET_OBLIGATION] Billing Type: {billing_schedule.get('billingType')}")
                    print(f"[DEBUG_TARGET_OBLIGATION] Event Type ID: {billing_schedule.get('eventTypeId')}")
                
                # Debug: Check if this is the target customer
                if str(customer_id) == TARGET_DEBUG_CUSTOMER:
                    target_found_in_obligations = True
                    logging.info(f"\n{'='*80}")
                    logging.info(f"[DEBUG_TARGET] ✓ TARGET CUSTOMER FOUND IN OBLIGATIONS")
                    logging.info(f"[DEBUG_TARGET] Customer ID: {customer_id}")
                    logging.info(f"[DEBUG_TARGET] Obligation ID: {obligation.get('id')}")
                    logging.info(f"[DEBUG_TARGET] Contract ID: {contract_id}")
                    print(f"[DEBUG] Target customer {TARGET_DEBUG_CUSTOMER} found in obligations")
                
                # Skip customers with excluded parent IDs
                if customer_id in excluded_customer_ids:
                    if str(customer_id) == TARGET_DEBUG_CUSTOMER:
                        logging.info(f"[DEBUG_TARGET] ✗✗✗ FILTERED OUT: Customer has excluded parent ID")
                        print(f"[DEBUG] Target customer EXCLUDED due to parent ID")
                    skipped_count += 1
                    continue
                
                # Extract billing schedule and check billing type
                billing_schedule = obligation.get("billingSchedule", {})
                billing_type = billing_schedule.get("billingType")
                
                # FILTER: Only include UNIT billing type (exclude FLAT and others)
                if billing_type != "UNIT":
                    if str(customer_id) == TARGET_DEBUG_CUSTOMER:
                        logging.info(f"[DEBUG_TARGET] ✗✗✗ FILTERED OUT: Non-UNIT billing type: {billing_type}")
                        print(f"[DEBUG] Target customer EXCLUDED due to billing type: {billing_type}")
                    skipped_count += 1
                    continue
                
                # DEBUG: Track target customer
                if str(customer_id) == "4a5a2962-bcf8-4a8b-a434-e1868072b0bd":
                    logging.info("\n[DEBUG_GENERATE] ✓✓✓ TARGET CUSTOMER FOUND IN OBLIGATIONS ✓✓✓")
                    logging.info(f"[DEBUG_GENERATE] Obligation ID: {obligation.get('id')}")
                    logging.info(f"[DEBUG_GENERATE] Contract ID: {contract_id}")
                    logging.info(f"[DEBUG_GENERATE] Customer ID: {customer_id}")
                    logging.info(f"[DEBUG_GENERATE] Service Start Date: {obligation.get('serviceStartDate')}")
                    logging.info(f"[DEBUG_GENERATE] Service End Date: {obligation.get('serviceEndDate')}")
                    logging.info(f"[DEBUG_GENERATE] Billing Schedule Name: {billing_schedule.get('name')}")
                    logging.info(f"[DEBUG_GENERATE] Billing Schedule End Date: {billing_schedule.get('endDate')}")
                    logging.info(f"[DEBUG_GENERATE] Event Type ID: {billing_schedule.get('eventTypeId')}")
                    logging.info(f"[DEBUG_GENERATE] Billing Type: {billing_type}")
                    print("[DEBUG] TARGET CUSTOMER FOUND IN OBLIGATIONS")
                
                # Extract Product name from billingSchedule (already extracted above)
                product_name = billing_schedule.get("name", "")
                
                # Extract eventTypeId and lookup event type name
                event_type_id = billing_schedule.get("eventTypeId")
                event_type_name = ""
                if event_type_id:
                    event_type_name = event_type_lookup.get(event_type_id, "")
                    
                    # Debug: Track the MC beds event type specifically
                    if str(event_type_id) == "b04dc31f-9e7a-4e65-8f15-9a45e1555c7f":
                        print(f"[DEBUG_MC_BEDS] Found obligation with MC beds event type")
                        print(f"[DEBUG_MC_BEDS] Event Type ID: {event_type_id}")
                        print(f"[DEBUG_MC_BEDS] Event Type Name from lookup: '{event_type_name}'")
                        print(f"[DEBUG_MC_BEDS] Customer ID: {customer_id}")
                        print(f"[DEBUG_MC_BEDS] Product Name: {product_name}")
                        if not event_type_name:
                            print(f"[DEBUG_MC_BEDS] ✗✗✗ EVENT TYPE NAME IS BLANK - This row will be filtered out!")

                
                # DEBUG: Track if target customer has blank event type
                if str(customer_id) == "4a5a2962-bcf8-4a8b-a434-e1868072b0bd":
                    logging.info(f"[DEBUG_GENERATE] Event Type Name: '{event_type_name}'")
                    if not event_type_name:
                        logging.info(f"[DEBUG_GENERATE] ⚠️⚠️⚠️ EVENT TYPE NAME IS BLANK - WILL BE FILTERED OUT ⚠️⚠️⚠️")
                        print("[DEBUG] TARGET CUSTOMER HAS BLANK EVENT TYPE")
                
                # Debug: Check target customer event type
                if str(customer_id) == TARGET_DEBUG_CUSTOMER:
                    logging.info(f"[DEBUG_TARGET] Product Name: {product_name}")
                    logging.info(f"[DEBUG_TARGET] Event Type ID: {event_type_id}")
                    logging.info(f"[DEBUG_TARGET] Event Type Name: '{event_type_name}'")
                    if not event_type_name:
                        logging.info(f"[DEBUG_TARGET] ✗✗✗ BLANK EVENT TYPE - Will be filtered in process_data()")
                        print(f"[DEBUG] Target customer has blank event type")
                
                # Create row
                report_rows.append({
                    'customer ID': customer_id,
                    'Product name': product_name,
                    'event type name': event_type_name
                })
                
            except Exception as e:
                print(f"      ⚠ Error processing obligation {obligation.get('id', 'unknown')}: {str(e)}")
                skipped_count += 1
                continue
        
        # Step 5: Create DataFrame
        if report_rows:
            usage_bt_df = pd.DataFrame(report_rows)
            print(f"      ✓ Generated {len(usage_bt_df)} rows")
            if skipped_count > 0:
                print(f"      ⚠ Skipped {skipped_count} obligations (missing contractId/customerId, non-UNIT billing type, or excluded parent)")
        else:
            print(f"      ⚠ No valid rows generated")
            usage_bt_df = pd.DataFrame(columns=['customer ID', 'Product name', 'event type name'])
        
        # Debug: Final check
        if not target_found_in_obligations:
            logging.info(f"\n[DEBUG_TARGET] ✗✗✗ TARGET CUSTOMER {TARGET_DEBUG_CUSTOMER} NOT FOUND IN OBLIGATIONS")
            logging.info(f"[DEBUG_TARGET] This customer has no obligations matching the date filter")
            print(f"[DEBUG] Target customer NOT found in any obligations")
        else:
            target_in_df = TARGET_DEBUG_CUSTOMER in usage_bt_df['customer ID'].values if not usage_bt_df.empty else False
            if target_in_df:
                logging.info(f"[DEBUG_TARGET] ✓ Target customer successfully added to Usage BT Report")
                print(f"[DEBUG] Target customer in Usage BT Report")
            else:
                logging.info(f"[DEBUG_TARGET] ✗✗✗ Target customer was found but NOT in final Usage BT Report")
                logging.info(f"[DEBUG_TARGET] Likely filtered due to blank event type or other issue")
                print(f"[DEBUG] Target customer found but not in report - check log")
        
        print(f"\n[API] ✓ Usage BT Report generation complete")
        return usage_bt_df
        
    except Exception as e:
        print(f"\n[API] ✗ Error generating Usage BT Report from API: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=['customer ID', 'Product name', 'event type name'])

# ============================================================================
# MAIN PROCESSING LOGIC
# ============================================================================

def process_data(dataframes):
    """
    Main processing function that implements the complete transformation logic.
    Returns tuple of (output_df, unmapped_customers_list)
    """
    print("\n" + "=" * 80)
    print("STEP 2: PROCESSING DATA TRANSFORMATION LOGIC")
    print("=" * 80)
    
    usage_bt = dataframes['usage_bt']
    community_quantity = dataframes['community_quantity']
    business_quantity = dataframes['business_quantity']
    minimum_report = dataframes['minimum_report']
    combo_product_report = dataframes['combo_product_report']
    
    output_rows = []
    unmapped_customers = []  # NEW: Track customers not found in any report
    
    # Calculate last day of previous month
    today = datetime.now()
    first_day_current = datetime(today.year, today.month, 1)
    last_day_previous = first_day_current - timedelta(days=1)
    current_date = last_day_previous.strftime('%Y-%m-%d')
    
    print(f"\nCurrent Date for Output: {current_date}")
    print(f"Total rows to process from Usage BT Report: {len(usage_bt)}")
    
    # DEBUG: Show customer IDs in Usage BT Report
    print(f"\n[DEBUG_USAGE_BT] Customer IDs in Usage BT Report:")
    print(f"  Total rows: {len(usage_bt)}")
    print(f"  Available columns: {list(usage_bt.columns)}")
    
    if len(usage_bt) > 0:
        # Find customer ID column case-insensitively
        customer_id_col = find_column_case_insensitive(usage_bt, 'customer ID')
        product_name_col = find_column_case_insensitive(usage_bt, 'Product name')
        event_type_col = find_column_case_insensitive(usage_bt, 'event type name')
        
        if customer_id_col:
            print(f"  Found customer ID column: '{customer_id_col}'")
            print(f"  Unique customer IDs: {usage_bt[customer_id_col].nunique()}")
            print(f"  Sample customer IDs (first 20): {usage_bt[customer_id_col].head(20).tolist()}")
            # Check for specific customer ID if provided
            target_id = '8f64bfad-fe84-4839-9a9f-037403bdc93a'
            if target_id in usage_bt[customer_id_col].values:
                print(f"  ✓ Target customer ID '{target_id}' FOUND in Usage BT Report")
                matching_rows = usage_bt[usage_bt[customer_id_col] == target_id]
                print(f"  Found {len(matching_rows)} row(s) with this customer ID:")
                for idx, row in matching_rows.iterrows():
                    product_val = row.get(product_name_col, 'N/A') if product_name_col else 'N/A'
                    event_val = row.get(event_type_col, 'N/A') if event_type_col else 'N/A'
                    print(f"    Row {idx}: Product='{product_val}', Event Type='{event_val}'")
            else:
                print(f"  ✗ Target customer ID '{target_id}' NOT FOUND in Usage BT Report")
                print(f"  This explains why minimums are not being applied - the customer ID is not in the source data!")
        else:
            print(f"  ⚠ WARNING: Could not find customer ID column!")
            print(f"  This will cause processing to fail.")
    
    # Find column names case-insensitively (do this once before the loop)
    customer_id_col = find_column_case_insensitive(usage_bt, 'customer ID')
    product_name_col = find_column_case_insensitive(usage_bt, 'Product name')
    event_type_col = find_column_case_insensitive(usage_bt, 'event type name')
    
    # Validate all required columns are found
    if not customer_id_col:
        raise ValueError(f"Could not find 'customer ID' column. Available columns: {list(usage_bt.columns)}")
    if not product_name_col:
        raise ValueError(f"Could not find 'Product name' column. Available columns: {list(usage_bt.columns)}")
    if not event_type_col:
        raise ValueError(f"Could not find 'event type name' column. Available columns: {list(usage_bt.columns)}")
    
    print(f"\n[COLUMN_MAPPING] Using columns:")
    print(f"  Customer ID: '{customer_id_col}'")
    print(f"  Product name: '{product_name_col}'")
    print(f"  Event type name: '{event_type_col}'")
    
    # Debug target customer
    TARGET_DEBUG_CUSTOMER = "0184231f-2f82-4afa-8a38-e4417afed001"
    
    # Iterate through each row in Usage BT Report CSV
    for idx, row in usage_bt.iterrows():
        print(f"\n{'-' * 80}")
        print(f"PROCESSING ROW {idx + 1}/{len(usage_bt)}")
        print(f"{'-' * 80}")
        
        try:
            # STEP 2.1: Extract data from Usage BT Report
            customer_id = row[customer_id_col]
            product_name = row[product_name_col]
            event_type_name = row[event_type_col]
            
            if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
                print(f"\n🔍🔍🔍 DEBUG TARGET CUSTOMER FOUND IN USAGE BT REPORT 🔍🔍🔍")
                print(f"🔍 Row {idx + 1}: customer_id={customer_id}")
                print(f"🔍           product_name={product_name}")
                print(f"🔍           event_type_name={event_type_name}")
            
            # DEBUG: Track target customer through processing
            is_target = str(customer_id) == "4a5a2962-bcf8-4a8b-a434-e1868072b0bd"
            is_debug_target = str(customer_id) == TARGET_DEBUG_CUSTOMER
            
            if is_target:
                logging.info(f"\n{'=' * 80}")
                logging.info(f"[DEBUG_PROCESS] ✓✓✓ TARGET CUSTOMER IN PROCESSING LOOP ✓✓✓")
                logging.info(f"{'=' * 80}")
                print("[DEBUG] TARGET CUSTOMER IN PROCESSING LOOP")
            
            if is_debug_target:
                logging.info(f"\n{'=' * 80}")
                logging.info(f"[DEBUG_TARGET] ✓ TARGET CUSTOMER {TARGET_DEBUG_CUSTOMER} ENTERED PROCESSING")
                logging.info(f"{'=' * 80}")
                print(f"[DEBUG] Target customer {TARGET_DEBUG_CUSTOMER} entered processing loop")
            
            print(f"  [2.1.1] Extracted from Usage BT Report:")
            print(f"          - Customer ID: {customer_id}")
            print(f"          - Product Name: {product_name}")
            print(f"          - Event Type Name: {event_type_name}")
            
            # Validate event_type_name is not blank
            if pd.isna(event_type_name) or not str(event_type_name).strip():
                print(f"          ✗ Event Type Name is blank or missing")
                print(f"          → Skipping this row")
                # DEBUG: Check if this is the target customer ID
                if str(customer_id) == '8f64bfad-fe84-4839-9a9f-037403bdc93a':
                    print(f"          [DEBUG] ⚠ TARGET CUSTOMER ID SKIPPED: Blank event_type_name")
                if is_debug_target:
                    logging.info(f"[DEBUG_TARGET] ✗✗✗ FILTERED OUT: Blank event type name")
                    print(f"[DEBUG] Target customer filtered: blank event type")
                continue
            
            # STEP 2.2: Get report type from Tabs API custom field
            print(f"\n  [2.1.2] Fetching report type from API...")
            
            from api import get_customer_report_type
            report_type = get_customer_report_type(customer_id)
            
            if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
                print(f"🔍 DEBUG TARGET CUSTOMER: ID={customer_id}, report_type={report_type}, product_name={product_name}")
            
            if not report_type:
                print(f"          ⚠ No 'Active Bed Report' custom field found for customer {customer_id}")
                print(f"          → Will try direct lookup in all reports by Tabs Platform ID")
                report_type = 'Direct Lookup'
            else:
                print(f"          ✓ Report type from API: '{report_type}'")
            
            # STEP 2.3: Determine report type and fetch value
            print(f"\n  [2.1.3] Determining report type and fetching values...")
            print(f"          Report Type Value: '{report_type}'")
            
            fetched_value = None
            
            if report_type == 'Direct Lookup':
                # No custom field found - try all reports with Tabs Platform ID
                print(f"          → No custom field, checking all reports with Tabs Platform ID...")
                fetched_value = process_by_community(
                    None,  # No internal_community_id needed
                    product_name, 
                    community_quantity,
                    idx,
                    customer_id=customer_id
                )
            
            elif report_type == 'By Community':
                print(f"          → Processing: 'By Community' logic")
                fetched_value = process_by_community(
                    None,  # No internal_community_id needed - using Tabs Platform ID
                    product_name, 
                    community_quantity,
                    idx,
                    customer_id=customer_id
                )
            
            elif report_type == 'By Bus Unit' or report_type == 'By Business Unit':
                print(f"          → Processing: 'By Business Unit' logic")
                fetched_value = process_by_business_unit(
                    None,  # No internal_community_id needed - using Tabs Platform ID
                    product_name, 
                    business_quantity,
                    idx,
                    customer_id=customer_id
                )
            
            elif report_type == 'Combination Product':
                print(f"          → Processing: 'Combination Product' logic")
                fetched_value = process_combo_product(
                    None,  # No internal_community_id needed - using Tabs Platform ID
                    product_name, 
                    combo_product_report,
                    idx,
                    customer_id=customer_id
                )
            
            else:
                print(f"          ✗ Unknown report type: '{report_type}'")
                print(f"          → Skipping this row")
                continue
            
            if fetched_value is None:
                if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
                    print(f"🔍 DEBUG TARGET CUSTOMER: fetched_value is None, report_type={report_type}, adding to unmapped")
                print(f"          ✗ Could not fetch value from report sheet")
                print(f"          → Skipping this row and tracking as unmapped")
                # Track as unmapped customer
                from api import lookup_customer_name_by_id
                unmapped_customers.append({
                    'customer_id': customer_id,
                    'customer_name': lookup_customer_name_by_id(customer_id),
                    'product_name': product_name,
                    'event_type_name': event_type_name,
                    'report_type': report_type,
                    'reason': 'Not found in bed count reports'
                })
                continue
            
            print(f"          ✓ Fetched Value: {fetched_value}")
            
            # STEP 2.4: Find minimum value from Minimum Report CSV using fuzzy matching
            print(f"\n  [2.1.4] Looking up Minimum Report...")
            
            # Print minimum_report structure for debugging
            print(f"          [MIN_REPORT_DEBUG] Total rows in minimum_report: {len(minimum_report)}")
            print(f"          [MIN_REPORT_DEBUG] Columns in minimum_report: {list(minimum_report.columns)}")
            
            # Find minimum_report columns case-insensitively
            min_customer_id_col = find_column_case_insensitive(minimum_report, 'customer ID')
            min_product_name_col = find_column_case_insensitive(minimum_report, 'Product name')
            min_active_date_col = find_column_case_insensitive(minimum_report, 'Active Date')
            
            if min_active_date_col:
                print(f"          [MIN_REPORT_DEBUG] Found Active Date column: '{min_active_date_col}'")
            else:
                print(f"          [MIN_REPORT_DEBUG] ⚠ Could not find 'Active Date' column in minimum_report")
                print(f"          [MIN_REPORT_DEBUG] Available columns: {list(minimum_report.columns)}")
            
            # Extract keywords from usage product name for matching
            product_keywords = extract_product_keywords(product_name)
            print(f"          → Extracted keywords from '{product_name}': {product_keywords}")
            
            # Get all rows with matching customer_id (with robust string normalization)
            print(f"          [CUSTOMER_ID_FILTER] Searching for customer ID: '{customer_id}' (type: {type(customer_id).__name__})")
            if not min_customer_id_col:
                print(f"          ⚠ WARNING: Could not find 'customer ID' column in minimum_report!")
                print(f"          Available columns: {list(minimum_report.columns)}")
                customer_min_rows = pd.DataFrame()
            else:
                # Normalize customer_id to string and strip whitespace
                customer_id_normalized = str(customer_id).strip().lower()
                print(f"          [CUSTOMER_ID_FILTER] Normalized search ID: '{customer_id_normalized}'")
                
                # Normalize the customer ID column in minimum_report for comparison
                min_report_ids_normalized = minimum_report[min_customer_id_col].astype(str).str.strip().str.lower()
                
                # Debug: Show a sample of IDs from minimum report
                if len(minimum_report) > 0:
                    sample_ids = min_report_ids_normalized.head(3).tolist()
                    print(f"          [CUSTOMER_ID_FILTER] Sample IDs from minimum report: {sample_ids}")
                
                # Perform case-insensitive, whitespace-trimmed comparison
                customer_min_rows = minimum_report[min_report_ids_normalized == customer_id_normalized]
            print(f"          [CUSTOMER_ID_FILTER] Found {len(customer_min_rows)} row(s) matching customer ID")
            
            if customer_min_rows.empty:
                print(f"          ⚠ No rows found for customer ID: {customer_id}")
                min_value = 0.0
                print(f"          → Using default min_value: {min_value}")
            else:
                print(f"          → Found {len(customer_min_rows)} row(s) for customer ID")
                print(f"          → Available products in Minimum Report:")
                for i, min_row in customer_min_rows.iterrows():
                    product_name_val = min_row.get(min_product_name_col, 'N/A') if min_product_name_col else 'N/A'
                    print(f"             • {product_name_val}")
                
                # Collect all fuzzy-matched rows
                matched_rows = []
                print(f"          → Checking each product from Minimum Report for fuzzy match...")
                for i, min_row in customer_min_rows.iterrows():
                    min_product_name = min_row.get(min_product_name_col, '') if min_product_name_col else ''
                    print(f"          → Checking product {i+1}/{len(customer_min_rows)}: '{min_product_name}'")
                    if fuzzy_match_product(product_name, min_product_name, product_keywords):
                        matched_rows.append((i, min_row))
                        print(f"          ✓ Fuzzy match found: '{min_product_name}'")
                    else:
                        print(f"          ✗ No fuzzy match: '{min_product_name}' does not contain all required keywords")
                
                if not matched_rows:
                    print(f"          ⚠ No fuzzy match found for keywords: {product_keywords}")
                    min_value = 0.0
                    print(f"          → Using default min_value: {min_value}")
                else:
                    print(f"          → Found {len(matched_rows)} fuzzy-matched row(s)")
                    
                    # Parse Active Date for each matched row and filter out future dates
                    # Use date only (no time) for comparison
                    # Calculate last day of previous month (same as current_date)
                    today = datetime.now()
                    first_day_current = datetime(today.year, today.month, 1)
                    last_day_previous = first_day_current - timedelta(days=1)
                    current_date_obj = last_day_previous.replace(hour=0, minute=0, second=0, microsecond=0)
                    valid_rows = []
                    
                    print(f"          → Processing Active Dates (current date: {current_date_obj.strftime('%Y-%m-%d')})...")
                    for idx, (row_idx, min_row) in enumerate(matched_rows):
                        # Get Active Date using case-insensitive column name
                        if min_active_date_col:
                            active_date_value = min_row.get(min_active_date_col, None)
                        else:
                            # Fallback to hardcoded name if not found earlier
                            active_date_value = min_row.get('Active Date', None)
                        
                        print(f"             Row {idx + 1}: Raw Active Date value: {active_date_value} (type: {type(active_date_value).__name__})")
                        parsed_date = parse_active_date(active_date_value, current_date_obj)
                        
                        if parsed_date is None:
                            print(f"             Row {idx + 1}: Invalid or missing Active Date - skipping")
                            print(f"             Row {idx + 1}: Could not parse '{active_date_value}' as a date")
                            continue
                        
                        # Normalize parsed_date to date only (no time)
                        if isinstance(parsed_date, datetime):
                            parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        if parsed_date > current_date_obj:
                            print(f"             Row {idx + 1}: Active Date {parsed_date.strftime('%Y-%m-%d')} is in future - filtering out")
                            continue
                        
                        valid_rows.append((row_idx, min_row, parsed_date))
                        print(f"             Row {idx + 1}: Active Date {parsed_date.strftime('%Y-%m-%d')} is valid")
                    
                    if not valid_rows:
                        print(f"          ⚠ All matched rows have invalid or future Active Dates")
                        min_value = 0.0
                        print(f"          → Using default min_value: {min_value}")
                    else:
                        # Select row with latest Active Date
                        selected_row = max(valid_rows, key=lambda x: x[2])  # x[2] is the parsed_date
                        selected_min_row = selected_row[1]
                        selected_date = selected_row[2]
                        
                        print(f"          → Selected row with latest Active Date: {selected_date.strftime('%Y-%m-%d')}")
                        product_name_val = selected_min_row.get(min_product_name_col, 'N/A') if min_product_name_col else 'N/A'
                        print(f"          → Product: '{product_name_val}'")
                        
                        # Debug: Show available columns
                        if hasattr(selected_min_row, 'index'):
                            available_cols = list(selected_min_row.index)
                        elif hasattr(selected_min_row, 'keys'):
                            available_cols = list(selected_min_row.keys())
                        else:
                            available_cols = []
                        print(f"          [COLUMN_DEBUG] Available columns in selected row: {available_cols}")
                        
                        # Find minimum quantity column with flexible matching
                        min_qty_column = find_minimum_quantity_column(selected_min_row)
                        if min_qty_column is None:
                            print(f"          [COLUMN_DEBUG] ⚠ 'minimum quantity' column not found!")
                            print(f"          [COLUMN_DEBUG] Available columns: {available_cols}")
                            print(f"          [VALUE_EXTRACTION] ⚠ Column not found - will use 0")
                            min_value = 0.0
                        else:
                            print(f"          [COLUMN_DEBUG] ✓ Found column: '{min_qty_column}'")
                            
                            # Extract and convert minimum quantity
                            raw_min_value = selected_min_row.get(min_qty_column, None)
                            print(f"          [VALUE_EXTRACTION] Raw '{min_qty_column}' value: {raw_min_value} (type: {type(raw_min_value).__name__})")
                            
                            if raw_min_value is None:
                                print(f"          [VALUE_EXTRACTION] ⚠ '{min_qty_column}' is None - will use 0")
                                min_value = 0.0
                            else:
                                min_value = safe_convert_to_numeric(raw_min_value)
                                print(f"          [VALUE_EXTRACTION] After safe_convert_to_numeric: {min_value} (type: {type(min_value).__name__})")
                                if pd.isna(min_value) or min_value is None:
                                    print(f"          [VALUE_EXTRACTION] ⚠ Converted value is None/NaN - will use 0")
                                    min_value = 0.0
                        
                        print(f"          ✓ Minimum Value Found: {min_value}")
            
            # STEP 2.5: Calculate final value
            print(f"\n  [2.1.5] Calculating final value...")
            print(f"          Formula: final_value = max(fetched_value, min_value)")
            print(f"          [MAX_CALC] Before conversion - fetched_value: {fetched_value} (type: {type(fetched_value).__name__}), min_value: {min_value} (type: {type(min_value).__name__})")
            
            # Convert fetched_value to numeric (min_value is already numeric from earlier conversion)
            fetched_value = safe_convert_to_numeric(fetched_value)
            print(f"          [MAX_CALC] After conversion - fetched_value: {fetched_value} (type: {type(fetched_value).__name__}), min_value: {min_value} (type: {type(min_value).__name__})")
            
            # Validate both values are valid numbers
            if pd.isna(fetched_value) or fetched_value is None:
                print(f"          [MAX_CALC] ⚠ fetched_value is None/NaN, using 0")
                fetched_value = 0.0
            if pd.isna(min_value) or min_value is None:
                print(f"          [MAX_CALC] ⚠ min_value is None/NaN, using 0")
                min_value = 0.0
            
            # Ensure both are floats for consistency
            fetched_value = float(fetched_value)
            min_value = float(min_value)
            
            print(f"          [MAX_CALC] Final values - fetched_value: {fetched_value}, min_value: {min_value}")
            print(f"          [MAX_CALC] Calculating max({fetched_value}, {min_value})")
            
            final_value = max(fetched_value, min_value)
            print(f"          ✓ Final Value: {final_value}")
            print(f"          [MAX_CALC] Result: {final_value} (min_value was {'applied' if final_value == min_value and min_value > 0 else 'not applied' if final_value == fetched_value else 'part of calculation'})")
            
            # STEP 2.6: Prepare output row
            print(f"\n  [2.1.6] Preparing output row...")
            output_row = {
                'customer_id': customer_id,
                'event_type_name': event_type_name,
                'datetime': current_date,
                'value': final_value,
                'differentiator': ''
            }
            
            print(f"          Output Row:")
            for key, value in output_row.items():
                print(f"            - {key}: {value}")
            
            output_rows.append(output_row)
            print(f"          ✓ Row added to output")
            
        except Exception as e:
            if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
                print(f"🔍 DEBUG TARGET CUSTOMER: Exception caught! {str(e)}")
                import traceback
                traceback.print_exc()
            print(f"  ✗ ERROR processing row {idx}: {str(e)}")
            print(f"  → Skipping this row")
            continue
    
    print(f"\n{'=' * 80}")
    print(f"PROCESSING COMPLETE: {len(output_rows)} rows processed successfully")
    print(f"UNMAPPED CUSTOMERS: {len(unmapped_customers)} customers could not be mapped")
    print(f"{'=' * 80}")
    
    return pd.DataFrame(output_rows), unmapped_customers

# ============================================================================
# BY COMMUNITY PROCESSING
# ============================================================================

def process_by_community(internal_community_id, product_name, community_quantity, row_idx, customer_id=None):
    """
    Process BY COMMUNITY report type.
    First tries direct lookup by Tabs Platform ID, then falls back to Internal Community ID.
    """
    print(f"\n          [BY_COMMUNITY_LOGIC] Starting...")
    
    if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
        print(f"🔍 DEBUG TARGET CUSTOMER: Entered process_by_community function")
        print(f"🔍   - customer_id: {customer_id}")
        print(f"🔍   - product_name: {product_name}")
        print(f"🔍   - community_quantity shape: {community_quantity.shape}")
    
    community_row = None
    
    # NEW: Try direct lookup by Tabs Platform ID first
    if customer_id:
        tabs_platform_id_col = find_column_case_insensitive(community_quantity, 'Tabs Platform ID')
        if tabs_platform_id_col:
            print(f"          [BY_COMMUNITY_LOGIC] Attempting direct lookup by Tabs Platform ID...")
            direct_rows = community_quantity[
                community_quantity[tabs_platform_id_col] == customer_id
            ]
            
            if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
                print(f"🔍 DEBUG TARGET CUSTOMER in By Community lookup: rows_found={len(direct_rows)}, product_name={product_name}")
                if not direct_rows.empty:
                    print(f"🔍 DEBUG: Sample row data: {direct_rows.iloc[0].to_dict()}")
            
            if not direct_rows.empty:
                print(f"          [BY_COMMUNITY_LOGIC] ✓ Found by Tabs Platform ID (direct lookup)")
                if len(direct_rows) > 1:
                    print(f"          [BY_COMMUNITY_LOGIC] ⚠ Found {len(direct_rows)} rows, using first")
                community_row = direct_rows.iloc[0]
    
    # FALLBACK: Use existing Internal Community ID lookup
    if community_row is None:
        print(f"          [BY_COMMUNITY_LOGIC] Falling back to Internal Community ID lookup...")
        # Find row with matching Internal Community ID
        community_rows = community_quantity[
            community_quantity['Community ID'] == internal_community_id
        ]
        
        if community_rows.empty:
            print(f"          [BY_COMMUNITY_LOGIC] ✗ No row found with Community ID: {internal_community_id}")
            return None
        
        if len(community_rows) > 1:
            print(f"          [BY_COMMUNITY_LOGIC] ⚠ Found {len(community_rows)} rows with Community ID {internal_community_id}")
            print(f"          [BY_COMMUNITY_LOGIC] → Using first row")
        
        community_row = community_rows.iloc[0]
        print(f"          [BY_COMMUNITY_LOGIC] ✓ Found matching row by Internal Community ID")
    
    # Determine which column to fetch based on product name
    print(f"          [BY_COMMUNITY_LOGIC] Checking product name: '{product_name}'")
    
    if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
        print(f"🔍 DEBUG TARGET CUSTOMER: About to check product matching")
        print(f"🔍   - community_row found: {community_row is not None}")
        print(f"🔍   - checking for 'Respond' in: {product_name}")
    
    if check_product_contains(product_name, ['Respond']):
        print(f"          [BY_COMMUNITY_LOGIC] ✓ 'Respond' found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Respond Beds'")
        fetched_value = community_row['Respond Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    elif check_product_contains(product_name, ['Aware']):
        if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
            print(f"🔍 DEBUG TARGET CUSTOMER: 'Aware' matched!")
        print(f"          [BY_COMMUNITY_LOGIC] ✓ 'Aware' found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Aware - Virtual or Wellness Checkins Active Beds'")
        fetched_value = community_row['Aware - Virtual or Wellness Checkins Active Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    elif check_product_contains(product_name, get_addon_variants()):
        if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
            print(f"🔍 DEBUG TARGET CUSTOMER: Addon variant matched!")
            print(f"🔍   - addon_variants checked: {get_addon_variants()}")
        print(f"          [BY_COMMUNITY_LOGIC] ✓ Addon variant found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds'")
        fetched_value = community_row['Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    else:
        print(f"          [BY_COMMUNITY_LOGIC] ✗ No matching product keyword found")
        print(f"          [BY_COMMUNITY_LOGIC] Checked for: Respond, Aware, Addon variants")
        
        if str(customer_id) == '9e660ece-132a-47ec-bb89-df1161c5395e':
            print(f"🔍 DEBUG TARGET CUSTOMER: No product match in By Community - returning None")
            print(f"🔍   - Product name: '{product_name}'")
            print(f"🔍   - Addon variants list: {get_addon_variants()}")
        
        return None

# ============================================================================
# BY BUSINESS UNIT PROCESSING
# ============================================================================

def process_by_business_unit(internal_community_id, product_name, business_quantity, row_idx, customer_id=None):
    """
    Process BY BUS UNIT report type.
    First tries direct lookup by Tabs Platform ID, then falls back to Internal Community ID.
    Handles filtering by Business Unit Type (Memory Care, Assisted Living, Skilled Nursing).
    Sums values across multiple rows if the same community ID and business unit type appear multiple times.
    """
    print(f"\n          [BY_BUS_UNIT_LOGIC] Starting...")
    
    bus_rows = None
    
    # NEW: Try direct lookup by Tabs Platform ID first
    if customer_id:
        tabs_platform_id_col = find_column_case_insensitive(business_quantity, 'Tabs Platform ID')
        if tabs_platform_id_col:
            print(f"          [BY_BUS_UNIT_LOGIC] Attempting direct lookup by Tabs Platform ID...")
            direct_rows = business_quantity[
                business_quantity[tabs_platform_id_col] == customer_id
            ]
            if not direct_rows.empty:
                print(f"          [BY_BUS_UNIT_LOGIC] ✓ Found {len(direct_rows)} row(s) by Tabs Platform ID (direct lookup)")
                bus_rows = direct_rows
    
    # FALLBACK: Use existing Internal Community ID lookup
    if bus_rows is None or bus_rows.empty:
        print(f"          [BY_BUS_UNIT_LOGIC] Falling back to Internal Community ID lookup...")
        # Find rows with matching Internal Community ID
        bus_rows = business_quantity[
            business_quantity['Community ID'] == internal_community_id
        ]
        
        if bus_rows.empty:
            print(f"          [BY_BUS_UNIT_LOGIC] ✗ No rows found with Community ID: {internal_community_id}")
            return None
        
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ Found {len(bus_rows)} row(s) with Community ID {internal_community_id}")
    
    # Determine Business Unit Type based on product name
    business_unit_type = None
    
    if 'MC' in product_name.upper():
        business_unit_type = 'Memory Care'
        print(f"          [BY_BUS_UNIT_LOGIC] 'MC' found → Business Unit Type: Memory Care")
    elif 'AL' in product_name.upper():
        business_unit_type = 'Assisted Living'
        print(f"          [BY_BUS_UNIT_LOGIC] 'AL' found → Business Unit Type: Assisted Living")
    elif 'SNF' in product_name.upper():
        business_unit_type = 'Skilled Nursing'
        print(f"          [BY_BUS_UNIT_LOGIC] 'SNF' found → Business Unit Type: Skilled Nursing")
    else:
        print(f"          [BY_BUS_UNIT_LOGIC] ⚠ No business unit type identifier found (MC/AL/SNF)")
        print(f"          [BY_BUS_UNIT_LOGIC] → Using all available rows")
        business_unit_type = None
    
    # Filter by business unit type if identified
    if business_unit_type:
        filtered_rows = bus_rows[bus_rows['Business Unit Type'] == business_unit_type]
        if filtered_rows.empty:
            print(f"          [BY_BUS_UNIT_LOGIC] ✗ No row with Business Unit Type: {business_unit_type}")
            print(f"          [BY_BUS_UNIT_LOGIC] Available types: {bus_rows['Business Unit Type'].unique().tolist()}")
            return None
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ Found {len(filtered_rows)} row(s) with Business Unit Type: {business_unit_type}")
    else:
        filtered_rows = bus_rows
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ Using all {len(filtered_rows)} available row(s)")
    
    # Determine which column to fetch based on product name
    print(f"          [BY_BUS_UNIT_LOGIC] Checking product name: '{product_name}'")
    
    if check_product_contains(product_name, ['Respond']):
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ 'Respond' found in product name")
        print(f"          [BY_BUS_UNIT_LOGIC] → Using column: 'Respond Beds'")
        column_name = 'Respond Beds'
    elif check_product_contains(product_name, ['Aware']):
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ 'Aware' found in product name")
        print(f"          [BY_BUS_UNIT_LOGIC] → Using column: 'Aware - Virtual or Wellness Checkins Active Beds'")
        column_name = 'Aware - Virtual or Wellness Checkins Active Beds'
    elif check_product_contains(product_name, get_addon_variants()):
        print(f"          [BY_BUS_UNIT_LOGIC] ✓ Addon variant found in product name")
        print(f"          [BY_BUS_UNIT_LOGIC] → Using column: 'Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds'")
        column_name = 'Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds'
    else:
        print(f"          [BY_BUS_UNIT_LOGIC] ✗ No matching product keyword found")
        print(f"          [BY_BUS_UNIT_LOGIC] Checked for: Respond, Aware, Addon variants")
        return None
    
    # Sum values across all matching rows
    total_value = 0.0
    for idx, row in filtered_rows.iterrows():
        row_value = safe_convert_to_numeric(row[column_name])
        total_value += row_value
        print(f"          [BY_BUS_UNIT_LOGIC] Row {idx}: {row_value} (running total: {total_value})")
    
    print(f"          [BY_BUS_UNIT_LOGIC] Summed {len(filtered_rows)} row(s) → Total Value: {total_value}")
    return total_value

# ============================================================================
# COMBINATION PRODUCT PROCESSING
# ============================================================================
# COMBINATION PRODUCT PROCESSING
# ============================================================================

def process_combo_product(internal_community_id, product_name, combo_product_report, row_idx, customer_id=None):
    """
    Process Combination Product report type.
    First tries direct lookup by Tabs Platform ID, then falls back to Internal Community ID.
    Handles custom logic based on product name patterns (Respond/Aware + MC/AL/SNF).
    """
    print(f"\n          [COMBO_PRODUCT_LOGIC] Starting...")
    
    # DEBUG: Log available columns
    logging.info(f"          [COMBO_PRODUCT_LOGIC] Combo Product Report Columns: {list(combo_product_report.columns)}")
    logging.info(f"          [COMBO_PRODUCT_LOGIC] Looking for Community ID: {internal_community_id}")
    logging.info(f"          [COMBO_PRODUCT_LOGIC] Product Name: {product_name}")
    print(f"          [COMBO_PRODUCT_LOGIC] Looking for Community ID: {internal_community_id}")
    
    combo_row = None
    
    # NEW: Try direct lookup by Tabs Platform ID first
    if customer_id:
        tabs_platform_id_col = find_column_case_insensitive(combo_product_report, 'Tabs Platform ID')
        if tabs_platform_id_col:
            print(f"          [COMBO_PRODUCT_LOGIC] Attempting direct lookup by Tabs Platform ID...")
            logging.info(f"          [COMBO_PRODUCT_LOGIC] Attempting direct lookup by Tabs Platform ID: {customer_id}")
            direct_rows = combo_product_report[
                combo_product_report[tabs_platform_id_col] == customer_id
            ]
            if not direct_rows.empty:
                print(f"          [COMBO_PRODUCT_LOGIC] ✓ Found by Tabs Platform ID (direct lookup)")
                logging.info(f"          [COMBO_PRODUCT_LOGIC] ✓ Found by Tabs Platform ID (direct lookup)")
                if len(direct_rows) > 1:
                    print(f"          [COMBO_PRODUCT_LOGIC] ⚠ Found {len(direct_rows)} rows, using first")
                combo_row = direct_rows.iloc[0]
    
    # FALLBACK: Use existing Internal Community ID lookup
    if combo_row is None:
        print(f"          [COMBO_PRODUCT_LOGIC] Falling back to Internal Community ID lookup...")
        logging.info(f"          [COMBO_PRODUCT_LOGIC] Falling back to Internal Community ID lookup...")
        
        # Find Community ID column case-insensitively
        community_id_col = find_column_case_insensitive(combo_product_report, 'Community ID')
        
        if not community_id_col:
            logging.info(f"          [COMBO_PRODUCT_LOGIC] ✗ Could not find 'Community ID' column")
            logging.info(f"          [COMBO_PRODUCT_LOGIC] Available columns: {list(combo_product_report.columns)}")
            print(f"          [COMBO_PRODUCT_LOGIC] ✗ Could not find 'Community ID' column")
            return None
        
        logging.info(f"          [COMBO_PRODUCT_LOGIC] Using column: '{community_id_col}'")
        
        # Find row with matching Community ID
        combo_rows = combo_product_report[
            combo_product_report[community_id_col] == internal_community_id
        ]
        
        # DEBUG: Log first 10 unique Community IDs for comparison
        unique_ids = combo_product_report[community_id_col].unique()[:10].tolist()
        logging.info(f"          [COMBO_PRODUCT_LOGIC] Available Community IDs in report (first 10): {unique_ids}")
        
        if combo_rows.empty:
            logging.info(f"          [COMBO_PRODUCT_LOGIC] ✗ No row found with Community ID: {internal_community_id}")
            print(f"          [COMBO_PRODUCT_LOGIC] ✗ No row found with Community ID: {internal_community_id}")
            return None
        
        if len(combo_rows) > 1:
            print(f"          [COMBO_PRODUCT_LOGIC] ⚠ Found {len(combo_rows)} rows with Community ID {internal_community_id}")
            print(f"          [COMBO_PRODUCT_LOGIC] → Using first row")
        
        combo_row = combo_rows.iloc[0]
        print(f"          [COMBO_PRODUCT_LOGIC] ✓ Found matching row by Internal Community ID")
    
    # Extract product type and business unit from product name
    product_upper = product_name.upper()
    has_respond = 'RESPOND' in product_upper
    has_aware = 'AWARE' in product_upper
    has_mc = 'MC' in product_upper
    has_al = 'AL' in product_upper
    has_snf = 'SNF' in product_upper
    
    print(f"          [COMBO_PRODUCT_LOGIC] Product name analysis:")
    print(f"            - Has 'Respond': {has_respond}")
    print(f"            - Has 'Aware': {has_aware}")
    print(f"            - Has 'MC': {has_mc}")
    print(f"            - Has 'AL': {has_al}")
    print(f"            - Has 'SNF': {has_snf}")
    
    # Get column values using case-insensitive lookup
    respond_aware_col = find_column_case_insensitive(combo_product_report, 'Respond With Aware Beds')
    respond_only_col = find_column_case_insensitive(combo_product_report, 'Respond Only Beds')
    aware_only_col = find_column_case_insensitive(combo_product_report, 'Aware Only Beds')
    
    respond_with_aware = safe_convert_to_numeric(combo_row.get(respond_aware_col, 0)) if respond_aware_col else 0
    respond_only = safe_convert_to_numeric(combo_row.get(respond_only_col, 0)) if respond_only_col else 0
    aware_only = safe_convert_to_numeric(combo_row.get(aware_only_col, 0)) if aware_only_col else 0
    
    logging.info(f"          [COMBO_PRODUCT_LOGIC] Column mappings:")
    logging.info(f"            - Respond With Aware Beds -> '{respond_aware_col}' = {respond_with_aware}")
    logging.info(f"            - Respond Only Beds -> '{respond_only_col}' = {respond_only}")
    logging.info(f"            - Aware Only Beds -> '{aware_only_col}' = {aware_only}")
    
    print(f"          [COMBO_PRODUCT_LOGIC] Column values:")
    print(f"            - Respond With Aware Beds: {respond_with_aware}")
    print(f"            - Respond Only Beds: {respond_only}")
    print(f"            - Aware Only Beds: {aware_only}")
    
    # Calculate fetched_value based on 6 cases
    fetched_value = None
    
    if has_respond and has_mc:
        # Case a: Respond MC -> Respond With Aware Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Respond MC")
        fetched_value = respond_with_aware
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {fetched_value}")
    
    elif has_respond and has_al:
        # Case b: Respond AL -> Respond With Aware Beds + Respond Only Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Respond AL")
        fetched_value = respond_with_aware + respond_only
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {respond_with_aware} + {respond_only} = {fetched_value}")
    
    elif has_respond and has_snf:
        # Case c: Respond SNF -> Respond With Aware Beds + Respond Only Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Respond SNF")
        fetched_value = respond_with_aware + respond_only
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {respond_with_aware} + {respond_only} = {fetched_value}")
    
    elif has_aware and has_mc:
        # Case d: Aware MC -> Respond With Aware Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Aware MC")
        fetched_value = respond_with_aware
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {fetched_value}")
    
    elif has_aware and has_al:
        # Case e: Aware AL -> Respond With Aware Beds + Aware Only Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Aware AL")
        fetched_value = respond_with_aware + aware_only
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {respond_with_aware} + {aware_only} = {fetched_value}")
    
    elif has_aware and has_snf:
        # Case f: Aware SNF -> Respond With Aware Beds + Aware Only Beds
        print(f"          [COMBO_PRODUCT_LOGIC] → Case: Aware SNF")
        fetched_value = respond_with_aware + aware_only
        print(f"          [COMBO_PRODUCT_LOGIC] Value: {respond_with_aware} + {aware_only} = {fetched_value}")
    
    else:
        print(f"          [COMBO_PRODUCT_LOGIC] ✗ No matching product pattern found")
        print(f"          [COMBO_PRODUCT_LOGIC] Expected patterns: Respond/Aware + MC/AL/SNF")
        return None
    
    return fetched_value

# ============================================================================
# DEDUPLICATION
# ============================================================================

def deduplicate_output(output_df):
    """
    Remove duplicate rows based on customer_id, event_type_name, datetime, and value.
    Only rows with ALL four fields identical are considered duplicates.
    """
    print("\n" + "=" * 80)
    print("STEP 2.5: DEDUPLICATION CHECK")
    print("=" * 80)
    
    # Debug target customer
    TARGET_DEBUG_CUSTOMER = "0184231f-2f82-4afa-8a38-e4417afed001"
    target_in_output = TARGET_DEBUG_CUSTOMER in output_df['customer_id'].values if not output_df.empty else False
    
    if target_in_output:
        logging.info(f"\n[DEBUG_TARGET] ✓ Target customer {TARGET_DEBUG_CUSTOMER} is in output BEFORE deduplication")
        print(f"[DEBUG] Target customer in output before deduplication")
    else:
        logging.info(f"\n[DEBUG_TARGET] ✗✗✗ Target customer {TARGET_DEBUG_CUSTOMER} NOT in output")
        logging.info(f"[DEBUG_TARGET] Customer was filtered out during processing")
        print(f"[DEBUG] Target customer NOT in final output - check log")
    
    original_count = len(output_df)
    print(f"\n  Original row count: {original_count}")
    
    # Check for duplicates
    duplicate_mask = output_df.duplicated(
        subset=['customer_id', 'event_type_name', 'datetime', 'value'],
        keep=False  # Mark all duplicates (not just subsequent ones)
    )
    
    duplicate_count = duplicate_mask.sum()
    
    if duplicate_count > 0:
        print(f"  ⚠ Found {duplicate_count} duplicate rows (including all copies)")
        print(f"\n  Duplicate row details:")
        
        # Show which rows are duplicates
        duplicates = output_df[duplicate_mask].sort_values(
            by=['customer_id', 'event_type_name', 'datetime', 'value']
        )
        
        print(duplicates.to_string(index=False))
        
        # Remove duplicates, keeping first occurrence
        deduplicated_df = output_df.drop_duplicates(
            subset=['customer_id', 'event_type_name', 'datetime', 'value'],
            keep='first'
        )
        
        removed_count = original_count - len(deduplicated_df)
        print(f"\n  ✓ Removed {removed_count} duplicate row(s), kept first occurrence")
        print(f"  Final row count: {len(deduplicated_df)}")
        
        return deduplicated_df
    else:
        print(f"  ✓ No duplicates found - all rows are unique")
        return output_df

# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def save_output(output_df, output_path='output.csv'):
    """
    Save the output DataFrame to a CSV file.
    """
    print("\n" + "=" * 80)
    print("STEP 3: SAVING OUTPUT CSV")
    print("=" * 80)
    
    try:
        output_df.to_csv(output_path, index=False)
        print(f"\n  ✓ Output saved successfully to: {output_path}")
        print(f"  Total rows in output: {len(output_df)}")
        print(f"\n  Output file preview (first 5 rows):")
        print(output_df.head().to_string(index=False))
        return True
    except Exception as e:
        print(f"\n  ✗ ERROR saving output: {str(e)}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function that orchestrates the entire process.
    """
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "DATA TRANSFORMATION SCRIPT".center(78) + "*")
    print("*" + "Usage BT Report Processing - WITH FUZZY MATCHING & DEDUPLICATION".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    
    try:
        # Step 0: Configure file paths
        file_paths = get_file_paths()
        
        # Step 1: Load CSV files
        dataframes = load_csv_files(file_paths)
        
        # Step 2: Process data
        output_df, unmapped_customers = process_data(dataframes)
        
        # Display unmapped customers summary
        if unmapped_customers:
            print(f"\n⚠️  UNMAPPED CUSTOMERS SUMMARY:")
            print(f"   {len(unmapped_customers)} customer(s) could not be mapped")
            for uc in unmapped_customers[:10]:  # Show first 10
                print(f"   - Customer: {uc['customer_id']}, Product: {uc['product_name']}, Reason: {uc['reason']}")
            if len(unmapped_customers) > 10:
                print(f"   ... and {len(unmapped_customers) - 10} more")
        
        # Step 2.5: Deduplicate output
        output_df = deduplicate_output(output_df)
        
        # Step 3: Save output
        save_output(output_df, 'output.csv')
        
        print("\n" + "*" * 80)
        print("*" + " " * 78 + "*")
        print("*" + "SCRIPT EXECUTION COMPLETED SUCCESSFULLY".center(78) + "*")
        print("*" + " " * 78 + "*")
        print("*" * 80)
        
    except Exception as e:
        print("\n" + "*" * 80)
        print("*" + " " * 78 + "*")
        print("*" + "SCRIPT EXECUTION FAILED".center(78) + "*")
        print("*" + " " * 78 + "*")
        print("*" * 80)
        print(f"\nError: {str(e)}")
        raise

if __name__ == "__main__":
    main()
