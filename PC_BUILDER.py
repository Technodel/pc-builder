import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. DATA LOADER ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556" # Your hardware tab
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), header=None) # Load without headers to see 'table_cpu'
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- 2. UNIVERSAL PARSER ---
def parse_section(df, table_tag):
    if df is None or df.empty:
        return pd.DataFrame()
    
    data = []
    found_section = False
    
    for _, row in df.iterrows():
        # Look at Column A for the tag (table_cpu, table_gpu, etc.)
        val_a = str(row.iloc[0]).strip().lower()
        
        if not found_section:
            if val_a == table_tag.lower():
                found_section = True
            continue
        
        # Stop if we hit the next table tag or a truly empty row
        if not val_a or val_a == "nan" or "table_" in val_a:
            # If we already have data, it means the table ended
            if len(data) > 0: break
            else: continue # Skip the header row (e.g., 'PROCESSORS')
            
        try:
            name = str(row.iloc[0]) # Item Name
            # Clean the price string from Column B
            price_raw = str(row.iloc[1]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_raw), 0))
            data.append({"ITEM": name, "PRICE": clean_price})
        except:
            continue
    return pd.DataFrame(data)

# --- 3. APP LOGIC ---
raw_df = load_all_data()

if not raw_df.empty:
    st.success("✅ Connected to Technodel Price List")
    
    # Now you can call any table by its tag name!
    # [cite: 2026-02-19]
    cpu_df = parse_section(raw_df, "table_cpu")
    gpu_df = parse_section(raw_df, "table_gpu")
    psu_df = parse_section(raw_df, "table_psu")

    st.title("Build Your PC")
    
    # Selection UI
    if not cpu_df.empty:
        cpu_list = ["Select CPU"] + cpu_df['ITEM'].tolist()
        st.selectbox("Step 1: Processor", cpu_list, key="c")
    else:
        st.warning("Could not find 'table_cpu' in Column A.")
