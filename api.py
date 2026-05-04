import pandas as pd
import streamlit as st
import requests
import io
import json
import logging
from datetime import datetime, timedelta

# Configure logging for debug output (console only)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

def get_customer_custom_field():
    url = f"https://integrators.prod.api.tabsplatform.com/v3/customers/custom-fields"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def get_all_billing_terms():
    """
    Fetch all billing terms from contracts that match the filters:
    - billingType == "UNIT"
    - billingStartDate <= last day of previous month
    - billingEndDate >= last day of previous month
    
    Returns data in the same format as the old obligations endpoint for compatibility.
    """
    # Calculate last day of previous month
    today = datetime.now()
    first_day_current = datetime(today.year, today.month, 1)
    last_day_previous = first_day_current - timedelta(days=1)
    date_filter_string = last_day_previous.strftime('%Y-%m-%d')
    
    # DEBUG: Log filter
    logging.info("\n[DEBUG_API] get_all_billing_terms() called")
    logging.info(f"[DEBUG_API] Date filter: billingStartDate <= {date_filter_string}, billingEndDate >= {date_filter_string}")
    logging.info(f"[DEBUG_API] Billing type filter: UNIT only")
    
    print(f"[DEBUG_API] Fetching all contracts...")
    
    # Step 1: Fetch all contracts
    contracts_response = get_all_contracts()
    contracts_data = contracts_response.get("payload", {}).get("data", [])
    print(f"[DEBUG_API] Retrieved {len(contracts_data)} contracts")
    
    # Step 2: Loop through contracts and fetch billing terms
    all_billing_data = []
    skipped_contracts = 0
    processed_contracts = 0
    
    for idx, contract in enumerate(contracts_data, 1):
        contract_id = contract.get("id")
        customer_id = contract.get("customerId")
        
        # Skip contracts without customer ID
        if not customer_id:
            skipped_contracts += 1
            continue
        
        # Progress logging every 100 contracts
        if idx % 100 == 0:
            print(f"[DEBUG_API] Processing contract {idx}/{len(contracts_data)}...")
        
        # Fetch billing terms for this contract
        billing_terms_response = get_billing_terms_for_contract(contract_id)
        if not billing_terms_response:
            skipped_contracts += 1
            continue
        
        billing_terms = billing_terms_response.get("payload", {}).get("data", [])
        
        # Step 3: Filter and transform billing terms
        for billing_term in billing_terms:
            # Filter 1: Only UNIT billing type
            billing_type = billing_term.get("billingType")
            if billing_type != "UNIT":
                continue
            
            # Filter 2: Date filtering
            billing_start_date_str = billing_term.get("billingStartDate", "")
            billing_end_date_str = billing_term.get("billingEndDate", "")
            
            try:
                # Parse dates (handle both date and datetime strings)
                if billing_start_date_str:
                    billing_start_date = datetime.strptime(billing_start_date_str.split('T')[0], '%Y-%m-%d')
                else:
                    continue
                
                if billing_end_date_str:
                    billing_end_date = datetime.strptime(billing_end_date_str.split('T')[0], '%Y-%m-%d')
                else:
                    continue
                
                # Apply date filter: billingStartDate <= last_day_previous AND billingEndDate >= last_day_previous
                if billing_start_date <= last_day_previous and billing_end_date >= last_day_previous:
                    # Transform to match old obligations format
                    transformed_data = {
                        "contractId": contract_id,
                        "customerId": customer_id,
                        "billingSchedule": {
                            "name": billing_term.get("name", ""),
                            "billingType": billing_type,
                            "eventTypeId": billing_term.get("eventTypeId"),
                            "startDate": billing_start_date_str,
                            "endDate": billing_end_date_str
                        }
                    }
                    all_billing_data.append(transformed_data)
                    processed_contracts += 1
            except Exception as e:
                logging.info(f"[DEBUG_API] Error parsing dates for contract {contract_id}: {str(e)}")
                continue
    
    # Create response in same format as old obligations endpoint
    result = {
        "payload": {
            "data": all_billing_data
        }
    }
    
    # DEBUG: Log results
    logging.info(f"[DEBUG_API] Total billing terms fetched: {len(all_billing_data)}")
    logging.info(f"[DEBUG_API] Processed contracts: {processed_contracts}")
    logging.info(f"[DEBUG_API] Skipped contracts: {skipped_contracts}")
    
    print(f"[DEBUG_API] Fetched {len(all_billing_data)} billing terms (UNIT type, date filtered)")
    print(f"[DEBUG_API] Processed {processed_contracts} contracts, skipped {skipped_contracts}")
    
    return result
