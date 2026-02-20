import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# --- 2. THE OFFLINE LOGIC (RESTORED EXACTLY) ---
def get_cpu_gen(cpu_name):
    # Logic: 5 digits (12700) -> 12, 4 digits (6500) -> 6
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

# --- 3. FIX: PRECISE DATA EXTRACTION ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_component_data(df, title):
    """Finds exact section header and stops ONLY at empty rows."""
    # Search for title in entire sheet
    mask = df.apply(lambda s: s.astype(str).str.strip().str.upper() == title.upper())
    matches = mask.stack()
    if not matches.empty:
        row_idx, col_idx = matches.index[0]
        data = []
        # Start reading below header
        for i in range(row_idx + 1, len(df)):
            name = str(df.iloc[i, col_idx]).strip()
            # STOP ONLY IF CELL IS EMPTY (Solves the 'Only Processors' bug)
            if not name or name.lower() == "nan" or name == "":
                break
            try:
                price_val = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                data.append({"ITEM": name, "PRICE": int(round(float(price_val), 0))})
            except: continue
        return pd.DataFrame(data)
    return pd.DataFrame()

# --- 4. APP LOGIC ---
raw_df = load_all_data()

if not raw_df.empty:
    # Use exact headers from your columns A, D, G, J
    cats = {
        'cpu': 'PROCESSORS', 'mb': 'MOTHER BOARDS', 'gpu': 'GRAPHICS CARDS',
        'psu': 'POWER SUPPLIES', 'case': 'CASES', 'coo': 'CPU COOLERS',
        'storage': 'INTERNAL STORAGE', 'ups': 'UPS'
    }
    dfs = {k: find_component_data(raw_df, v) for k, v in cats.items()}
    
    # Pre-load RAM Tables specifically
    ram_tables = {
        "DDR3": find_component_data(raw_df, "DDR3"),
        "DDR4": find_component_data(raw_df, "DDR4"),
        "DDR5": find_component_data(raw_df, "DDR5")
    }

    # --- 5. UI LAYOUT ---
    st.title("Technodel Smart Builder")
    st.info("✅ 1 Year Warranty | 🚀 Ready for pickup within 24 hours")
    
    col1, col2 = st.columns(2)
    with col1:
        # Processor
        cpu_options = [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()]
        cpu_choice = st.selectbox("Processor", ["Select"] + cpu_options, key="c")
        
        # Motherboard (Filtered)
        mb_options = dfs['mb']
        if "Select" not in cpu_choice:
            mb_options = mb_options[mb_options['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_options.iterrows()], key="m")
        
        st.divider()
        # RAM Tech Logic
        if "Select" not in mb_choice:
            tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR3" if "DDR3" in mb_choice.upper() else "DDR4"
            active_ram_df = ram_tables.get(tech, pd.DataFrame())
            
            if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
            for i in range(st.session_state.ram_count):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in active_ram_df.iterrows()], key=f"ram_{i}")
            
            if st.button("➕ Add RAM"):
                st.session_state.ram_count += 1; st.rerun()

    with col2:
        # Other Components
        gpu_choice = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['gpu'].iterrows()], key="g")
        psu_choice = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['psu'].iterrows()], key="p")
        case_choice = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['case'].iterrows()], key="ca")
        cool_choice = st.selectbox("Cooling", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['coo'].iterrows()], key="co")
        
        st.divider()
        # Multi-Storage [cite: 2026-02-19]
        if 'storage_count' not in st.session_state: st.session_state.storage_count = 1
        for i in range(st.session_state.storage_count):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['storage'].iterrows()], key=f"store_{i}")
        if st.button("➕ Add Storage"):
            st.session_state.storage_count += 1; st.rerun()

    # --- 6. TOTALS ---
    st.divider()
    total = 0
    summary = []

    # Iterate through session state to calculate total
    for key, label in [('c', 'CPU'), ('m', 'Motherboard'), ('g', 'GPU'), ('p', 'PSU'), ('ca', 'Case'), ('co', 'Cooling')]:
        val = st.session_state.get(key)
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            summary.append(f"**{label}:** {val}")

    # Add RAM & Storage
    for i in range(st.session_state.get('ram_count', 1)):
        val = st.session_state.get(f"ram_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            summary.append(f"**RAM {i+1}:** {val}")

    for i in range(st.session_state.get('storage_count', 1)):
        val = st.session_state.get(f"store_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",", ""))
            summary.append(f"**Storage {i+1}:** {val}")

    if summary:
        st.subheader("🛒 Build Summary")
        for item in summary: st.write(item)
        st.header(f"TOTAL: ${total:,}")

else:
    st.error("Sheet Connection Error. Check public sharing on GID 1309359556.")
