import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. DEFINITIONS (Functions must come first) ---

@st.cache_data(ttl=600)
def load_all_data():
    """Fetches data from Google Sheets using the Marketing Bot method."""
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def parse_section(df, keyword):
    """Parses specific hardware tables from the main sheet."""
    if df is None or df.empty:
        return pd.DataFrame()
    data = []
    found_section = False
    
    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        
        # Stop at next table or empty row
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        try:
            # Using Index positions to avoid 'KeyError: ITEM'
            name = str(row.iloc[1]) 
            price_val = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_val), 0))
            data.append({"ITEM": name, "PRICE": clean_price})
        except:
            continue
    return pd.DataFrame(data)

# --- 2. EXECUTION (Now Python knows the functions) ---

# This was line 34 - now it works because load_all_data is defined above!
raw_df = load_all_data()

if raw_df is not None and not raw_df.empty:
    # 3. PARSE SECTIONS
    sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
    dfs = {s: parse_section(raw_df, s) for s in sections}

    # 4. UI SETUP
    st.title("Build Your PC")
    
    # Handle URL parameters for customer links [cite: 2026-02-19]
    params = st.query_params
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Step 1: CPU Selection
        if not dfs['cpu'].empty:
            cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist()
            url_cpu = params.get("c", "Select CPU")
            default_idx = cpu_list.index(url_cpu) if url_cpu in cpu_list else 0
            
            selected_cpu = st.selectbox("Step 1: Choose Processor", cpu_list, index=default_idx, key="c")
        else:
            st.error("Could not find 'table_cpu' in your sheet.")

    # 5. SHARE BUILD LINK [cite: 2026-02-19]
    st.divider()
    if st.session_state.get('c') and st.session_state['c'] != "Select CPU":
        st.subheader("🔗 Share Build Link")
        base_url = "https://technodel-builder.streamlit.app/?"
        query = urllib.parse.urlencode({"c": st.session_state['c']})
        st.code(base_url + query)
else:
    st.error("Failed to load data. Please ensure the Google Sheet is 'Published to the Web'.")
