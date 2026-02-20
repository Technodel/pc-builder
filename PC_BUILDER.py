import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# --- 2. INTEL GEN LOGIC ---
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

# --- 3. THE "STACKED" DATA GRABBER ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_stacked_section(df, title, is_ram_sub=False):
    """Finds a header and reads until the next category header or empty price."""
    mask = df.apply(lambda s: s.astype(str).str.strip().str.upper() == title.upper())
    matches = mask.stack()
    if matches.empty: return pd.DataFrame()
    
    row_idx, col_idx = matches.index[0]
    data = []
    
    # Major headers that indicate we should stop reading current section
    stops = ["PROCESSORS", "CPU COOLERS", "CASES", "MOTHER BOARDS", "INTERNAL STORAGE", "RAMS", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]
    
    for i in range(row_idx + 1, len(df)):
        name = str(df.iloc[i, col_idx]).strip()
        
        # 1. Skip strictly empty cells
        if not name or name.lower() == "nan" or name == "": continue
        
        # 2. Stop if we hit a DIFFERENT major header (stacked below)
        if name.upper() in stops and name.upper() != title.upper(): break
        
        # 3. RAM Sub-sections stop if they hit a different DDR title
        if is_ram_sub and "DDR" in name.upper() and name.upper() != title.upper(): break

        try:
            price_raw = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
            # If price is missing or not a number, skip this row
            if not price_raw or price_raw.lower() == "nan": continue
            data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
        except: continue
        
    return pd.DataFrame(data)

# --- 4. APP EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # Hunt for every section precisely as shown in image_e33455.jpg
    cpu_df = find_stacked_section(raw_df, 'PROCESSORS')
    coo_df = find_stacked_section(raw_df, 'CPU COOLERS')
    cas_df = find_stacked_section(raw_df, 'CASES')
    mb_df  = find_stacked_section(raw_df, 'MOTHER BOARDS')
    st_df  = find_stacked_section(raw_df, 'INTERNAL STORAGE')
    psu_df = find_stacked_section(raw_df, 'POWER SUPPLIES')
    gpu_df = find_stacked_section(raw_df, 'GRAPHICS CARDS')
    ups_df = find_stacked_section(raw_df, 'UPS')

    st.title("Technodel Smart Builder")

    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key="c")
        mb_list = mb_df[mb_df['ITEM'].apply(lambda x: is_compat(cpu_choice, x))] if "Select" not in cpu_choice else mb_df
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_list.iterrows()], key="m")
        
        # RAM Logic using DDR3/4/5 headers
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            ram_df = find_stacked_section(raw_df, tech, is_ram_sub=True)
            if 'r_cnt' not in st.session_state: st.session_state.r_cnt = 1
            for i in range(st.session_state.r_cnt):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_df.iterrows()], key=f"r_{i}")
            if st.button("➕ RAM"): st.session_state.r_cnt += 1; st.rerun()

    with col2:
        st.selectbox("Graphics Card", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key="g")
        st.selectbox("Power Supply", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in psu_df.iterrows()], key="p")
        st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cas_df.iterrows()], key="ca")
        st.selectbox("Cooler", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in coo_df.iterrows()], key="co")
        
        if 's_cnt' not in st.session_state: st.session_state.s_cnt = 1
        for i in range(st.session_state.s_cnt):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in st_df.iterrows()], key=f"s_{i}")
        if st.button("➕ Storage"): st.session_state.s_cnt += 1; st.rerun()

    # --- 5. TOTALS ---
    total = 0
    for k in ['c', 'm', 'g', 'p', 'ca', 'co']:
        v = st.session_state.get(k)
        if v and "Select" not in v: total += int(v.split(" - $")[1].replace(",", ""))
    
    for i in range(st.session_state.get('r_cnt', 1)):
        v = st.session_state.get(f"r_{i}"); total += int(v.split(" - $")[1].replace(",", "")) if v and "Select" not in v else 0
        
    for i in range(st.session_state.get('s_cnt', 1)):
        v = st.session_state.get(f"s_{i}"); total += int(v.split(" - $")[1].replace(",", "")) if v and "Select" not in v else 0

    if total > 0:
        st.divider()
        st.header(f"Total: ${total:,}")
