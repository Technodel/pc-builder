import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. DATA LOADER ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), header=None)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. HEADER-BASED PARSER ---
def parse_by_title(df, title_keyword):
    if df is None or df.empty: return pd.DataFrame()
    data = []
    found = False
    for _, row in df.iterrows():
        # Search Column A for your specific titles
        val_a = str(row.iloc[0]).strip().upper()
        if not found:
            if title_keyword.upper() in val_a:
                found = True
            continue
        # Stop at the next header or empty row
        if not val_a or val_a == "NAN" or any(x in val_a for x in ["MOTHER", "STORAGE", "COOLER", "CASES", "RAMS", "POWER", "GRAPHICS", "UPS"]):
            if len(data) > 0: break
            else: continue
        try:
            name = str(row.iloc[0])
            price_raw = str(row.iloc[1]).replace('$', '').replace(',', '').strip()
            data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
        except: continue
    return pd.DataFrame(data)

# --- 3. APP UI ---
raw_df = load_all_data()
if not raw_df.empty:
    # We use your titles directly
    dfs = {
        "cpu": parse_by_title(raw_df, "PROCESSORS"),
        "gpu": parse_by_title(raw_df, "GRAPHICS CARDS"),
        "ram": parse_by_title(raw_df, "RAMS"),
        "psu": parse_by_title(raw_df, "POWER SUPPLIES")
    }
    
    st.success("✅ Success! Found categories using your titles.")
    st.selectbox("Choose Processor", ["Select"] + dfs['cpu']['ITEM'].tolist())
