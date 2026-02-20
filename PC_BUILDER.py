import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re
import urllib.parse

# --- 1. PAGE CONFIG & LOGO ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide", page_icon="💻")

# Technodel Site Logo
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
def load_all_data():
    try:
        # This uses the connection settings from your Streamlit Secrets
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Load the "hardware" tab specifically
        df = conn.read(worksheet="hardware")
        return df
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.info("💡 Pro Tip: Make sure you shared the Google Sheet with the 'client_email' found in your Secrets!")
        return pd.DataFrame()

def parse_section(df, keyword):
    if df.empty: return pd.DataFrame()
    data = []
    found_section = False
    current_ram_tech = None
    
    for _, row in df.iterrows():
        # Column A is index 0 (tags like table_cpu)
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
            name = str(row.iloc[1]) # Column B
            # Clean price formatting
            price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_str), 0))
            
            data.append({
                "ITEM": name, 
                "PRICE": clean_price,
                "RAM_TECH": "DDR5" if "DDR5" in name.upper() else ("DDR4" if "DDR4" in name.upper() else current_ram_tech)
            })
        except: continue
    return pd.DataFrame(data)

# --- 3. DATA & UI ---
raw_sheet = load_all_data()
sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
dfs = {s: parse_section(raw_sheet, s) for s in sections}

# --- SELECTBOXES ---
st.title("Build Your PC")
col1, col2 = st.columns([2, 1])

with col1:
    cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist() if not dfs['cpu'].empty else ["No Data"]
    selected_cpu = st.selectbox("Choose Processor", cpu_list, key="c")
    
    # [Add the rest of your selectboxes (m, g, r, etc.) here]

# --- 4. SHARE BUILD LINK ---
if any(st.session_state.get(k) and "Select" not in str(st.session_state[k]) for k in ['c']):
    st.divider()
    base_url = "https://technodel-builder.streamlit.app/?"
    params = {k: st.session_state[k] for k in ['c','m','g','p','ca','co'] if st.session_state.get(k) and "Select" not in str(st.session_state[k])}
    st.subheader("🔗 Share Build Link")
    st.code(base_url + urllib.parse.urlencode(params))
