# Alkira Streamlit App


Usage Transformation for Alkira
## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API key:
   - Option 1: Add it to `.streamlit/secrets.toml`:
   ```toml
   tabs_api_key = "your-api-key-here"
   ```
   - Option 2: Enter it in the sidebar when running the app

3. Run the app:
```bash
streamlit run main.py
```

## API

- Get All Products
- Create Obligations

## Files to Upload:
1. Monthly Minimums
2. Customer Mapping
3. By Community Report
4. By Business Unit Report
5. By Combo Report
6. Flat BTs

## Project Structure

- `main.py` - Main Streamlit application
- `api.py` - API functions for Tabs platform integration
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit configuration
- `.streamlit/secrets.toml` - Secrets (API keys, etc.)


Things to store
Tabs Obligations


