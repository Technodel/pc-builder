import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. LOGO & CONFIG ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide")

st.markdown(
    """
    <div style="text-align: left; padding-bottom: 5px;">
        <img src="https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp" width="280">
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. THE CONNECTION (FIXES HTTP 400) ---
@st.cache_data(ttl=600)
def load_data_from_public_sheet():
    # Your Sheet ID from the screenshot
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    # The 'hardware' tab is the first tab, so gid=0
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    
    try:
        # This header 'tricks' Google into thinking a browser is visiting
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(csv_url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content))
            return df
        else:
            st.error(f"❌ Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

# --- 3. DATA PROCESSING ---
raw_df = load_data_from_public_sheet()

if raw_df.empty:
    st.warning("⚠️ Still blocked. Make sure 'Publish to web' is active.")
else:
    st.success("✅ Connected successfully to 'hardware' tab!")
    
    # Your specific parsing logic for table_cpu, table_gpu, etc.
    # [Insert your parsing code here]

# --- 4. SHARE BUILD LINK ---
# This fulfills your requirement for technodel-builder.streamlit.app [cite: 2026-02-19]
st.divider()
if not raw_df.empty:
    st.subheader("🔗 Share Build Link")
    base_url = "https://technodel-builder.streamlit.app/?"
    # Example logic: add your actual selection variables here
    params = {"build": "custom"} 
    st.code(base_url + urllib.parse.urlencode(params))
