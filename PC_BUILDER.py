import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. CONFIG ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide")

# --- 2. DATA LOADER (THE FIX) ---
@st.cache_data(ttl=600)
def load_data_no_email():
    # Replace with your actual Sheet ID
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    # Ensure GID matches your 'hardware' tab (0 = first tab)
    URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    
    try:
        # The 'User-Agent' header is what kills the 400 Error
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
        else:
            st.error(f"❌ Google rejected request: Status {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

# --- 3. UI LOGIC ---
df = load_data_no_email()

if df.empty:
    st.warning("⚠️ Still blocked. Did you click 'Publish to the web' in Google Sheets?")
else:
    st.success("✅ Connection Fixed!")
    # Your parsing logic for 'table_cpu' etc. goes here
    
# --- 4. SHARE BUILD LINK (Your Project Goal) ---
# [cite: 2026-02-19]
if st.button("Generate Share Link"):
    base_url = "https://technodel-builder.streamlit.app/?"
    # Add your selection logic here
    st.code(base_url + "c=Intel+i9")
