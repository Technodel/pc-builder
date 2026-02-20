import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# --- 2. LOGIC (RESTORED FROM OFFLINE) ---
def get_cpu_gen(cpu_name):
    match = re.search(r'(\d{4,5})', cpu_name)
    if match:
        val = match.group(1)
        return val[:2] if len(val) == 5 else val[0]
    return None

def is_compat(cpu_sel, mb_name):
    if "Select" in cpu_sel: return True
    gen = get_cpu_gen(cpu_sel)
    match = re.search(r'\((.*?)\)', mb_name)
    if gen and match:
        allowed = re.findall(r'\d+', match.group(1))
        return str(gen) in allowed
    return True

# --- 3. DATA GRABBER (FIXED FOR NESTED DDR TABLES) ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_ram_by_tech(df, tech_type):
    """Finds the 'RAMS' column, then looks for the sub-header (DDR3/4/5)."""
    # 1. Find the column that contains 'RAMS'
    mask = df.apply(lambda s: s.astype(str).str.strip().str.upper() == "RAMS")
    matches = mask.stack()
    if matches.empty: return pd.DataFrame()
    
    row_idx, col_idx = matches.index[0]
    data = []
    found_sub_header = False
    
    # 2. Start from 'RAMS' and look for DDR3, DDR4, or DDR5
    for i in range(row_idx + 1, len(df)):
        cell_val = str(df.iloc[i, col_idx]).strip()
        
        # If we find our target tech (e.g., DDR5)
        if cell_val.upper() == tech_type.upper():
            found_sub_header = True
            continue
        
        # If we are in our tech section, grab names until we hit the next DDR header or empty
        if found_sub_header:
            if not cell_val or cell_val.lower() == "nan" or "DDR" in cell_val.upper():
                if len(data) > 0: break # Stop if we hit the next section
                continue
            
            try:
                price = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                data.append({"ITEM": cell_val, "PRICE": int(round(float(price), 0))})
            except: continue
            
    return pd.DataFrame(data)

def find_standard_data(df, title):
    """Handles standard columns like PROCESSORS, MOTHER BOARDS, etc."""
    mask = df.apply(lambda s: s.astype(str).str.strip().str.upper() == title.upper())
    matches = mask.stack()
    if matches.empty: return pd.DataFrame()
    
    row_idx, col_idx = matches.index[0]
    data = []
    for i in range(row_idx + 1, len(df)):
        name = str(df.iloc[i, col_idx]).strip()
        if not name or name.lower() == "nan" or name == "": break
        try:
            price = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
            data.append({"ITEM": name, "PRICE": int(round(float(price), 0))})
        except: continue
    return pd.DataFrame(data)

# --- 4. APP EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # Standard Categories
    titles = {
        'cpu': 'PROCESSORS', 'mb': 'MOTHER BOARDS', 'gpu': 'GRAPHICS CARDS',
        'psu': 'POWER SUPPLIES', 'case': 'CASES', 'coo': 'CPU COOLERS',
        'storage': 'INTERNAL STORAGE'
    }
    dfs = {k: find_standard_data(raw_df, v) for k, v in titles.items()}
    
    st.title("Technodel Smart Builder")

    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()], key="c")
        
        mb_options = dfs['mb']
        if "Select" not in cpu_choice:
            mb_options = mb_options[mb_options['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_options.iterrows()], key="m")
        
        # FIXED RAM LOGIC: Detects DDR tech from board name and finds sub-header in Sheet
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            current_ram_df = find_ram_by_tech(raw_df, tech)
            
            if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
            for i in range(st.session_state.ram_count):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in current_ram_df.iterrows()], key=f"ram_{i}")
            
            if st.button("➕ Add RAM"):
                st.session_state.ram_count += 1; st.rerun()

    with col2:
        gpu_choice = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['gpu'].iterrows()], key="g")
        psu_choice = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['psu'].iterrows()], key="p")
        case_choice = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['case'].iterrows()], key="ca")
        
        st.divider()
        if 'storage_count' not in st.session_state: st.session_state.storage_count = 1
        for i in range(st.session_state.storage_count):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['storage'].iterrows()], key=f"store_{i}")
        if st.button("➕ Add Storage"):
            st.session_state.storage_count += 1; st.rerun()

    # --- TOTALS ---
    total = 0
    for key in ['c', 'm', 'g', 'p', 'ca']:
        val = st.session_state.get(key)
        if val and "Select" not in val: total += int(val.split(" - $")[1].replace(",", ""))

    for i in range(st.session_state.get('ram_count', 1)):
        val = st.session_state.get(f"ram_{i}")
        if val and "Select" not in val: total += int(val.split(" - $")[1].replace(",", ""))

    for i in range(st.session_state.get('storage_count', 1)):
        val = st.session_state.get(f"store_{i}")
        if val and "Select" not in val: total += int(val.split(" - $")[1].replace(",", ""))

    if total > 0:
        st.header(f"TOTAL PRICE: ${total:,}")
