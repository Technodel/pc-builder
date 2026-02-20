import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import urllib.parse

# --- 1. THE CONNECTION (REPLICATING THE SUCCESSFUL BOT) ---
@st.cache_data(ttl=600)
def load_all_data():
    # This ID matches your Sheet 'Price_List_2026-02-19'
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    
    # gid=0 is the 'hardware' tab because it is the first tab on the left
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    
    try:
        # THE KEY: This header 'tricks' Google into thinking a person is visiting
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(csv_url, headers=headers)
        
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
        else:
            # Matches the error in your screenshot
            st.error(f"Google rejected the request (Status {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

# --- 2. PARSING LOGIC (Technodel Standards) ---
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
            name = str(row.iloc[1])
            price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_str), 0))
            data.append({"ITEM": name, "PRICE": clean_price})
        except: continue
    return pd.DataFrame(data)

# --- 3. UI EXECUTION ---
df = load_all_data()

if df is not None and not df.empty:
    dfs = {s: parse_section(df, s) for s in ["cpu", "mb", "ram", "gpu"]}
    st.success("✅ Connected successfully using the Marketing Bot method!")
    
    # Simple selection for testing
    cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist()
    st.selectbox("Step 1: Choose Processor", cpu_list, key="c")
else:
    # Error state from your screenshot
    st.warning("Still blocked. Ensure 'File > Share > Publish to Web' is active in the sheet.")

# --- 4. SHARE BUILD LINK (Your Project Requirement) ---
# [cite: 2026-02-19]
st.divider()
if st.session_state.get('c') and "Select" not in st.session_state['c']:
    base_url = "https://technodel-builder.streamlit.app/?"
    params = {"c": st.session_state['c']}
    st.subheader("🔗 Share Build Link")
    st.code(base_url + urllib.parse.urlencode(params))
