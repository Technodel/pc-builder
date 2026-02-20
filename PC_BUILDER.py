import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re
import urllib.parse

# --- 1. PAGE CONFIG & LOGO ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide", page_icon="💻")

# Your exact logo formatting
st.markdown(
    """
    <div style="text-align: left; padding-bottom: 5px;">
        <img src="https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp" width="280">
    </div>
    """,
    unsafe_allow_html=True
)

# Your exact CSS styles
st.markdown("""
    <style>
    .stSelectbox { margin-bottom: -15px; }
    .stButton button { width: 100%; border-radius: 5px; height: 2.2em; margin-top: 10px;}
    .live-summary { background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #00a8e8; margin-bottom: 20px; }
    .screenshot-box { background-color: #ffffff; padding: 30px; border: 2px solid #333; border-radius: 12px; color: #000000; margin-top: 20px; }
    .contact-footer { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #00a8e8; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BOT CONNECTION (FIXES HTTP 400) ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # Same connection logic used in the marketing bot [cite: 2026-02-19]
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Replace this with your actual Google Sheet URL
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4/edit#gid=0"
        
        # Pulling the 'hardware' sheet specifically
        df = conn.read(spreadsheet=SHEET_URL, worksheet="hardware")
        return df
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

def parse_section(df, keyword):
    if df.empty: return pd.DataFrame()
    data = []
    found_section = False
    current_ram_tech = None
    
    for _, row in df.iterrows():
        # Using index 0 for Column A (Table Tags)
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        
        # End of table check
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        if "DDR4" in val_a.upper(): current_ram_tech = "DDR4"
        if "DDR5" in val_a.upper(): current_ram_tech = "DDR5"
        
        try:
            name = str(row.iloc[1]) # Column B
            # Clean price formatting exactly as agreed [cite: 2026-02-16]
            price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_str), 0))
            
            data.append({
                "ITEM": name, 
                "PRICE": clean_price,
                "RAM_TECH": "DDR5" if "DDR5" in name.upper() else ("DDR4" if "DDR4" in name.upper() else current_ram_tech)
            })
        except: continue
    return pd.DataFrame(data)

# Fetching data
raw_sheet = load_all_data()
sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
dfs = {s: parse_section(raw_sheet, s) for s in sections}

# --- 3. COMPATIBILITY & UI (Your Perfect Logic) ---
# [Your gen extraction, compatibility checks, and selectboxes go here]

# --- 4. SHARE BUILD LINK (NEW FEATURE) ---
st.divider()
base_url = "https://technodel-builder.streamlit.app/?"
# This generates a link that automatically pre-selects parts for customers [cite: 2026-02-19]
build_params = {k: st.session_state[k] for k in ['c','m','g','p','ca','co'] if st.session_state.get(k) and "Select" not in st.session_state[k]}

if build_params:
    st.subheader("🔗 Share Build Link")
    st.code(base_url + urllib.parse.urlencode(build_params))
