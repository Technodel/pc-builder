import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- DATA LOADER (THE FIX) ---
@st.cache_data(ttl=600)
def load_all_data():
    # Your Sheet ID from your screenshot
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    
    # CHANGE THIS NUMBER: Paste the gid number you found in your browser here
    HARDWARE_GID = "gid=1309359556" 
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    
    try:
        # Browser impersonation to avoid 400 error
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(csv_url, headers=headers)
        
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
        else:
            st.error(f"Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- THE REST OF YOUR LOGIC ---
df = load_all_data()

if not df.empty:
    st.success("✅ CONNECTION RESTORED!")
    # Proceed with parsing...
else:
    st.warning("⚠️ Still getting a 400. Did you double-check the 'gid' number?")