# Example response:
# {
#   "payload": {
#     "data": [
#       {
#         "id": "ab8ca3c8-6c2d-4a1a-885f-d98246d6b617",
#         "serviceStartDate": "2021-12-02T00:00:00.000Z",
#         "serviceEndDate": "2024-12-01T00:00:00.000Z",
#         "categoryId": "f73348b5-8524-47f0-89e5-f4882b341de4",
#         "contractId": "429915ac-cfbd-43fa-a90e-4a47083cffb1",
#         "revenueSchedule": {
#           "categoryId": "f73348b5-8524-47f0-89e5-f4882b341de4",
#           "recognizedRevenue": [
#             {
#               "timeframe": "2024-05",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-06",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-07",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-08",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-09",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-10",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-11",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2024-12",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-01",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-02",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-03",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-04",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-05",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-06",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-07",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-08",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-09",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-10",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-11",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2025-12",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-01",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-02",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-03",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-04",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-05",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-06",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-07",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-08",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-09",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-10",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-11",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2026-12",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2027-01",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2027-02",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2027-03",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2027-04",
#               "total": 0,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2027-05",
#               "total": 0,
#               "booksClosed": false
#             }
#           ]
#         },
#         "billingSchedule": {
#           "name": "SafelyYou-Insight",
#           "description": "",
#           "startDate": "2021-12-02T00:00:00.000Z",
#           "endDate": "2024-12-01T00:00:00.000Z",
#           "duration": 36,
#           "isArrears": false,
#           "isRecurring": true,
#           "interval": "MONTH",
#           "intervalFrequency": 1,
#           "netPaymentTerms": 30,
#           "quantity": 24,
#           "invoiceType": "INVOICE",
#           "classId": null,
#           "eventTypeId": null,
#           "itemId": null,
#           "billingType": "FLAT",
#           "pricingType": "SIMPLE",
#           "pricing": [
#             {
#               "tier": 0,
#               "amount": 3000,
#               "amountType": "TOTAL_INVOICE",
#               "tierMinimum": 0
#             }
#           ]
#         }
#       },
#       {
#         "id": "5e0e5342-3b48-4b5a-865d-687319e34234",
#         "serviceStartDate": "2022-09-28T00:00:00.000Z",
#         "serviceEndDate": "2024-09-27T00:00:00.000Z",
#         "categoryId": "f73348b5-8524-47f0-89e5-f4882b341de4",
#         "contractId": "32e6d2bb-08e9-4ad1-9d88-c15583149264",
#         "revenueSchedule": {
#           "categoryId": "f73348b5-8524-47f0-89e5-f4882b341de4",
#           "recognizedRevenue": [
#             {
#               "timeframe": "2022-09",
#               "total": 16,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2022-10",
#               "total": 160,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2022-11",
#               "total": 160,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2022-12",
#               "total": 160,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2023-01",
#               "total": 160,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2023-02",
#               "total": 160,
#               "booksClosed": false
#             },
#             {
#               "timeframe": "2023-03",
#               "total": 160,
#               "booksClosed": false
#             },
#             {

def get_all_customers():
    url = f"https://integrators.prod.api.tabsplatform.com/v3/customers?limit=10000"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.get(url+"1", headers=headers)
    success = response.json().get("success")
    if success:
        payload = response.json().get("payload",{})
        totalItems = payload.get("totalItems",0)
        if totalItems > 0:
            response = requests.get(url+str(totalItems), headers=headers)
            if response.json().get("success"):
                payload = response.json().get("payload",{})
                data = payload.get("data",[])
                return data
    return []

def get_excluded_customer_ids():
    """
    Get set of customer IDs to exclude based on parentCustomerId.
    Excludes customers where parentCustomerId matches specific IDs.
    
    Returns:
        set: Set of customer IDs to exclude from processing
    """
    EXCLUDED_PARENT_IDS = {
        "6f5c57f9-3dd5-4669-8de9-cfd4a7459021",
        "6d94324f-91a9-424b-9649-913aa765aa7c"
    }
    
    customers = get_all_customers()
    
    excluded_ids = set()
    for customer in customers:
        parent_id = customer.get("parentCustomerId")
        if parent_id in EXCLUDED_PARENT_IDS:
            excluded_ids.add(customer.get("id"))
    
    return excluded_ids

    # Example response:
    #  "payload": {
    # "data": [
    #   {
    #     "id": "a8e03b2b-8b20-4eb7-bdac-da1c1447dab2",
    #     "name": "Commit Consume Customer No. 3",
    #     "parentCustomerId": null,
    #     "secondaryBillingContacts": [],
    #     "externalIds": [],
    #     "defaultCurrency": "USD",
    #     "lastUpdatedAt": "2024-08-15T19:27:52.828Z",
       # "customFields": [
        #   {
        #     "id": "3ecee77e-eba1-4142-acc2-42290b1958b5",
        #     "manufacturerCustomFieldId": "6ddd8eff-818d-4462-a369-3912576b3b84",
        #     "customFieldName": "Tenant ID",
        #     "customFieldValue": "449"
        #   }
        # ]    #   },
    #   {
    #     "id": "a22deb49-03d1-4490-9907-da2fe883d8cd",
    #     "name": "Commit Consume Customer No. 4",
    #     "parentCustomerId": null,
    #     "secondaryBillingContacts": [],
    #     "externalIds": [],
    #     "defaultCurrency": "USD",
    #     "lastUpdatedAt": "2024-08-15T19:27:34.659Z",
        # "customFields": [
        #   {
        #     "id": "3ecee77e-eba1-4142-acc2-42290b1958b5",
        #     "manufacturerCustomFieldId": "6ddd8eff-818d-4462-a369-3912576b3b84",
        #     "customFieldName": "Tenant ID",
        #     "customFieldValue": "449"
        #   }
        # ]
    #   },

def get_all_contracts():
    """
    Fetch all contracts from Tabs API.
    Only retrieves contracts with status="PROCESSED".
    
    Returns:
        dict: API response with contracts data
    """
    url = f"https://integrators.prod.api.tabsplatform.com/v3/contracts?limit=10000&filter=status:eq:PROCESSED"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.get(url, headers=headers)
    result = response.json()
    
    # Debug: Check if specific contract is in the response
    TARGET_CONTRACT_ID = "5f8bb451-587a-41a1-add3-d9b5c9208326"
    contracts_data = result.get("payload", {}).get("data", [])
    contract_ids = [c.get("id") for c in contracts_data]
    
    print(f"[DEBUG_CONTRACT] Total contracts fetched: {len(contracts_data)}")
    if TARGET_CONTRACT_ID in contract_ids:
        print(f"[DEBUG_CONTRACT] ✓ Target contract {TARGET_CONTRACT_ID} FOUND in contracts")
    else:
        print(f"[DEBUG_CONTRACT] ✗ Target contract {TARGET_CONTRACT_ID} NOT FOUND in contracts")
        print(f"[DEBUG_CONTRACT] Sample contract IDs (first 10): {contract_ids[:10]}")
    
    return result

