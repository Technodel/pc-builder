import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. DATA LOADER (REPLICATING MARKETING BOT) ---
@st.cache_data(ttl=600)
def load_all_data():
    # This ID matches your Sheet 'Price_List_2026-02-19'
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    
    # gid=0 refers to the first tab. Your screenshot shows 'hardware' is first
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    
    try:
        # THE KEY FIX: We add a 'User-Agent' so Google treats us like a browser
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(csv_url, headers=headers)
        
        if response.status_code == 200:
            # Successfully fetched CSV data
            return pd.read_csv(BytesIO(response.content))
        else:
            # This triggers if Google rejects the specific request
            st.error(f"Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- 2. EXECUTION ---
df = load_all_data()

if df.empty:
    # If the sheet is shared but not published, it will stay blocked
    st.warning("Still blocked. Ensure 'File > Share > Publish to Web' is active in the sheet.")
else:
    st.success("✅ Connected successfully to 'hardware' tab!")
    # Proceed with your table_cpu parsing logic...
