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

# --- 3. THE DATA GRABBER (LOCKED TO COLUMNS) ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def get_data_from_col(df, col_idx, start_title, sub_filter=None):
    """Reads items from a specific column index only."""
    data = []
    found_start = False
    
    for i in range(len(df)):
        cell_val = str(df.iloc[i, col_idx]).strip()
        
        # Look for the header (e.g. PROCESSORS or DDR5)
        if not found_start:
            if cell_val.upper() == start_title.upper():
                found_start = True
            continue
        
        # Once header is found, collect items
        if found_start:
            # STOP if cell is empty or we hit another major DDR header (if we are in RAMS)
            if not cell_val or cell_val.lower() == "nan" or cell_val == "":
                if len(data) > 0: break
                continue
            
            # If we are looking for a specific RAM tech (DDR3/4/5)
            if sub_filter and "DDR" in cell_val.upper() and cell_val.upper() != sub_filter.upper():
                if len(data) > 0: break
                continue

            try:
                price_val = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                data.append({"ITEM": cell_val, "PRICE": int(round(float(price_val), 0))})
            except: continue
            
    return pd.DataFrame(data)

# --- 4. APP EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # We map titles to their exact column index in your sheet
    # Column A=0, D=3, G=6, J=9 etc.
    dfs = {
        'cpu': get_data_from_col(raw_df, 0, 'PROCESSORS'),
        'mb':  get_data_from_col(raw_df, 3, 'MOTHER BOARDS'),
        'gpu': get_data_from_col(raw_df, 6, 'GRAPHICS CARDS'),
        'psu': get_data_from_col(raw_df, 9, 'POWER SUPPLIES'),
        'case': get_data_from_col(raw_df, 12, 'CASES'),
        'st':   get_data_from_col(raw_df, 15, 'INTERNAL STORAGE')
    }
    
    st.title("Technodel Smart Builder")

    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()], key="c")
        
        mb_options = dfs['mb']
        if "Select" not in cpu_choice:
            mb_options = mb_options[mb_options['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_options.iterrows()], key="m")
        
        # RAM LOGIC: Find the RAM column (likely column index 18) and find sub-header
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            # Assuming RAMS are in Column S (Index 18) based on your layout
            ram_df = get_data_from_col(raw_df, 18, tech)
            
            if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
            for i in range(st.session_state.ram_count):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_df.iterrows()], key=f"ram_{i}")
            if st.button("➕ Add RAM"): st.session_state.ram_count += 1; st.rerun()

    with col2:
        gpu_choice = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['gpu'].iterrows()], key="g")
        psu_choice = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['psu'].iterrows()], key="p")
        case_choice = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['case'].iterrows()], key="ca")
        
        st.divider()
        if 'st_count' not in st.session_state: st.session_state.st_count = 1
        for i in range(st.session_state.st_count):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['st'].iterrows()], key=f"st_{i}")
        if st.button("➕ Add Storage"): st.session_state.st_count += 1; st.rerun()

    # --- TOTALS ---
    total = 0
    summary = []
    for k, lab in [('c','CPU'), ('m','MB'), ('g','GPU'), ('p','PSU'), ('ca','Case')]:
        v = st.session_state.get(k)
        if v and "Select" not in v:
            total += int(v.split(" - $")[1].replace(",",""))
            summary.append(f"{lab}: {v}")
    
    st.divider()
    if total > 0:
        st.header(f"Total: ${total:,}")
        for s in summary: st.write(s)