def get_billing_terms_for_contract(contract_id):
    """
    Fetch billing terms for a specific contract from Tabs API.
    
    Args:
        contract_id: The contract ID to fetch billing terms for
        
    Returns:
        dict: API response with billing terms data, or None if request fails
    """
    url = f"https://integrators.prod.api.tabsplatform.com/v3/contracts/{contract_id}/billing-terms"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[DEBUG_BILLING_TERMS] Failed to fetch billing terms for contract {contract_id}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"[DEBUG_BILLING_TERMS] Error fetching billing terms for contract {contract_id}: {str(e)}")
        return None

    # Example response:
#     {
#   "payload": {
#     "data": [
#       {
#         "id": "ac5a7dbc-f930-4afd-b2b6-d18eaafeaeb5",
#         "fileName": "001. Change Order_Belmont Village La Jolla MC Expansion_07.29.2025.pdf",
#         "name": "001. Change Order_Belmont Village La Jolla MC Expansion_07.29.2025",
#         "status": "PROCESSED",
#         "customerId": "38a733cf-aff2-4263-ba8a-118261fe3faf",
#         "closeDate": null,
#         "customerName": "Belmont Village:Belmont Village - La Jolla",
#         "createdAt": "2025-10-22T01:06:44.642Z",
#         "lastUpdatedAt": "2025-10-22T01:06:54.602Z",
#         "externalIds": [],
#         "source": "UPLOAD"
#       },
#       {
#         "id": "ecad9b36-b259-4efc-a3fb-2502e4f0dd98",
#         "fileName": "001. Change Order_Claiborne The Avaline at River Oaks (AL)_10.15.2025.pdf",
#         "name": "001. Change Order_Claiborne The Avaline at River Oaks (AL)_10.15.2025",
#         "status": "NEW",
#         "customerId": null,
#         "closeDate": null,
#         "customerName": "",
#         "createdAt": "2025-11-18T22:24:36.060Z",
#         "lastUpdatedAt": "2025-11-18T22:24:36.060Z",
#         "externalIds": [],
#         "source": "UPLOAD"
#       },
      


def get_event_ids():
    url = "https://integrators.prod.api.tabsplatform.com/v3/events/types?limit=1000"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json().get("payload",{}).get("data",[]))
 
#    # Example response:
#    {
#   "payload": {
#     "data": [
#       {
#         "id": "0000802f-5b90-4610-8434-99ac8dae5497",
#         "name": "GCP Interconnect - L"
#       },
#       {
#         "id": "00d41157-2098-4831-9043-1ca39a97f719",
#         "name": "PAN - BYOL - M"
#       },
#       {
#         "id": "012b7a24-3828-4c48-ab30-2a0ea3cd3602",
#         "name": "FortiGate - BYOL - M"
#       }]}}    

def get_integration_items():
    url = "https://integrators.prod.api.tabsplatform.com/v3/items?limit=1000"
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json().get("payload",{}).get("data",[]))
    # Example response:
#     {
#   "payload": {
#     "data": [
#       {
#         "id": "3b96a3da-480e-4d22-a524-52c3a14b3037",
#         "name": "Additional Alkira Datastore - 100G",
#         "externalIds": [
#           {
#             "type": "NETSUITE",
#             "id": "110"
#           }
#         ]
#       },
#       {
#         "id": "eabe1261-76aa-492c-bbf9-ee0cf3153b04",
#         "name": "Akamai Prolexic - 2L",
#         "externalIds": [
#           {
#             "type": "NETSUITE",
#             "id": "1920"
#           }
#         ]
#       },
#       ]}}

def find_contracts(customer_id, contract_name):
    contracts = st.session_state["all_contracts"]
    matching_contracts = [
        contract for contract in contracts
        if contract["customerId"] == customer_id and contract["name"] == contract_name
    ]
    need_to_create = not matching_contracts  # True if no matches found

    return matching_contracts, need_to_create

def lookup_customer_id_by_name(customer_name):
    """
    Lookup customer_id from customer name.
    
    Args:
        customer_name: Customer name to search for
    
    Returns:
        str: Customer ID if found, None otherwise
    """
    # Cache customers in session state for performance
    if 'all_customers_cache' not in st.session_state:
        print("  [lookup_customer] Fetching all customers from API...")
        customers = get_all_customers()
        st.session_state['all_customers_cache'] = customers
        print(f"  [lookup_customer] Cached {len(customers)} customers")
    else:
        customers = st.session_state['all_customers_cache']
    
    # Search for matching customer name (case-insensitive)
    customer_name_lower = str(customer_name).strip().lower()
    for customer in customers:
        customer_db_name = customer.get("name", "").strip().lower()
        if customer_db_name == customer_name_lower:
            return customer.get("id")
    
    return None

def lookup_customer_name_by_id(customer_id):
    """
    Lookup customer name from customer ID.
    Uses cached customer list for performance.
    
    Args:
        customer_id: Customer ID (UUID)
    
    Returns:
        str: Customer name if found, empty string otherwise
    """
    if 'all_customers_cache' not in st.session_state:
        customers = get_all_customers()
        st.session_state['all_customers_cache'] = customers
    else:
        customers = st.session_state['all_customers_cache']
    
    for customer in customers:
        if customer.get("id") == customer_id:
            return customer.get("name", "")
    
    return ""

