import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG & LOGIC ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

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

# --- 2. THE ERROR-PROOF GRABBER ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_section(df, title, is_ram_sub=False):
    """Dynamically finds a header and pulls Name/Price until an empty row."""
    # Find coordinates of the title
    mask = df.apply(lambda s: s.astype(str).str.strip().str.upper() == title.upper())
    matches = mask.stack()
    if matches.empty: return pd.DataFrame()
    
    row_idx, col_idx = matches.index[0]
    data = []
    
    # Read downwards from the header
    for i in range(row_idx + 1, len(df)):
        try:
            name = str(df.iloc[i, col_idx]).strip()
            # Stop if empty or if we hit a different DDR section while looking for RAM
            if not name or name.lower() == "nan" or (is_ram_sub and "DDR" in name.upper() and name.upper() != title.upper()):
                break
            
            # Check if next column (Price) exists to avoid IndexError
            if col_idx + 1 < len(df.columns):
                price_raw = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                price = int(round(float(price_raw), 0))
                data.append({"ITEM": name, "PRICE": price})
        except: continue
        
    return pd.DataFrame(data)

# --- 3. APP EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # We hunt for headers wherever they moved to
    cats = {
        'cpu': find_section(raw_df, 'PROCESSORS'),
        'mb':  find_section(raw_df, 'MOTHER BOARDS'),
        'gpu': find_section(raw_df, 'GRAPHICS CARDS'),
        'psu': find_section(raw_df, 'POWER SUPPLIES'),
        'ca':  find_section(raw_df, 'CASES'),
        'st':  find_section(raw_df, 'INTERNAL STORAGE')
    }
    
    st.title("Technodel Smart Builder")

    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cats['cpu'].iterrows()], key="c")
        
        mb_list = cats['mb']
        if "Select" not in cpu_choice:
            mb_list = mb_list[mb_list['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_list.iterrows()], key="m")
        
        # RAM Tech Filter
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            ram_df = find_section(raw_df, tech, is_ram_sub=True)
            
            if 'r_cnt' not in st.session_state: st.session_state.r_cnt = 1
            for i in range(st.session_state.r_cnt):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_df.iterrows()], key=f"r_{i}")
            if st.button("➕ RAM"): st.session_state.r_cnt += 1; st.rerun()

    with col2:
        # Standard Selects
        gpu = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cats['gpu'].iterrows()], key="g")
        psu = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cats['psu'].iterrows()], key="p")
        cas = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cats['ca'].iterrows()], key="ca_sel")
        
        if 's_cnt' not in st.session_state: st.session_state.s_cnt = 1
        for i in range(st.session_state.s_cnt):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cats['st'].iterrows()], key=f"s_{i}")
        if st.button("➕ Storage"): st.session_state.s_cnt += 1; st.rerun()

    # --- 4. SUMMARY & CALC ---
    total = 0
    # Add standard selections
    for k in ['c', 'm', 'g', 'p', 'ca_sel']:
        v = st.session_state.get(k)
        if v and "Select" not in v: total += int(v.split(" - $")[1].replace(",", ""))
    
    # Add dynamic RAM/Storage
    for i in range(st.session_state.get('r_cnt', 1)):
        v = st.session_state.get(f"r_{i}")
        if v and "Select" not in v: total += int(v.split(" - $")[1].replace(",", ""))
        
    for i in range(st.session_state.get('s_cnt', 1)):
        v = st.session_state.get(f"s_{i}")
        if v and "Select" not in v: total += int(v.split(" - $")[1].replace(",", ""))

    if total > 0:
        st.divider()
        st.header(f"Total: ${total:,}")
