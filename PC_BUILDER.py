import streamlit as st
import pandas as pd
import openpyxl
import re
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Technodel Pro Builder", layout="wide", page_icon="💻")

st.markdown("""
    <style>
    .stSelectbox { margin-bottom: -15px; }
    .stButton button { width: 100%; border-radius: 5px; height: 2em; margin-top: 10px;}
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💻 Technodel Custom PC Builder")

# --- 2. FILE SELECTOR (NEW FEATURE) ---
def get_all_excel_files():
    # Scans the current folder for Excel files
    base_path = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(base_path) if f.endswith(('.xlsx', '.xlsm'))]
    
    if not files:
        return []
    
    # Sort files by last modified time (newest first)
    full_paths = [os.path.join(base_path, f) for f in files]
    full_paths.sort(key=os.path.getmtime, reverse=True)
    return [os.path.basename(p) for p in full_paths]

excel_options = get_all_excel_files()

if not excel_options:
    st.error("❌ No Excel files found in the folder!")
    st.stop()

# Dropdown for file selection, defaults to newest
selected_filename = st.selectbox("📂 Select Hardware Database (Showing newest first)", excel_options)
FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), selected_filename)

# --- 3. DATA LOADER (RE-OPTIMIZED) ---
@st.cache_data
def load_data(file_path, table_name):
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb["Hardware"]
        if table_name not in ws.tables:
            return pd.DataFrame(columns=['ITEM', 'PRICE', 'RAM_TECH'])
            
        target_table = ws.tables[table_name]
        table_range = ws[target_table.ref]
        
        data = []
        current_ram_tech = None 
        
        for row in table_range[1:]:
            item_name = str(row[0].value).strip() if row[0].value else ""
            price = row[1].value if len(row) > 1 else 0

            if item_name.upper() == "DDR4": current_ram_tech = "DDR4"; continue
            if item_name.upper() == "DDR5": current_ram_tech = "DDR5"; continue
            
            item_tech = current_ram_tech
            if not item_tech:
                if "DDR5" in item_name.upper(): item_tech = "DDR5"
                elif "DDR4" in item_name.upper(): item_tech = "DDR4"

            if item_name and item_name != "None":
                data.append({
                    "ITEM": item_name, 
                    "PRICE": float(price) if price else 0.0, 
                    "RAM_TECH": item_tech
                })
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame(columns=['ITEM', 'PRICE', 'RAM_TECH'])

# Load Hardware from selected file
cpu_df = load_data(FILE_PATH, "Table_cpu")
mb_df  = load_data(FILE_PATH, "Table_mb")
ram_df = load_data(FILE_PATH, "Table_ram")
gpu_df = load_data(FILE_PATH, "Table_gpu")
case_df = load_data(FILE_PATH, "Table_case")
psu_df = load_data(FILE_PATH, "Table_psu")
cool_df = load_data(FILE_PATH, "Table_coo")
storage_df = load_data(FILE_PATH, "Table_storage")

# --- 4. NEW GENERATION MATCHING LOGIC ---
def get_cpu_gen(cpu_name):
    match = re.search(r'(\d{4,5})', cpu_name)
    if match:
        num = match.group(1)
        return num[:2] if len(num) == 5 else num[0]
    return None

def is_compat(cpu_sel, mb_name):
    if "Select" in cpu_sel: return True
    gen = get_cpu_gen(cpu_sel)
    if not gen: return True
    
    # Extract numbers inside parentheses from the board name (e.g. 'H610 (12,13)')
    match = re.search(r'\((.*?)\)', mb_name)
    if match:
        gens_in_name = re.findall(r'\d+', match.group(1))
        return str(gen) in gens_in_name
    return False

# --- 5. UI LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Core Components")
    cpu_choice = st.selectbox("Select Processor (CPU)", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key="c")
    
    mb_display_list = mb_df.copy()
    if "Select" not in cpu_choice:
        gen_found = get_cpu_gen(cpu_choice)
        st.info(f"🔍 Filtering for Generation: **{gen_found}**")
        
        # Filter by looking at the parenthesis in the ITEM name
        filtered = mb_df[mb_df['ITEM'].apply(lambda x: is_compat(cpu_choice, x))]
        
        if not filtered.empty:
            mb_display_list = filtered
        else:
            st.warning(f"⚠️ No board found with '({gen_found})' in its name.")

    mb_choice = st.selectbox("Select Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_display_list.iterrows()], key="m")
    
    st.divider()
    st.write("**Memory (RAM)**")
    if "Select" in mb_choice:
        st.info("ℹ️ Select a Motherboard to unlock RAM.")
    else:
        mb_type = "DDR5" if "DDR5" in mb_choice.upper() else "DDR4"
        filtered_ram = ram_df[ram_df['RAM_TECH'] == mb_type]
        if filtered_ram.empty: filtered_ram = ram_df

        if 'ram_count' not in st.session_state: st.session_state.ram_count = 1
        for i in range(st.session_state.ram_count):
            st.selectbox(f"RAM Stick {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in filtered_ram.iterrows()], key=f"ram_{i}")
        
        if st.session_state.ram_count < 4:
            if st.button("➕ Add More RAM"):
                st.session_state.ram_count += 1
                st.rerun()

with col2:
    st.subheader("Graphics & Storage")
    gpu_choice = st.selectbox("Select GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key="g")
    psu_choice = st.selectbox("Select PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in psu_df.iterrows()], key="p")
    case_choice = st.selectbox("Select Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in case_df.iterrows()], key="ca")
    cool_choice = st.selectbox("Select Cooler", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cool_df.iterrows()], key="co")

    st.divider()
    st.write("**Storage**")
    if 'storage_count' not in st.session_state: st.session_state.storage_count = 1
    for i in range(st.session_state.storage_count):
        st.selectbox(f"Drive {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in storage_df.iterrows()], key=f"store_{i}")
    
    if st.session_state.storage_count < 4:
        if st.button("➕ Add More Storage"):
            st.session_state.storage_count += 1
            st.rerun()

# --- 6. PRICE CALCULATION ---
st.divider()
total = 0.0
build_details = f"--- BUILD SUMMARY ({selected_filename}) ---\n\n"

for label, k in [("CPU", 'c'), ("Motherboard", 'm'), ("GPU", 'g'), ("PSU", 'p'), ("Case", 'ca'), ("Cooler", 'co')]:
    val = st.session_state.get(k)
    if val and "Select" not in val:
        name_only = val.split(" - $")[0]
        price_val = float(val.split(" - $")[1].replace(",",""))
        total += price_val
        build_details += f"{label}: {name_only} (${price_val:,.2f})\n"

for i in range(st.session_state.get('ram_count', 1)):
    val = st.session_state.get(f"ram_{i}")
    if val and "Select" not in val:
        name_only = val.split(" - $")[0]
        price_val = float(val.split(" - $")[1].replace(",",""))
        total += price_val
        build_details += f"RAM {i+1}: {name_only} (${price_val:,.2f})\n"

for i in range(st.session_state.get('storage_count', 1)):
    val = st.session_state.get(f"store_{i}")
    if val and "Select" not in val:
        name_only = val.split(" - $")[0]
        price_val = float(val.split(" - $")[1].replace(",",""))
        total += price_val
        build_details += f"Storage {i+1}: {name_only} (${price_val:,.2f})\n"

build_details += f"\nTOTAL PRICE: ${total:,.2f}\n"

c1, c2 = st.columns([2, 1])
with c1:
    st.metric(label="Total Build Price", value=f"${total:,.2f}")
with c2:
    st.download_button(label="📥 Download Build (.txt)", data=build_details, file_name="pc_build.txt", mime="text/plain")

if st.button("Reset Builder"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()