def get_customer_report_type(customer_id):
    """
    Fetch customer details from Tabs API and extract Active Bed Report type from custom fields.
    Uses caching to minimize API calls.
    
    Args:
        customer_id: Customer ID (UUID)
    
    Returns:
        str: Report type from "Active Bed Report" custom field, or None if not found
    """
    # Cache customer report types in session state
    if 'customer_report_types_cache' not in st.session_state:
        st.session_state['customer_report_types_cache'] = {}
    
    # Check cache first
    if customer_id in st.session_state['customer_report_types_cache']:
        return st.session_state['customer_report_types_cache'][customer_id]
    
    # Fetch from API
    try:
        url = f"https://integrators.prod.api.tabsplatform.com/v3/customers/{customer_id}"
        headers = {"Authorization": st.session_state['tabs_api_key']}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            custom_fields = data.get('payload', {}).get('customFields', [])
            
            # Look for "Active Bed Report" custom field
            for field in custom_fields:
                if field.get('customFieldName') == 'Active Bed Report':
                    report_type = field.get('customFieldValue')
                    # Cache the result
                    st.session_state['customer_report_types_cache'][customer_id] = report_type
                    print(f"  [get_customer_report_type] Customer {customer_id}: Report type = '{report_type}'")
                    return report_type
            
            # Custom field not found - cache as None
            print(f"  [get_customer_report_type] Customer {customer_id}: No 'Active Bed Report' custom field found")
            st.session_state['customer_report_types_cache'][customer_id] = None
            return None
        else:
            print(f"  [get_customer_report_type] API error for customer {customer_id}: Status {response.status_code}")
            # Don't cache errors, return None to allow retry
            return None
    
    except Exception as e:
        print(f"  [get_customer_report_type] Exception fetching customer {customer_id}: {str(e)}")
        # Don't cache errors
        return None

def lookup_or_create_contract(customer_id, contract_name):
    """
    Lookup existing contract or create a new one.
    
    Args:
        customer_id: Customer ID
        contract_name: Contract name
    
    Returns:
        str: Contract ID
    """
    # Cache contracts in session state for performance
    if 'all_contracts_cache' not in st.session_state:
        print("  [lookup_contract] Fetching all contracts from API...")
        contracts_response = get_all_contracts()
        contracts_data = contracts_response.get("payload", {}).get("data", [])
        st.session_state['all_contracts_cache'] = contracts_data
        print(f"  [lookup_contract] Cached {len(contracts_data)} contracts")
    else:
        contracts_data = st.session_state['all_contracts_cache']
    
    # Search for existing contract
    contract_name_lower = str(contract_name).strip().lower()
    for contract in contracts_data:
        if (contract.get("customerId") == customer_id and 
            str(contract.get("name", "")).strip().lower() == contract_name_lower):
            return contract.get("id")
    
    # Contract not found, create it
    print(f"  [lookup_contract] Contract '{contract_name}' not found, creating new contract...")
    result = create_contract(customer_id, contract_name)
    if result:
        contract_id, _ = result
        # Add new contract to cache
        new_contract = {"id": contract_id, "customerId": customer_id, "name": contract_name}
        st.session_state['all_contracts_cache'].append(new_contract)
        return contract_id
    
    return None

def lookup_item_id_by_name(item_name):
    """
    Lookup item_id from item name using /v3/items API.
    
    Args:
        item_name: Item name to search for
    
    Returns:
        str: Item ID if found, None otherwise
    """
    # Cache items in session state for performance
    if 'all_items_cache' not in st.session_state:
        print("  [lookup_item] Fetching all items from API...")
        items_df = get_integration_items()
        st.session_state['all_items_cache'] = items_df
        print(f"  [lookup_item] Cached {len(items_df)} items")
    else:
        items_df = st.session_state['all_items_cache']
    
    if items_df.empty:
        return None
    
    # Search for matching item name (case-insensitive)
    item_name_lower = str(item_name).strip().lower()
    for _, item in items_df.iterrows():
        item_db_name = str(item.get("name", "")).strip().lower()
        if item_db_name == item_name_lower:
            return item.get("id")
    
    return None


def create_contract(customer_id, contract_name):
    url = f"/v3/contracts"
    create_contract_url = f"https://integrators.prod.api.tabsplatform.com{url}"
    payload = {
            "name": contract_name,
            "customerId": customer_id,
            "shouldProcess": False
    }
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}"
    }
    response = requests.post(create_contract_url, headers=headers, json=payload)
    if response.status_code == 201 or response.status_code == 200:
        print(f"✓ create_contract API call successful (HTTP {response.status_code}) for customer {customer_id}")
        if hasattr(response, 'json'):
            response_data = response.json()
            full_payload = response_data.get("payload", {})
            contract_id = full_payload.get("id")
            if not contract_id:
                print(f"✗ create_contract: No contract_id in response for customer {customer_id}")
                ret = None
            else:
                actionpayload = {
                    "action": "MARK_AS_PROCESSED"
                }
                action_response = requests.post(f"https://integrators.prod.api.tabsplatform.com/v3/contracts/{contract_id}/actions", json = actionpayload, headers=headers)
                if action_response.status_code == 200 or action_response.status_code == 201:
                    print(f"✓ create_contract: Contract {contract_id} marked as processed for customer {customer_id}")
                else:
                    print(f"⚠ create_contract: Failed to mark contract {contract_id} as processed (HTTP {action_response.status_code})")
                ret = contract_id, full_payload
        else:
            print(f"✗ create_contract: Invalid response format for customer {customer_id}")
            ret = None
    else:
        print(f"✗ create_contract API call failed (HTTP {response.status_code}) for customer {customer_id}")
        try:
            error_data = response.json()
            error_msg = error_data.get('message', error_data.get('error', 'Unknown error'))
            print(f"  Error details: {error_msg}")
        except:
            print(f"  Error details: {response.text if hasattr(response, 'text') else 'No error details available'}")
        ret = None
    return ret

    
