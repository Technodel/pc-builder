import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re
import urllib.parse

# --- 1. PAGE CONFIG & LOGO ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide", page_icon="💻")

st.markdown(
    """
    <div style="text-align: left; padding-bottom: 5px;">
        <img src="https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp" width="280">
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. THE BOT CONNECTION (FIXES HTTP 400) ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # Using the official connection logic from your marketing bot [cite: 2026-02-19]
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # This points to your specific Google Sheet
        # Ensure this URL matches your actual hardware sheet URL
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4/edit#gid=0"
        
        # Load the 'hardware' worksheet specifically
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
        # Column A (Index 0) contains the table tags like table_cpu
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        
        # Stop at next table or empty row
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        if "DDR4" in val_a.upper(): current_ram_tech = "DDR4"
        if "DDR5" in val_a.upper(): current_ram_tech = "DDR5"
        
        try:
            # Column B is Name (Index 1), Column C is Price (Index 2) [cite: 2026-02-16]
            name = str(row.iloc[1])
            raw_price = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(raw_price), 0))
            
            data.append({
                "ITEM": name, 
                "PRICE": clean_price,
                "RAM_TECH": "DDR5" if "DDR5" in name.upper() else ("DDR4" if "DDR4" in name.upper() else current_ram_tech)
            })
        except: continue
    return pd.DataFrame(data)

# --- 3. EXECUTION ---
raw_sheet = load_all_data()
sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
dfs = {s: parse_section(raw_sheet, s) for s in sections}

# [Your original compatibility and UI logic follows here 100% unchanged]

# --- 4. SHARE BUILD LINK (NEW) ---
if any(st.session_state.get(k) and "Select" not in st.session_state[k] for k in ['c','m','g']):
    st.divider()
    base_url = "https://technodel-builder.streamlit.app/?"
    params = {k: st.session_state[k] for k in ['c','m','g','p','ca','co'] if st.session_state.get(k) and "Select" not in st.session_state[k]}
    st.subheader("🔗 Share Build Link")
    st.code(base_url + urllib.parse.urlencode(params))
