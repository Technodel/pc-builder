import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG ---
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

# --- 3. THE COLUMN-AWARE GRABBER ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def get_items_from_col(df, col_idx, start_title, stop_at_next_header=True):
    """Finds title in a specific column and grabs items until next green header."""
    data = []
    found = False
    # Known green headers in your sheet to stop at
    headers = ["PROCESSORS", "CPU COOLERS", "CASES", "MOTHER BOARDS", "INTERNAL STORAGE", "RAMS", "DDR3", "DDR4", "DDR5", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]
    
    for i in range(len(df)):
        cell_val = str(df.iloc[i, col_idx]).strip().upper()
        
        if not found:
            if cell_val == start_title.upper():
                found = True
            continue
        
        # If we are in the section
        if found:
            # Stop if we hit another header in the same column
            if stop_at_next_header and cell_val in headers:
                break
            
            name = str(df.iloc[i, col_idx]).strip()
            # Skip empty rows or "nan"
            if not name or name.lower() == "nan" or name == "":
                continue
                
            try:
                price_raw = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                if price_raw and price_raw.lower() != "nan":
                    data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
            except: continue
            
    return pd.DataFrame(data)

# --- 4. DATA PROCESSING ---
raw_df = load_all_data()

if not raw_df.empty:
    # Mapped exactly to your Google Sheet Columns
    # Column A (0): PROCESSORS, CPU COOLERS, CASES
    # Column D (3): MOTHER BOARDS, INTERNAL STORAGE
    # Column G (6): RAMS (DDR3, DDR4, DDR5)
    # Column J (9): POWER SUPPLIES, GRAPHICS CARDS, UPS
    
    cpu_df = get_items_from_col(raw_df, 0, 'PROCESSORS')
    coo_df = get_items_from_col(raw_df, 0, 'CPU COOLERS')
    cas_df = get_items_from_col(raw_df, 0, 'CASES')
    
    mb_df  = get_items_from_col(raw_df, 3, 'MOTHER BOARDS')
    st_df  = get_items_from_col(raw_df, 3, 'INTERNAL STORAGE')
    
    psu_df = get_items_from_col(raw_df, 9, 'POWER SUPPLIES')
    gpu_df = get_items_from_col(raw_df, 9, 'GRAPHICS CARDS')
    ups_df = get_items_from_col(raw_df, 9, 'UPS')

    st.title("Technodel PC Builder")

    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key="c")
        mb_list = mb_df[mb_df['ITEM'].apply(lambda x: is_compat(cpu_choice, x))] if "Select" not in cpu_choice else mb_df
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_list.iterrows()], key="m")
        
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            ram_df = get_items_from_col(raw_df, 6, tech)
            if 'r_cnt' not in st.session_state: st.session_state.r_cnt = 1
            for i in range(st.session_state.r_cnt):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_df.iterrows()], key=f"r_{i}")
            if st.button("➕ Add RAM"): st.session_state.r_cnt += 1; st.rerun()

    with col2:
        st.selectbox("Graphics Card", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key="g")
        st.selectbox("Power Supply", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in psu_df.iterrows()], key="p")
        st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cas_df.iterrows()], key="ca")
        st.selectbox("Cooler", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in coo_df.iterrows()], key="co")
        
        if 's_cnt' not in st.session_state: st.session_state.s_cnt = 1
        for i in range(st.session_state.s_cnt):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in st_df.iterrows()], key=f"s_{i}")
        if st.button("➕ Add Storage"): st.session_state.s_cnt += 1; st.rerun()

    # --- TOTALS ---
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
        st.header(f"Total Price: ${total:,}")