# ============================================================================
# OLD IMPLEMENTATION - COMMENTED OUT
# ============================================================================
# def push_bt(csv_file_data, merchant_name='alkira'):
#     """
#     Push CSV file data to bulk-create-billing-schedules endpoint as multipart/form-data.
#     
#     Args:
#         csv_file_data: Tuple (filename, file_data, content_type) or file-like object for CSV upload
#         merchant_name: Merchant name for the endpoint (default: 'alkira')
#         
#     Returns:
#         Response object from the API
#     """
#     #prep the url
#     url = f"https://integrators.prod.api.tabsplatform.com/v16/secrets/merchant/{merchant_name}/bulk-create-billing-schedules"
# 
#     #prep the header
#     headers = {
#         "Authorization": f"{st.session_state['tabs_api_key']}"
#     }
# 
#     # Prepare files for multipart/form-data upload
#     # csv_file_data should be a tuple of (filename, file_data, content_type) or file-like object
#     if isinstance(csv_file_data, tuple):
#         files = {'file': csv_file_data}
#     else:
#         # If it's a file-like object, wrap it with a filename
#         files = {'file': ('billing_schedules.csv', csv_file_data, 'text/csv')}
#     
#     # Send CSV file as multipart/form-data
#     response = requests.post(url, headers=headers, files=files)
#     
#     # Print status of push_bt API call
#     if response.status_code == 201:
#         print(f"✓ push_bt API call successful (HTTP {response.status_code})")
#         try:
#             response_data = response.json()
#             # Debug: Print the full response structure
#             print(f"  Full API response: {response_data}")
#             
#             # Check if billingTermIds is nested under payload or data
#             billing_term_ids = response_data.get('billingTermIds', [])
#             if not billing_term_ids and 'payload' in response_data:
#                 payload = response_data.get('payload', {})
#                 billing_term_ids = payload.get('billingTermIds', [])
#             if not billing_term_ids and 'data' in response_data:
#                 data = response_data.get('data', {})
#                 billing_term_ids = data.get('billingTermIds', [])
#             
#             if billing_term_ids:
#                 print(f"  Created {len(billing_term_ids)} billing term(s)")
#             else:
#                 print(f"  Warning: No billingTermIds in response")
#                 print(f"  Response keys: {list(response_data.keys())}")
#         except Exception as e:
#             print(f"  Warning: Could not parse response JSON: {str(e)}")
#             print(f"  Response text: {response.text[:500] if hasattr(response, 'text') else 'N/A'}")
#     else:
#         print(f"✗ push_bt API call failed (HTTP {response.status_code})")
#         try:
#             error_data = response.json()
#             error_msg = error_data.get('message', error_data.get('error', 'Unknown error'))
#             print(f"  Error details: {error_msg}")
#         except:
#             print(f"  Error details: {response.text if hasattr(response, 'text') else 'No error details available'}")
#     
#     return response

def validate_bt_customers(csv_file_data):
    """
    Validate customer names in billing terms CSV without creating any obligations.
    This allows users to see which customers cannot be found before pushing BT.
    
    Args:
        csv_file_data: Tuple (filename, file_data, content_type) or file-like object for CSV upload
        
    Returns:
        dict: Validation results with structure:
            {
                'success': bool,
                'total_rows': int,
                'found_customers': [{'row': int, 'customer_name': str, 'customer_id': str}, ...],
                'unfound_customers': [{'row': int, 'customer_name': str}, ...],
                'found_count': int,
                'unfound_count': int,
                'errors': [str, ...]  # Parse errors or other issues
            }
    """
    # Parse CSV data to DataFrame
    try:
        if isinstance(csv_file_data, tuple):
            # Extract file data from tuple (filename, file_data, content_type)
            csv_string = csv_file_data[1]
            if isinstance(csv_string, bytes):
                csv_string = csv_string.decode('utf-8')
        else:
            # If it's a file-like object, read it
            csv_string = csv_file_data.read()
            if isinstance(csv_string, bytes):
                csv_string = csv_string.decode('utf-8')
        
        # Convert CSV string to DataFrame (tab-delimited)
        # Try tab-delimited first, fall back to comma if that results in only 1 column
        csv_buffer = io.StringIO(csv_string)
        df = pd.read_csv(csv_buffer, delimiter='\t')
        
        # Check if parsing worked (if only 1 column, probably wrong delimiter)
        if len(df.columns) == 1:
            print(f"⚠ validate_bt_customers: Tab delimiter resulted in 1 column, trying comma delimiter")
            csv_buffer = io.StringIO(csv_string)
            df = pd.read_csv(csv_buffer, delimiter=',')
        
        print(f"✓ validate_bt_customers: Parsed CSV with {len(df)} rows")
        print(f"  Columns found: {list(df.columns)}")
        
    except Exception as e:
        print(f"✗ validate_bt_customers: Failed to parse CSV data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            'success': False,
            'total_rows': 0,
            'found_customers': [],
            'unfound_customers': [],
            'found_count': 0,
            'unfound_count': 0,
            'errors': [f"Failed to parse CSV: {str(e)}"]
        }
    
    # Initialize result tracking
    found_customers = []
    unfound_customers = []
    errors = []
    
    # Process each row to validate customer names
    for idx, row in df.iterrows():
        try:
            # Extract customer name
            customer_name = row.get('customer name', '')
            if not customer_name or pd.isna(customer_name):
                error_msg = f"Row {idx + 1}: Missing customer name"
                print(f"✗ validate_bt_customers: {error_msg}")
                unfound_customers.append({
                    'row': idx + 1,
                    'customer_name': '(missing)'
                })
                continue
            
            # Lookup customer ID
            customer_id = lookup_customer_id_by_name(customer_name)
            if customer_id:
                print(f"✓ validate_bt_customers: Row {idx + 1}: Found customer '{customer_name}' (ID: {customer_id})")
                found_customers.append({
                    'row': idx + 1,
                    'customer_name': customer_name,
                    'customer_id': customer_id
                })
            else:
                print(f"✗ validate_bt_customers: Row {idx + 1}: Customer '{customer_name}' not found")
                unfound_customers.append({
                    'row': idx + 1,
                    'customer_name': customer_name
                })
                
        except Exception as e:
            error_msg = f"Row {idx + 1}: {str(e)}"
            print(f"✗ validate_bt_customers: Error processing row {idx + 1}: {str(e)}")
            errors.append(error_msg)
    
    # Build result summary
    found_count = len(found_customers)
    unfound_count = len(unfound_customers)
    total_rows = len(df)
    
    print(f"✓ validate_bt_customers: Validation complete - {found_count} found, {unfound_count} not found out of {total_rows} rows")
    
    return {
        'success': True,
        'total_rows': total_rows,
        'found_customers': found_customers,
        'unfound_customers': unfound_customers,
        'found_count': found_count,
        'unfound_count': unfound_count,
        'errors': errors
    }


