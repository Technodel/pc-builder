import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. CONFIG & LOGO ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide")

st.markdown(
    """
    <div style="text-align: left; padding-bottom: 5px;">
        <img src="https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp" width="280">
    </div>
    """,
    unsafe_allow_html=True
)

# --- 2. DATA LOADER (REPLICATING MARKETING BOT SUCCESS) ---
@st.cache_data(ttl=600)
def load_all_data():
    # Your Sheet ID
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    # Your hardware tab GID
    HARDWARE_GID = "1309359556"
    
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    
    try:
        # User-Agent tricks Google into allowing the connection
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
        else:
            # Displays the exact error from your screen
            st.error(f"Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- 3. PARSING LOGIC ---
def parse_section(df, keyword):
    if df.empty: return pd.DataFrame()
    data = []
    found_section = False
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
            data.append({"ITEM": name, "PRICE": clean_price})
        except: continue
    return pd.DataFrame(data)

# --- 4. UI EXECUTION ---
raw_df = load_all_data()

if raw_df.empty:
    st.warning("⚠️ Connection failed. Ensure 'File > Share > Publish to web' is active.")
else:
    st.success("✅ SUCCESS! Data loaded from Hardware tab.")
    
    # Parse the data
    sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
    dfs = {s: parse_section(raw_df, s) for s in sections}

    st.title("Build Your PC")
    
    # Get parameters from URL [cite: 2026-02-19]
    params = st.query_params
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Example CPU Selectbox
        cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist()
        # Auto-select if in URL [cite: 2026-02-19]
        default_cpu = params.get("c", "Select CPU")
        idx = cpu_list.index(default_cpu) if default_cpu in cpu_list else 0
        selected_cpu = st.selectbox("Step 1: Choose Processor", cpu_list, index=idx, key="c")

# --- 5. SHARE BUILD LINK (Your Project Requirement) ---
# Generates the link to send to customers [cite: 2026-02-19]
st.divider()
if not raw_df.empty and st.session_state.get('c') != "Select CPU":
    st.subheader("🔗 Share Build Link")
    base_url = "https://technodel-builder.streamlit.app/?"
    query = urllib.parse.urlencode({"c": st.session_state['c']})
    st.code(base_url + query)
