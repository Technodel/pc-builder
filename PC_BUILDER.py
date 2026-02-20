import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# Sidebar with Contact & Socials
with st.sidebar:
    st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=200)
    st.title("Contact Information")
    st.write("📞 03659872 | 70449900")
    st.write("📞 71234002 | 07345689")
    st.write("📧 Adarwich@engineer.com")
    st.divider()
    st.write("🌐 [Technodel.net](https://technodel.net)")
    st.write("📸 [Instagram](https://instagram.com/technodel_computers)")
    st.write("🔵 [Facebook](https://fb.com/technodel)")
    st.write("🎵 [TikTok](https://tiktok.com/@technodel_computer)")

# --- 2. OFFLINE LOGIC (REPRODUCED EXACTLY) ---
def get_cpu_gen(cpu_name):
    match = re.search(r'(\d{4,5})', cpu_name)
    return (match.group(1)[:2] if len(match.group(1)) == 5 else match.group(1)[0]) if match else None

def is_compat(cpu_sel, mb_name):
    if "Select" in cpu_sel: return True
    gen = get_cpu_gen(cpu_sel)
    match = re.search(r'\((.*?)\)', mb_name)
    return str(gen) in re.findall(r'\d+', match.group(1)) if (gen and match) else True

# --- 3. DATA LOADER (MULTI-COLUMN SCANNER) ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def find_component_data(df, title):
    for col in df.columns:
        match = df[df[col].astype(str).str.contains(title, case=False, na=False)]
        if not match.empty:
            start_row = match.index[0] + 1
            data = []
            for i in range(start_row, len(df)):
                name = str(df.iloc[i, col]).strip()
                if not name or name == "nan" or any(h in name.upper() for h in ["PRICE", "PROCESSORS"]):
                    if len(data) > 0: break
                    continue
                try:
                    price = str(df.iloc[i, col+1]).replace('$','').replace(',','').strip()
                    # Custom RAM Tech detection for DDR4/DDR5 matching
                    tech = "DDR5" if "DDR5" in name.upper() else "DDR4"
                    data.append({"ITEM": name, "PRICE": int(round(float(price),0)), "RAM_TECH": tech})
                except: continue
            return pd.DataFrame(data)
    return pd.DataFrame()

# --- 4. DATA PROCESSING ---
raw_df = load_all_data()
if not raw_df.empty:
    titles = {
        'cpu': 'PROCESSORS', 'mb': 'MOTHER BOARDS', 'ram': 'RAMS',
        'gpu': 'GRAPHICS CARDS', 'psu': 'POWER SUPPLIES', 'case': 'CASES',
        'coo': 'CPU COOLERS', 'storage': 'INTERNAL STORAGE', 'ups': 'UPS'
    }
    dfs = {k: find_component_data(raw_df, v) for k, v in titles.items()}

    # --- 5. COMPONENT SELECTION INTERFACE ---
    st.header("Build Your Technodel PC")
    st.info("✅ 1 Year Warranty | 🚀 Ready for pickup within 24 hours")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()], key="c")
        
        # Smart Filtered Motherboard List
        mb_list = dfs['mb']
        if "Select" not in cpu_choice:
            mb_list = mb_list[mb_list['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_list.iterrows()], key="m")
        
        st.divider()
        # Multi-RAM Logic
        if "Select" not in mb_choice:
            mb_tech = "DDR5" if "DDR5" in mb_choice.upper() else "DDR4"
            ram_list = dfs['ram'][dfs['ram']['RAM_TECH'] == mb_tech]
            
            if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
            for i in range(st.session_state.ram_count):
                st.selectbox(f"RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_list.iterrows()], key=f"ram_{i}")
            
            if st.button("➕ Add RAM"): 
                st.session_state.ram_count += 1
                st.rerun()

    with col2:
        gpu_choice = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['gpu'].iterrows()], key="g")
        psu_choice = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['psu'].iterrows()], key="p")
        case_choice = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['case'].iterrows()], key="ca")
        
        st.divider()
        # Multi-Storage Logic
        if 'storage_count' not in st.session_state: st.session_state.storage_count = 1
        for i in range(st.session_state.storage_count):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['storage'].iterrows()], key=f"store_{i}")
        
        if st.button("➕ Add Storage"): 
            st.session_state.storage_count += 1
            st.rerun()

    # --- 6. LIVE TOTALS & SUMMARY ---
    st.divider()
    total = 0
    items_for_preview = []
    
    # Calculate regular parts
    keys = [('CPU', 'c'), ('Motherboard', 'm'), ('GPU', 'g'), ('PSU', 'p'), ('Case', 'ca')]
    for label, k in keys:
        val = st.session_state.get(k)
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",",""))
            items_for_preview.append(f"**{label}:** {val}")

    # Calculate multi-parts
    for i in range(st.session_state.get('ram_count', 1)):
        val = st.session_state.get(f"ram_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",",""))
            items_for_preview.append(f"**RAM {i+1}:** {val}")

    for i in range(st.session_state.get('storage_count', 1)):
        val = st.session_state.get(f"store_{i}")
        if val and "Select" not in val:
            total += int(val.split(" - $")[1].replace(",",""))
            items_for_preview.append(f"**Storage {i+1}:** {val}")

    if items_for_preview:
        st.subheader("🛒 Real-Time Build Summary")
        for item in items_for_preview: st.write(item)
        st.header(f"TOTAL: ${total:,}")
        
        # Download Quote
        quote_body = "\n".join(items_for_preview) + f"\n\nTOTAL: ${total:,}"
        st.download_button("💾 Download Quote", quote_body, "Technodel_Quote.txt")

else:
    st.error("Sheet Sync Failed. Please check headers in Columns A, D, G, J.")
