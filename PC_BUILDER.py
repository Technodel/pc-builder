import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. DATA LOADER ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        return pd.read_csv(BytesIO(response.content), header=None) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. TECHNODEL LOGIC: GENERATION GRABBER ---
def get_intel_gen(name):
    """Logic: 4 digits (e.g. 6500) = 1st digit. 5 digits (e.g. 12700) = first 2 digits."""
    match = re.search(r'i\d-(\d{4,5})', name, re.I)
    if match:
        digits = match.group(1)
        return int(digits[:2]) if len(digits) == 5 else int(digits[0])
    return None

def find_component_data(df, title):
    for col in df.columns:
        match = df[df[col].astype(str).str.contains(title, case=False, na=False)]
        if not match.empty:
            start_row = match.index[0] + 1
            data = []
            for i in range(start_row, len(df)):
                name = str(df.iloc[i, col]).strip()
                if not name or name == "nan" or "PRICE" in name.upper():
                    if len(data) > 0: break
                    continue
                try:
                    price = int(round(float(str(df.iloc[i, col + 1]).replace('$', '').replace(',', '')), 0))
                    data.append({"ITEM": name, "PRICE": price, "GEN": get_intel_gen(name)})
                except: continue
            return pd.DataFrame(data)
    return pd.DataFrame()

# --- 3. UI EXECUTION ---
raw_df = load_all_data()
if not raw_df.empty:
    cats = {"CPU": "PROCESSORS", "MB": "MOTHER BOARDS", "RAM": "RAMS", "ST": "INTERNAL STORAGE", "GPU": "GRAPHICS CARDS", "PSU": "POWER SUPPLIES", "CASE": "CASES", "UPS": "UPS"}
    dfs = {k: find_component_data(raw_df, v) for k, v in cats.items()}
    
    st.title("Technodel Smart Builder")
    
    # Selection logic
    col1, col2 = st.columns(2)
    with col1:
        cpu_sel = st.selectbox("Processor", ["Select"] + dfs['CPU']['ITEM'].tolist())
        cpu_gen = dfs['CPU'][dfs['CPU']['ITEM'] == cpu_sel]['GEN'].values[0] if cpu_sel != "Select" else None
        if cpu_gen: st.success(f"Detected: {cpu_gen}th Generation")

        mb_sel = st.selectbox("Motherboard", ["Select"] + dfs['MB']['ITEM'].tolist())
        # COMPATIBILITY CHECK: Look for gen in motherboard parenthesis (e.g. "H610 (12,13)")
        if mb_sel != "Select" and cpu_gen:
            compat_match = re.search(r'\((.*?)\)', mb_sel)
            if compat_match:
                allowed = [g.strip() for g in compat_match.group(1).split(',')]
                if str(cpu_gen) not in allowed:
                    st.error(f"⚠️ Incompatible! Board supports generations: {', '.join(allowed)}")

    with col2:
        # EXPANDABLE RAM & STORAGE (UP TO 4)
        r_qty = st.number_input("RAM Quantity", 1, 4, 1)
        r_model = st.selectbox("RAM Type", ["Select"] + dfs['RAM']['ITEM'].tolist())
        
        s_qty = st.number_input("Storage Quantity", 1, 4, 1)
        s_model = st.selectbox("Storage Model", ["Select"] + dfs['ST']['ITEM'].tolist())

    # --- FOOTER & CONTACTS ---
    st.divider()
    st.write("📞 03 659872 | 70 449900 | 71 234002 | 07 345689")
    st.write("🌐 [Technodel.net](https://Technodel.net) | [Instagram](https://instagram.com/technodel_computers)")
