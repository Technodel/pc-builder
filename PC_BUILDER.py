import streamlit as st
import pandas as pd
import urllib.parse
import requests
from io import BytesIO

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

# --- 2. DATA LOADER (THE "NO-EMAIL" METHOD) ---
@st.cache_data(ttl=600)
def load_all_data():
    # Replace this with your actual Google Sheet ID
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    # Use the gid for the 'hardware' tab (usually 0 if it's the first tab)
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    
    try:
        # We add a 'User-Agent' to pretend we are a browser and avoid the 400 Error
        response = requests.get(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content))
            return df
        else:
            st.error(f"❌ Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

# --- 3. PARSING LOGIC (Same as agreed) ---
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

# --- 4. EXECUTION ---
raw_sheet = load_all_data()

if raw_sheet.empty:
    st.warning("⚠️ Still getting a 400 error. Ensure your sheet is 'Published to the Web'.")
else:
    dfs = {s: parse_section(raw_sheet, s) for s in ["cpu", "mb", "ram", "gpu", "case"]}
    st.success("✅ Connection Successful!")
    
    # Selection UI
    cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist()
    st.selectbox("Step 1: Choose Processor", cpu_list, key="c")

# --- 5. SHARE BUILD LINK (Your new project requirement) ---
st.divider()
if st.session_state.get('c') and "Select" not in st.session_state['c']:
    base_url = "https://technodel-builder.streamlit.app/?"
    # Generates the link for customers [cite: 2026-02-19]
    params = {"c": st.session_state['c']}
    st.subheader("🔗 Share Build Link")
    st.code(base_url + urllib.parse.urlencode(params))
