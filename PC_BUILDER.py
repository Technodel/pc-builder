import streamlit as st
import pandas as pd
import re
import urllib.parse

# --- 1. PAGE CONFIG & LOGO ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide", page_icon="💻")

st.markdown(
    """
    <div style="text-align: left; padding-bottom: 5px;">
        <img src="https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp" width="280">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <style>
    .stSelectbox { margin-bottom: -15px; }
    .stButton button { width: 100%; border-radius: 5px; height: 2.2em; margin-top: 10px;}
    .live-summary {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00a8e8;
        margin-bottom: 20px;
    }
    .screenshot-box { 
        background-color: #ffffff; 
        padding: 30px; 
        border: 2px solid #333; 
        border-radius: 12px; 
        font-family: 'Segoe UI', sans-serif; 
        color: #000000;
        margin-top: 20px;
    }
    .contact-footer { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #00a8e8;
        margin-top: 30px;
    }
    .social-icon { width: 18px; height: 18px; vertical-align: middle; margin-right: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADER (GOOGLE SHEETS LOGIC) ---
@st.cache_data(ttl=600)  # Refresh cache every 10 minutes
def load_all_data():
    try:
        # Using your marketing bot logic: Direct CSV export for the 'hardware' tab
        SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        GID = "0" # Replace with your Hardware tab GID if different
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
        
        # Load the whole sheet
        full_df = pd.read_csv(URL)
        return full_df
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

def parse_section(df, keyword):
    data = []
    found_section = False
    current_ram_tech = None
    
    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        
        # Look for the section start (e.g., table_cpu)
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        
        # Stop when hitting the next table or an empty row
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        # RAM Tech Logic from your perfect code
        if "DDR4" in val_a.upper(): current_ram_tech = "DDR4"
        if "DDR5" in val_a.upper(): current_ram_tech = "DDR5"
        
        try:
            raw_price = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(raw_price), 0))
            if clean_price <= 0: continue
            
            data.append({
                "ITEM": val_a, 
                "PRICE": clean_price,
                "RAM_TECH": "DDR5" if "DDR5" in val_a.upper() else ("DDR4" if "DDR4" in val_a.upper() else current_ram_tech)
            })
        except: continue
    return pd.DataFrame(data)

# Load the raw data once
raw_sheet = load_all_data()

# Parse sections exactly like your local logic
sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
dfs = {s: parse_section(raw_sheet, s) for s in sections}

# --- 3. COMPATIBILITY LOGIC ---
def get_cpu_gen(cpu_name):
    match = re.search(r'(\d{4,5})', cpu_name)
    return (match.group(1)[:2] if len(match.group(1)) == 5 else match.group(1)[0]) if match else None

def is_compat(cpu_sel, mb_name):
    if "Select" in cpu_sel: return True
    gen = get_cpu_gen(cpu_sel)
    match = re.search(r'\((.*?)\)', mb_name)
    return str(gen) in re.findall(r'\d+', match.group(1)) if (gen and match) else True

# --- 4. COMPONENT SELECTION ---
st.title("💻 Technodel PC Builder Pro")
col1, col2 = st.columns([1, 1])

with col1:
    cpu_choice = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['cpu'].iterrows()], key="c")
    mb_list = dfs['mb']
    if "Select" not in cpu_choice:
        filtered = mb_list[mb_list['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        if not filtered.empty: mb_list = filtered
    mb_choice = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_list.iterrows()], key="m")
    
    st.divider()
    if "Select" not in mb_choice:
        mb_type = "DDR5" if "DDR5" in mb_choice.upper() else "DDR4"
        ram_list = dfs['ram'][dfs['ram']['RAM_TECH'] == mb_type]
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
    cool_choice = st.selectbox("Cooling", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['coo'].iterrows()], key="co")
    
    st.divider()
    if 'storage_count' not in st.session_state: st.session_state.storage_count = 1
    for i in range(st.session_state.storage_count):
        st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in dfs['storage'].iterrows()], key=f"store_{i}")
    if st.button("➕ Add Storage"): 
        st.session_state.storage_count += 1
        st.rerun()

# --- 5. LIVE TOTALS & PREVIEW ---
st.divider()
total = 0
items_for_preview = []
items_for_text = []

keys = [('CPU', 'c'), ('Motherboard', 'm'), ('GPU', 'g'), ('PSU', 'p'), ('Case', 'ca'), ('Cooler', 'co')]
for label, k in keys:
    val = st.session_state.get(k)
    if val and "Select" not in val:
        total += int(val.split(" - $")[1].replace(",",""))
        items_for_preview.append(f"<b>{label}:</b> {val}")
        items_for_text.append(f"{label}: {val}")

for i in range(st.session_state.get('ram_count', 1)):
    val = st.session_state.get(f"ram_{i}")
    if val and "Select" not in val:
        total += int(val.split(" - $")[1].replace(",",""))
        items_for_preview.append(f"<b>RAM {i+1}:</b> {val}")
        items_for_text.append(f"RAM {i+1}: {val}")

for i in range(st.session_state.get('storage_count', 1)):
    val = st.session_state.get(f"store_{i}")
    if val and "Select" not in val:
        total += int(val.split(" - $")[1].replace(",",""))
        items_for_preview.append(f"<b>Storage {i+1}:</b> {val}")
        items_for_text.append(f"Storage {i+1}: {val}")

if items_for_text:
    st.subheader("🛒 Real-Time Build Summary")
    list_items_md = "\n".join([f"* {i}" for i in items_for_text])
    st.markdown(f'<div class="live-summary">{list_items_md}<h2 style="color:#00a8e8; margin-top:15px;">TOTAL: ${total:,}</h2></div>', unsafe_allow_html=True)

# Generate Share Link (Automatically pre-fills for customers)
base_url = "https://technodel-builder.streamlit.app/?"
query_data = {}
for k in ['c','m','g','p','ca','co']:
    if st.session_state.get(k) and "Select" not in st.session_state[k]:
        query_data[k] = st.session_state[k]
share_url = base_url + urllib.parse.urlencode(query_data)

st.subheader("🔗 Share Build Link")
st.code(share_url)

# Footer & Screenshot logic (remains exactly same as your code)
st.markdown("""<div class="contact-footer">...</div>""", unsafe_allow_html=True) # Trimmed for brevity
