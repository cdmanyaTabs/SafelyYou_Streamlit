import pandas as pd
from datetime import datetime
import os
import numpy as np
import re

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
        'customer_mapping': 'Customer_Mapping.csv',
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
        
        print("\n[1.2] Loading Customer Mapping CSV...")
        dataframes['customer_mapping'] = pd.read_csv(file_paths['customer_mapping'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['customer_mapping'].shape}")
        print(f"      Columns: {list(dataframes['customer_mapping'].columns)}")
        
        print("\n[1.3] Loading Community Quantity Data Report CSV...")
        dataframes['community_quantity'] = pd.read_csv(file_paths['community_quantity'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['community_quantity'].shape}")
        print(f"      Columns: {list(dataframes['community_quantity'].columns)}")
        
        print("\n[1.4] Loading Business Quantity Data Report CSV...")
        dataframes['business_quantity'] = pd.read_csv(file_paths['business_quantity'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['business_quantity'].shape}")
        print(f"      Columns: {list(dataframes['business_quantity'].columns)}")
        
        print("\n[1.5] Loading Minimum Report CSV...")
        dataframes['minimum_report'] = pd.read_csv(file_paths['minimum_report'])
        print(f"      ✓ Loaded successfully with shape: {dataframes['minimum_report'].shape}")
        print(f"      Columns: {list(dataframes['minimum_report'].columns)}")
        
        print("\n[1.6] Loading Combo Product Report CSV...")
        dataframes['combo_product_report'] = pd.read_csv(file_paths['combo_product_report'], delimiter='\t')
        print(f"      ✓ Loaded successfully with shape: {dataframes['combo_product_report'].shape}")
        print(f"      Columns: {list(dataframes['combo_product_report'].columns)}")
        
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

def extract_product_keywords(product_name):
    """
    Extract key identifying keywords from product name.
    Returns list of keywords: [product_type, business_unit (if present)]
    
    Product types: RESPOND, AWARE, ADDON
    Business units: MC, AL, SNF
    """
    # Normalize: uppercase and replace special chars with spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(product_name).upper())
    normalized = ' '.join(normalized.split())  # Remove extra spaces
    
    keywords = []
    
    # Check for product type
    if 'RESPOND' in normalized:
        keywords.append('RESPOND')
    elif 'AWARE' in normalized:
        keywords.append('AWARE')
    elif any(variant in normalized for variant in ['ADDON', 'ADD ON']):
        keywords.append('ADDON')
    
    # Check for business unit type
    # Use word boundaries to avoid matching "MC" in "MCDONALDS" etc.
    words = normalized.split()
    if 'MC' in words:
        keywords.append('MC')
    elif 'AL' in words:
        keywords.append('AL')
    elif 'SNF' in words:
        keywords.append('SNF')
    
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
    # Normalize minimum product name
    normalized_min = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(minimum_product_name).upper())
    normalized_min = ' '.join(normalized_min.split())
    
    # Check if all keywords are present
    for keyword in extracted_keywords:
        # Special handling for ADDON variants
        if keyword == 'ADDON':
            if not any(variant in normalized_min for variant in ['ADDON', 'ADD ON']):
                return False
        else:
            # For MC, AL, SNF - check as whole words
            if keyword in ['MC', 'AL', 'SNF']:
                words = normalized_min.split()
                if keyword not in words:
                    return False
            else:
                # For RESPOND, AWARE - check substring
                if keyword not in normalized_min:
                    return False
    
    return True

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
    
    try:
        # Try parsing with pandas to_datetime (handles multiple formats)
        parsed_date = pd.to_datetime(date_str, errors='coerce', infer_datetime_format=True)
        
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
    
    if not event_types_df.empty:
        for _, row in event_types_df.iterrows():
            event_type_id = row.get("id")
            event_type_name = row.get("name")
            if event_type_id and event_type_name:
                event_type_lookup[event_type_id] = event_type_name
    
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
        from api import get_all_obligations, get_all_contracts
        from api import get_event_ids
        
        # Step 1: Fetch obligations
        print("\n[API] Fetching obligations from Tabs API...")
        obligations_response = get_all_obligations()
        obligations_data = obligations_response.get("payload", {}).get("data", [])
        print(f"      ✓ Retrieved {len(obligations_data)} obligations")
        
        # Step 2: Fetch contracts
        print("\n[API] Fetching contracts from Tabs API...")
        contracts_response = get_all_contracts()
        contract_lookup = build_contract_lookup(contracts_response)
        print(f"      ✓ Built contract lookup with {len(contract_lookup)} contracts")
        
        # Step 3: Fetch event types
        print("\n[API] Fetching event types from Tabs API...")
        event_types_df = get_event_ids()
        event_type_lookup = build_event_type_lookup(event_types_df)
        print(f"      ✓ Built event type lookup with {len(event_type_lookup)} event types")
        
        # Step 4: Process obligations and build report rows
        print("\n[API] Processing obligations to build Usage BT Report...")
        report_rows = []
        skipped_count = 0
        
        for obligation in obligations_data:
            try:
                # Extract contractId
                contract_id = obligation.get("contractId")
                if not contract_id:
                    skipped_count += 1
                    continue
                
                # Lookup customerId from contract
                customer_id = contract_lookup.get(contract_id)
                if not customer_id:
                    skipped_count += 1
                    continue
                
                # Extract Product name from billingSchedule
                billing_schedule = obligation.get("billingSchedule", {})
                product_name = billing_schedule.get("name", "")
                
                # Extract eventTypeId and lookup event type name
                event_type_id = billing_schedule.get("eventTypeId")
                event_type_name = ""
                if event_type_id:
                    event_type_name = event_type_lookup.get(event_type_id, "")
                
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
                print(f"      ⚠ Skipped {skipped_count} obligations (missing contractId or customerId)")
        else:
            print(f"      ⚠ No valid rows generated")
            usage_bt_df = pd.DataFrame(columns=['customer ID', 'Product name', 'event type name'])
        
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
    """
    print("\n" + "=" * 80)
    print("STEP 2: PROCESSING DATA TRANSFORMATION LOGIC")
    print("=" * 80)
    
    usage_bt = dataframes['usage_bt']
    customer_mapping = dataframes['customer_mapping']
    community_quantity = dataframes['community_quantity']
    business_quantity = dataframes['business_quantity']
    minimum_report = dataframes['minimum_report']
    combo_product_report = dataframes['combo_product_report']
    
    output_rows = []
    # Set current date once at the start in YYYY-MM-DD format (date only, no time)
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\nCurrent Date for Output: {current_date}")
    print(f"Total rows to process from Usage BT Report: {len(usage_bt)}")
    
    # Iterate through each row in Usage BT Report CSV
    for idx, row in usage_bt.iterrows():
        print(f"\n{'-' * 80}")
        print(f"PROCESSING ROW {idx + 1}/{len(usage_bt)}")
        print(f"{'-' * 80}")
        
        try:
            # STEP 2.1: Extract data from Usage BT Report
            customer_id = row['customer ID']
            product_name = row['Product name']
            event_type_name = row['event type name']
            
            print(f"  [2.1.1] Extracted from Usage BT Report:")
            print(f"          - Customer ID: {customer_id}")
            print(f"          - Product Name: {product_name}")
            print(f"          - Event Type Name: {event_type_name}")
            
            # STEP 2.2: Find mapping in Customer Mapping CSV
            print(f"\n  [2.1.2] Looking up Customer Mapping...")
            mapping_rows = customer_mapping[customer_mapping['Tabs customer ID'] == customer_id]
            
            if mapping_rows.empty:
                print(f"          ✗ No mapping found for customer ID: {customer_id}")
                print(f"          → Skipping this row")
                continue
            
            # Handle multiple mapping rows
            if len(mapping_rows) > 1:
                print(f"          ⚠ Found {len(mapping_rows)} mapping entries for customer ID {customer_id}")
                print(f"          → Using first entry")
            
            mapping_row = mapping_rows.iloc[0]
            internal_community_id = mapping_row['Internal Community ID']
            report_type = mapping_row['Report']
            
            print(f"          ✓ Mapping found:")
            print(f"            - Internal Community ID: {internal_community_id}")
            print(f"            - Report Type: {report_type}")
            
            # STEP 2.3: Determine report type and fetch value
            print(f"\n  [2.1.3] Determining report type and fetching values...")
            print(f"          Report Type Value: '{report_type}'")
            
            fetched_value = None
            
            if report_type == 'By Community':
                print(f"          → Processing: 'By Community' logic")
                fetched_value = process_by_community(
                    internal_community_id, 
                    product_name, 
                    community_quantity,
                    idx
                )
            
            elif report_type == 'By Bus Unit':
                print(f"          → Processing: 'By Bus Unit' logic")
                fetched_value = process_by_business_unit(
                    internal_community_id, 
                    product_name, 
                    business_quantity,
                    idx
                )
            
            elif report_type == 'Combination Product':
                print(f"          → Processing: 'Combination Product' logic")
                fetched_value = process_combo_product(
                    internal_community_id, 
                    product_name, 
                    combo_product_report,
                    idx
                )
            
            else:
                print(f"          ✗ Unknown report type: '{report_type}'")
                print(f"          → Skipping this row")
                continue
            
            if fetched_value is None:
                print(f"          ✗ Could not fetch value from report sheet")
                print(f"          → Skipping this row")
                continue
            
            print(f"          ✓ Fetched Value: {fetched_value}")
            
            # STEP 2.4: Find minimum value from Minimum Report CSV using fuzzy matching
            print(f"\n  [2.1.4] Looking up Minimum Report...")
            
            # Extract keywords from usage product name for matching
            product_keywords = extract_product_keywords(product_name)
            print(f"          → Extracted keywords from '{product_name}': {product_keywords}")
            
            # Get all rows with matching customer_id
            customer_min_rows = minimum_report[minimum_report['customer ID'] == customer_id]
            
            if customer_min_rows.empty:
                print(f"          ⚠ No rows found for customer ID: {customer_id}")
                min_value = 0
                print(f"          → Using default min_value: {min_value}")
            else:
                print(f"          → Found {len(customer_min_rows)} row(s) for customer ID")
                print(f"          → Available products in Minimum Report:")
                for i, min_row in customer_min_rows.iterrows():
                    print(f"             • {min_row['Product name']}")
                
                # Collect all fuzzy-matched rows
                matched_rows = []
                for i, min_row in customer_min_rows.iterrows():
                    min_product_name = min_row['Product name']
                    if fuzzy_match_product(product_name, min_product_name, product_keywords):
                        matched_rows.append((i, min_row))
                        print(f"          ✓ Fuzzy match found: '{min_product_name}'")
                
                if not matched_rows:
                    print(f"          ⚠ No fuzzy match found for keywords: {product_keywords}")
                    min_value = 0
                    print(f"          → Using default min_value: {min_value}")
                else:
                    print(f"          → Found {len(matched_rows)} fuzzy-matched row(s)")
                    
                    # Parse Active Date for each matched row and filter out future dates
                    # Use date only (no time) for comparison
                    current_date_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    valid_rows = []
                    
                    print(f"          → Processing Active Dates (current date: {current_date_obj.strftime('%Y-%m-%d')})...")
                    for idx, (row_idx, min_row) in enumerate(matched_rows):
                        active_date_value = min_row.get('Active Date', None)
                        parsed_date = parse_active_date(active_date_value, current_date_obj)
                        
                        if parsed_date is None:
                            print(f"             Row {idx + 1}: Invalid or missing Active Date - skipping")
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
                        min_value = 0
                        print(f"          → Using default min_value: {min_value}")
                    else:
                        # Select row with latest Active Date
                        selected_row = max(valid_rows, key=lambda x: x[2])  # x[2] is the parsed_date
                        selected_min_row = selected_row[1]
                        selected_date = selected_row[2]
                        
                        print(f"          → Selected row with latest Active Date: {selected_date.strftime('%Y-%m-%d')}")
                        print(f"          → Product: '{selected_min_row['Product name']}'")
                        
                        min_value = selected_min_row['minimum quantity']
                        min_value = safe_convert_to_numeric(min_value)
                        print(f"          ✓ Minimum Value Found: {min_value}")
            
            # STEP 2.5: Calculate final value
            print(f"\n  [2.1.5] Calculating final value...")
            print(f"          Formula: final_value = max(fetched_value, min_value)")
            print(f"                  = max({fetched_value}, {min_value})")
            
            # Convert both values to numeric before max()
            fetched_value = safe_convert_to_numeric(fetched_value)
            min_value = safe_convert_to_numeric(min_value)
            
            final_value = max(fetched_value, min_value)
            print(f"          ✓ Final Value: {final_value}")
            
            # STEP 2.6: Prepare output row
            print(f"\n  [2.1.6] Preparing output row...")
            output_row = {
                'customer_id': customer_id,
                'event_type_name': event_type_name,
                'datetime': current_date,
                'value': final_value,
                'differentiator': 0
            }
            
            print(f"          Output Row:")
            for key, value in output_row.items():
                print(f"            - {key}: {value}")
            
            output_rows.append(output_row)
            print(f"          ✓ Row added to output")
            
        except Exception as e:
            print(f"  ✗ ERROR processing row {idx}: {str(e)}")
            print(f"  → Skipping this row")
            continue
    
    print(f"\n{'=' * 80}")
    print(f"PROCESSING COMPLETE: {len(output_rows)} rows processed successfully")
    print(f"{'=' * 80}")
    
    return pd.DataFrame(output_rows)

# ============================================================================
# BY COMMUNITY PROCESSING
# ============================================================================

def process_by_community(internal_community_id, product_name, community_quantity, row_idx):
    """
    Process BY COMMUNITY report type.
    """
    print(f"\n          [BY_COMMUNITY_LOGIC] Starting...")
    
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
    print(f"          [BY_COMMUNITY_LOGIC] ✓ Found matching row")
    
    # Determine which column to fetch based on product name
    print(f"          [BY_COMMUNITY_LOGIC] Checking product name: '{product_name}'")
    
    if check_product_contains(product_name, ['Respond']):
        print(f"          [BY_COMMUNITY_LOGIC] ✓ 'Respond' found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Respond Beds'")
        fetched_value = community_row['Respond Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    elif check_product_contains(product_name, ['Aware']):
        print(f"          [BY_COMMUNITY_LOGIC] ✓ 'Aware' found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Aware - Virtual or Wellness Checkins Active Beds'")
        fetched_value = community_row['Aware - Virtual or Wellness Checkins Active Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    elif check_product_contains(product_name, get_addon_variants()):
        print(f"          [BY_COMMUNITY_LOGIC] ✓ Addon variant found in product name")
        print(f"          [BY_COMMUNITY_LOGIC] → Using column: 'Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds'")
        fetched_value = community_row['Addon - Aware Secure Virtual Checkins + Clarity Presence Tracking Beds']
        fetched_value = safe_convert_to_numeric(fetched_value)
        print(f"          [BY_COMMUNITY_LOGIC] Value: {fetched_value}")
        return fetched_value
    
    else:
        print(f"          [BY_COMMUNITY_LOGIC] ✗ No matching product keyword found")
        print(f"          [BY_COMMUNITY_LOGIC] Checked for: Respond, Aware, Addon variants")
        return None

# ============================================================================
# BY BUSINESS UNIT PROCESSING
# ============================================================================

def process_by_business_unit(internal_community_id, product_name, business_quantity, row_idx):
    """
    Process BY BUS UNIT report type.
    Handles filtering by Business Unit Type (Memory Care, Assisted Living, Skilled Nursing).
    Sums values across multiple rows if the same community ID and business unit type appear multiple times.
    """
    print(f"\n          [BY_BUS_UNIT_LOGIC] Starting...")
    
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

def process_combo_product(internal_community_id, product_name, combo_product_report, row_idx):
    """
    Process Combination Product report type.
    Handles custom logic based on product name patterns (Respond/Aware + MC/AL/SNF).
    """
    print(f"\n          [COMBO_PRODUCT_LOGIC] Starting...")
    
    # Find row with matching Community ID
    combo_rows = combo_product_report[
        combo_product_report['Community ID'] == internal_community_id
    ]
    
    if combo_rows.empty:
        print(f"          [COMBO_PRODUCT_LOGIC] ✗ No row found with Community ID: {internal_community_id}")
        return None
    
    if len(combo_rows) > 1:
        print(f"          [COMBO_PRODUCT_LOGIC] ⚠ Found {len(combo_rows)} rows with Community ID {internal_community_id}")
        print(f"          [COMBO_PRODUCT_LOGIC] → Using first row")
    
    combo_row = combo_rows.iloc[0]
    print(f"          [COMBO_PRODUCT_LOGIC] ✓ Found matching row")
    
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
    
    # Get column values
    respond_with_aware = safe_convert_to_numeric(combo_row.get('Respond With Aware Beds', 0))
    respond_only = safe_convert_to_numeric(combo_row.get('Respond Only Beds', 0))
    aware_only = safe_convert_to_numeric(combo_row.get('Aware Only Beds', 0))
    
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
        output_df = process_data(dataframes)
        
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
