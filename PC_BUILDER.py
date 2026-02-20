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

# --- 2. DATA LOADER (THE BOT LOGIC) ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # Step A: Establish connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Step B: Read the 'hardware' tab
        # We use 'read' without a URL because the URL should be in your Secrets
        df = conn.read(worksheet="hardware")
        return df
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.info("💡 ACTION REQUIRED: Ensure you have added the 'client_email' from your Secrets to your Google Sheet 'Share' list.")
        return pd.DataFrame()

def parse_section(df, keyword):
    if df.empty: return pd.DataFrame()
    data = []
    found_section = False
    current_ram_tech = None
    
    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        try:
            name = str(row.iloc[1]) # Column B
            price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_str), 0))
            
            data.append({
                "ITEM": name, 
                "PRICE": clean_price,
                "RAM_TECH": "DDR5" if "DDR5" in name.upper() else ("DDR4" if "DDR4" in name.upper() else "DDR4")
            })
        except: continue
    return pd.DataFrame(data)

# --- 3. EXECUTION ---
raw_sheet = load_all_data()
sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
dfs = {s: parse_section(raw_sheet, s) for s in sections}

# --- 4. THE UI (RESTORED PERFECT LOGIC) ---
st.title("Build Your PC")

if raw_sheet.empty:
    st.warning("⚠️ No data loaded. Please check the connection error above.")
else:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        cpu_options = ["Select CPU"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()]
        cpu_choice = st.selectbox("Step 1: Processor", cpu_options, key="c")
        
        # Auto-selection from URL Logic
        params = st.query_params
        # ... (rest of your selection logic)

    # --- 5. SHARE BUILD LINK ---
    st.divider()
    base_url = "https://technodel-builder.streamlit.app/?"
    # Only show link if parts are selected
    active_params = {k: st.session_state[k] for k in ['c'] if st.session_state.get(k) and "Select" not in st.session_state[k]}
    
    if active_params:
        st.subheader("🔗 Share Build Link")
        st.code(base_url + urllib.parse.urlencode(active_params))
