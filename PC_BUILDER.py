import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# --- 2. OFFLINE LOGIC (REPRODUCED EXACTLY) ---
def get_cpu_gen(cpu_name):
    # Logic: 5 digits = first 2 (12th gen), 4 digits = first 1 (6th gen)
    match = re.search(r'(\d{4,5})', cpu_name)
    if match:
        val = match.group(1)
        return val[:2] if len(val) == 5 else val[0]
    return None

def is_compat(cpu_sel, mb_name):
    # Matches CPU gen to parentheses in MB name: e.g. 'H610 (12,13,14)'
    if "Select" in cpu_sel: return True
    gen = get_cpu_gen(cpu_sel)
    match = re.search(r'\((.*?)\)', mb_name)
    if gen and match:
        allowed_gens = re.findall(r'\d+', match.group(1))
        return str(gen) in allowed_gens
    return True

# --- 3. OPTIMIZED DATA LOADER ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_component_data(df, title):
    """Finds exact section header and grabs name + price below it."""
    # Find header coordinates
    mask = df.apply(lambda s: s.astype(str).str.contains(rf"^{title}$", case=False, na=False))
    matches = mask.stack()
    if not matches.empty:
        row_idx, col_idx = matches.index[0]
        data = []
        # Start reading below header
        for i in range(row_idx + 1, len(df)):
            name = str(df.iloc[i, col_idx]).strip()
            # Stop if cell is empty or hits another major category header
            if not name or name == "nan" or any(h in name.upper() for h in ["PROCESSORS", "MOTHER", "DDR", "PRICE"]):
                if len(data) > 0: break
                continue
            try:
                price_val = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                data.append({"ITEM": name, "PRICE": int(round(float(price_val), 0))})
            except: continue
        return pd.DataFrame(data)
    return pd.DataFrame()

# --- 4. APP LOGIC ---
raw_df = load_all_data()

if not raw_df.empty:
    cats = {
        'cpu': 'PROCESSORS', 'mb': 'MOTHER BOARDS', 'gpu': 'GRAPHICS CARDS',
        'psu': 'POWER SUPPLIES', 'case': 'CASES', 'coo': 'CPU COOLERS',
        'storage': 'INTERNAL STORAGE', 'ups': 'UPS'
    }
    dfs = {k: find_component_data(raw_df, v) for k, v in cats.items()}
    
    # Pre-load ALL 3 RAM Tables
    ram_tables = {
        "DDR3": find_component_data(raw_df, "DDR3"),
        "DDR4": find_component_data(raw_df, "DDR4"),
        "DDR5": find_component_data(raw_df, "DDR5")
    }

    # --- 5. UI LAYOUT ---
    st.header("Technodel Online Builder")
    
    col1, col2 = st.columns(2)
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()], key="c")
        
        mb_options = dfs['mb']
        if "Select" not in cpu_choice:
            mb_options = mb_options[mb_options['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_options.iterrows()], key="m")
        
        st.divider()
        # DYNAMIC RAM FILTERING
        if "Select" not in mb_choice:
            # Determine RAM tech from board name
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            active_ram_df = ram_tables.get(tech, pd.DataFrame())
            
            if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
            for i in range(st.session_state.ram_count):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in active_ram_df.iterrows()], key=f"ram_{i}")
            
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

    # --- 6. REAL-TIME TOTALS & PREVIEW ---
    st.divider()
    total = 0
    preview_items = []

    # Compile parts from session state
    for label, key in [('CPU', 'c'), ('Motherboard', 'm'), ('GPU', 'g'), ('PSU', 'p'), ('Case', 'ca')]:
        val = st.session_state.get(key)
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            preview_items.append(f"**{label}:** {val}")

    for i in range(st.session_state.get('ram_count', 1)):
        val = st.session_state.get(f"ram_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            preview_items.append(f"**RAM {i+1}:** {val}")

    for i in range(st.session_state.get('storage_count', 1)):
        val = st.session_state.get(f"store_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            preview_items.append(f"**Storage {i+1}:** {val}")

    if preview_items:
        st.subheader("🛒 Build Summary")
        for item in preview_items: st.write(item)
        st.header(f"TOTAL: ${total:,}")