def push_bt(csv_file_data, merchant_name='safelyyou', progress_callback=None):
    """
    Push billing terms to Tabs API using the new v3/contracts/{id}/obligations endpoint.
    Parses CSV data and creates individual obligations for each row.
    
    Args:
        csv_file_data: Tuple (filename, file_data, content_type) or file-like object for CSV upload
        merchant_name: Merchant name (kept for backward compatibility, not used in new API)
        progress_callback: Optional callback function(current, total, customer_name, status, error_msg)
        
    Returns:
        Response-like object compatible with old implementation
    """
    # Parse CSV data to DataFrame
    try:
        if isinstance(csv_file_data, tuple):
            # Extract file data from tuple (filename, file_data, content_type)
            csv_string = csv_file_data[1]
            if isinstance(csv_string, bytes):
                csv_string = csv_string.decode('utf-8')
        else:
            # If it's a file-like object, read it
            csv_string = csv_file_data.read()
            if isinstance(csv_string, bytes):
                csv_string = csv_string.decode('utf-8')
        
        # Convert CSV string to DataFrame (tab-delimited)
        # Try tab-delimited first, fall back to comma if that results in only 1 column
        csv_buffer = io.StringIO(csv_string)
        df = pd.read_csv(csv_buffer, delimiter='\t')
        
        # Check if parsing worked (if only 1 column, probably wrong delimiter)
        if len(df.columns) == 1:
            print(f"⚠ push_bt: Tab delimiter resulted in 1 column, trying comma delimiter")
            csv_buffer = io.StringIO(csv_string)
            df = pd.read_csv(csv_buffer, delimiter=',')
        
        # Add debug output
        print(f"✓ push_bt: Parsed CSV with {len(df)} rows")
        print(f"  Columns found: {list(df.columns)}")
        if len(df) > 0:
            print(f"  First row data:")
            first_row = df.iloc[0]
            for col in df.columns:
                val = first_row.get(col, 'NOT FOUND')
                is_na = pd.isna(val) if pd.notna(val) else True
                print(f"    '{col}': '{val}' (type: {type(val).__name__}, is_na: {is_na})")
            customer_name_val = first_row.get('customer name', 'NOT FOUND')
            customer_name_is_na = pd.isna(customer_name_val) if pd.notna(customer_name_val) else True
            print(f"  Customer name value (row 1): '{customer_name_val}'")
            print(f"  Customer name type: {type(customer_name_val)}")
            print(f"  Customer name is NaN: {customer_name_is_na}")
            print(f"  Customer name empty/whitespace: {not str(customer_name_val).strip() if customer_name_val != 'NOT FOUND' else 'N/A'}")
        
    except Exception as e:
        print(f"✗ push_bt: Failed to parse CSV data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Return a mock response object with error status
        class MockResponse:
            def __init__(self, status_code, error_msg):
                self.status_code = status_code
                self._error_msg = error_msg
            def json(self):
                return {"error": self._error_msg}
        return MockResponse(400, f"Failed to parse CSV: {str(e)}")
    
    # Prepare headers
    headers = {
        "Authorization": f"{st.session_state['tabs_api_key']}",
        "Content-Type": "application/json"
    }
    
    # Collect obligation IDs and track results
    obligation_ids = []
    errors = []
    total_rows = len(df)
    successful_count = 0
    failed_count = 0
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Extract customer name and lookup customer_id
            customer_name = row.get('customer name', '')
            
            # Notify progress - processing started
            if progress_callback:
                progress_callback(idx + 1, total_rows, customer_name, "processing")
            
            if not customer_name or pd.isna(customer_name):
                error_msg = f"Row {idx + 1}: Missing customer name"
                print(f"✗ push_bt: {error_msg}")
                errors.append(error_msg)
                failed_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows, "Unknown", "failed", error_msg)
                continue
            
            customer_id = lookup_customer_id_by_name(customer_name)
            if not customer_id:
                error_msg = f"Row {idx + 1}: Customer '{customer_name}' not found"
                print(f"✗ push_bt: {error_msg}")
                errors.append(error_msg)
                failed_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows, customer_name, "failed", error_msg)
                continue
            
            # Extract contract name and lookup/create contract_id
            contract_name = row.get('contract name', '')
            if not contract_name or pd.isna(contract_name):
                error_msg = f"Row {idx + 1}: Missing contract name"
                print(f"✗ push_bt: {error_msg}")
                errors.append(error_msg)
                failed_count += 1
                continue
            
            contract_id = lookup_or_create_contract(customer_id, contract_name)
            if not contract_id:
                error_msg = f"Row {idx + 1}: Failed to find or create contract '{contract_name}' for customer '{customer_name}'"
                print(f"✗ push_bt: {error_msg}")
                errors.append(error_msg)
                failed_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows, customer_name, "failed", error_msg)
                continue
            
            # Build URL
            url = f"https://integrators.prod.api.tabsplatform.com/v3/contracts/{contract_id}/obligations"
            
            # Extract and map new CSV columns to API payload
            service_start_date = row.get('revenue start date', '')
            service_end_date = row.get('revenue end date', '')
            name = row.get('product name', '')
            note = row.get('product description', '') if pd.notna(row.get('product description', '')) else ''
            invoice_date = row.get('invoice date', '')
            duration = 1  # Always 1 as per plan
            net_payment_terms = row.get('net payment terms', '')
            quantity = row.get('quantity', 1)
            total_price = row.get('total price', 0)
            billing_strategy = row.get('billing strategy', 'LAST_OF_PERIOD')
            billing_interval = row.get('billing interval', 'MONTH')
            interval_frequency = row.get('interval frequency', 1)
            is_recurring = row.get('is recurring revenue', True)
            qbo_item_name = row.get('QBO integration item', '')
            
            # Lookup item_id from QBO integration item name
            item_id = None
            if qbo_item_name and pd.notna(qbo_item_name) and str(qbo_item_name).strip():
                item_id = lookup_item_id_by_name(qbo_item_name)
                if not item_id:
                    print(f"  ⚠ push_bt: Row {idx + 1}: Item '{qbo_item_name}' not found, proceeding without itemId")
            
            # Event type ID is optional, leave empty
            event_type_id = ''
            
            # Handle NaN values - convert to appropriate defaults to avoid JSON serialization errors
            if pd.isna(name):
                name = ''
            if pd.isna(billing_strategy):
                billing_strategy = 'LAST_OF_PERIOD'
            if pd.isna(billing_interval):
                billing_interval = 'MONTH'
            
            # Convert net_payment_terms to int or None
            try:
                if pd.notna(net_payment_terms) and str(net_payment_terms).strip():
                    net_payment_terms = int(float(net_payment_terms))
                else:
                    net_payment_terms = None
            except (ValueError, TypeError):
                net_payment_terms = None
            
            # Convert quantity to int
            try:
                quantity = int(quantity) if pd.notna(quantity) else 1
            except (ValueError, TypeError):
                quantity = 1
            
            # Convert total_price to float
            try:
                total_price = float(total_price) if pd.notna(total_price) else 0.0
            except (ValueError, TypeError):
                total_price = 0.0
            
            # Convert interval_frequency to int
            try:
                interval_frequency = int(interval_frequency) if pd.notna(interval_frequency) else 1
            except (ValueError, TypeError):
                interval_frequency = 1
            
            # Convert is_recurring to boolean
            if pd.isna(is_recurring):
                is_recurring = True
            else:
                # Handle string values like "True", "true", "1", etc.
                is_recurring_str = str(is_recurring).strip().lower()
                is_recurring = is_recurring_str in ['true', '1', 'yes', 'y']
            
            # Map billing strategy to invoiceDateStrategy
            billing_strategy_upper = str(billing_strategy).strip().upper()
            if billing_strategy_upper in ['LAST_OF_PERIOD', 'ADVANCE']:
                invoice_date_strategy = billing_strategy_upper
            else:
                invoice_date_strategy = 'LAST_OF_PERIOD'  # Default
            
            # Map billing interval to interval enum (MONTH, WEEK, DAY, etc.)
            billing_interval_upper = str(billing_interval).strip().upper()
            # Validate interval (MONTH, WEEK, DAY, YEAR, etc.)
            valid_intervals = ['MONTH', 'WEEK', 'DAY', 'YEAR', 'QUARTER']
            if billing_interval_upper in valid_intervals:
                interval = billing_interval_upper
            else:
                interval = 'MONTH'  # Default
            
            # Handle date formatting - convert to YYYY-MM-DD format
            def format_date(date_value):
                if pd.isna(date_value) or date_value == '':
                    return None
                date_str = str(date_value).strip()
                
                # Try to parse and reformat to YYYY-MM-DD
                try:
                    from datetime import datetime
                    # Try common date formats - include 2-digit year formats
                    parsed_date = None
                    # Order matters: try most specific first
                    for fmt in [
                        '%Y-%m-%d',      # 2027-01-01
                        '%m/%d/%Y',      # 01/01/2027 or 1/1/2027 (Python handles both)
                        '%m/%d/%y',      # 01/01/27 or 1/1/27 (2-digit year)
                        '%d/%m/%Y',      # 01/01/2027 (day first)
                        '%d/%m/%y',      # 01/01/27 (day first, 2-digit year)
                        '%Y/%m/%d'       # 2027/01/01
                    ]:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d')
                    
                    # If already in YYYY-MM-DD format, return as-is
                    if len(date_str) == 10 and date_str.count('-') == 2:
                        return date_str
                    
                    return date_str  # Return as-is if parsing fails
                except:
                    return date_str
            
            service_start_date = format_date(service_start_date)
            service_end_date = format_date(service_end_date)
            invoice_date = format_date(invoice_date)
            
            # If invoice_date is None, use service_start_date as fallback
            # startDate is required by the API
            if invoice_date is None:
                invoice_date = service_start_date
            
            # Build payload - only include dates that are not None
            payload = {
                "billingSchedule": {
                    "name": name,
                    "description": note,
                    "duration": duration,
                    "invoiceDateStrategy": invoice_date_strategy,
                    "isRecurring": is_recurring,
                    "interval": interval,
                    "intervalFrequency": interval_frequency,
                    "quantity": quantity,
                    "billingType": "FLAT",
                    "pricingType": "SIMPLE",
                    "invoiceType": "INVOICE",
                    "pricing": [
                        {
                            "tier": 0,
                            "amount": total_price,
                            "amountType": "TOTAL_INVOICE",  # For FLAT billing type
                            "tierMinimum": 0
                        }
                    ]
                }
            }
            
            # Add service dates only if they are not None
            if service_start_date is not None:
                payload["serviceStartDate"] = service_start_date
            if service_end_date is not None:
                payload["serviceEndDate"] = service_end_date
            
            # Add invoice start date (required field)
            if invoice_date is not None:
                payload["billingSchedule"]["startDate"] = invoice_date
            
            # Add endDate to billingSchedule if service_end_date exists
            if service_end_date is not None:
                payload["billingSchedule"]["endDate"] = service_end_date
            
            # Add netPaymentTerms only if not None
            if net_payment_terms is not None:
                payload["billingSchedule"]["netPaymentTerms"] = net_payment_terms
            
            # Validate critical required fields before sending
            if not payload["billingSchedule"].get("startDate"):
                error_msg = f"Row {idx + 1}: Missing required startDate (invoice date and revenue start date are both empty)"
                print(f"✗ push_bt: {error_msg}")
                errors.append(error_msg)
                failed_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows, customer_name, "failed", error_msg)
                continue
            
            # Add eventTypeId if available (optional, can be empty)
            if event_type_id and pd.notna(event_type_id) and str(event_type_id).strip():
                payload["billingSchedule"]["eventTypeId"] = str(event_type_id).strip()
            
            # Add itemId if available
            if item_id and pd.notna(item_id) and str(item_id).strip():
                payload["billingSchedule"]["itemId"] = str(item_id).strip()
            
            # Make POST request
            response = requests.post(url, headers=headers, json=payload)
            
            # Handle response
            if response.status_code == 201 or response.status_code == 200:
                try:
                    response_data = response.json()
                    # Extract obligation ID from response
                    # The ID might be in payload.id or directly in the response
                    obligation_id = None
                    if 'payload' in response_data:
                        payload_data = response_data.get('payload', {})
                        obligation_id = payload_data.get('id')
                    if not obligation_id:
                        obligation_id = response_data.get('id')
                    
                    if obligation_id:
                        obligation_ids.append(obligation_id)
                        successful_count += 1
                        print(f"✓ push_bt: Created obligation {obligation_id} for contract {contract_id} (row {idx + 1})")
                        if progress_callback:
                            progress_callback(idx + 1, total_rows, customer_name, "success")
                    else:
                        print(f"⚠ push_bt: API call succeeded for row {idx + 1} but no obligation ID in response")
                        successful_count += 1
                        if progress_callback:
                            progress_callback(idx + 1, total_rows, customer_name, "success")
                except Exception as e:
                    print(f"⚠ push_bt: API call succeeded for row {idx + 1} but failed to parse response: {str(e)}")
                    successful_count += 1
                    if progress_callback:
                        progress_callback(idx + 1, total_rows, customer_name, "success")
            else:
                # Extract detailed error information from API response
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    
                    # Build detailed error message with API response details
                    error_parts = []
                    
                    # Get main error message
                    if 'message' in error_data:
                        error_parts.append(error_data['message'])
                    
                    # Check for nested error object with details
                    if 'error' in error_data and isinstance(error_data['error'], dict):
                        error_obj = error_data['error']
                        
                        # Add error code if present
                        if 'code' in error_obj:
                            error_parts.append(f"Error Code: {error_obj['code']}")
                        
                        # Add error message if present and different from main message
                        if 'message' in error_obj and error_obj['message'] not in error_parts:
                            error_parts.append(error_obj['message'])
                        
                        # Add validation details if present
                        if 'details' in error_obj and isinstance(error_obj['details'], dict):
                            details = error_obj['details']
                            detail_messages = []
                            for field, messages in details.items():
                                if isinstance(messages, list):
                                    for msg in messages:
                                        detail_messages.append(f"• {field}: {msg}")
                                else:
                                    detail_messages.append(f"• {field}: {messages}")
                            
                            if detail_messages:
                                error_parts.append("\n  " + "\n  ".join(detail_messages))
                    
                    # Fallback to other error fields if nothing extracted yet
                    if not error_parts:
                        if 'error' in error_data and isinstance(error_data['error'], str):
                            error_parts.append(error_data['error'])
                        elif 'errors' in error_data:
                            error_parts.append(str(error_data['errors']))
                        else:
                            # Last resort - show status code
                            error_parts.append(f"Status {response.status_code}")
                    
                    # Combine all error parts with clear separation
                    if error_parts:
                        error_msg = " | ".join(error_parts)
                    
                    # Print full error response for debugging
                    print(f"  Debug - Full error response: {error_data}")
                except Exception as e:
                    # If JSON parsing fails, use raw response text
                    try:
                        error_msg = f"HTTP {response.status_code} - {response.text[:200]}"
                    except:
                        error_msg = f"HTTP {response.status_code} - Unable to parse error response"
                    print(f"  Debug - Error parsing response: {str(e)}")
                
                # Format final error message for user
                full_error_msg = f"{customer_name}: {error_msg}"
                
                print(f"✗ push_bt: Failed to create obligation for contract {contract_id} (row {idx + 1}): {error_msg}")
                errors.append(full_error_msg)
                failed_count += 1
                if progress_callback:
                    progress_callback(idx + 1, total_rows, customer_name, "failed", error_msg)
                
        except Exception as e:
            error_msg = f"Row {idx + 1}: {str(e)}"
            print(f"✗ push_bt: Error processing row {idx + 1}: {str(e)}")
            errors.append(error_msg)
            failed_count += 1
            # Try to get customer name for callback
            try:
                customer_name = row.get('customer name', 'Unknown')
            except:
                customer_name = 'Unknown'
            if progress_callback:
                progress_callback(idx + 1, total_rows, customer_name, "failed", error_msg)
    
    # Print summary
    print(f"✓ push_bt: Processed {total_rows} row(s) - {successful_count} successful, {failed_count} failed")
    if obligation_ids:
        print(f"✓ push_bt: Created {len(obligation_ids)} obligation(s)")
    
    # Create a mock response object compatible with old implementation
    class MockResponse:
        def __init__(self, status_code, obligation_ids, errors, successful_count, failed_count):
            self.status_code = status_code
            self._obligation_ids = obligation_ids
            self._errors = errors
            self._successful_count = successful_count
            self._failed_count = failed_count
        
        def json(self):
            # Return structure compatible with old implementation
            return {
                "billingTermIds": self._obligation_ids,
                "errors": self._errors if self._errors else None,
                "successful_count": self._successful_count,
                "failed_count": self._failed_count
            }
    
    # Return success if at least some obligations were created
    status_code = 201 if successful_count > 0 else 400
    return MockResponse(status_code, obligation_ids, errors, successful_count, failed_count)
