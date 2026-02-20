import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re
import urllib.parse

# --- 1. RESET ENGINE ---
if 'rid' not in st.session_state:
    st.session_state.rid = 0

def hard_reset():
    st.session_state.rid += 1
    # We DON'T clear r_cnt or s_cnt so the buttons/rows stay visible
    # We only clear the selections
    for key in list(st.session_state.keys()):
        if key not in ['rid', 'r_cnt', 's_cnt']:
            del st.session_state[key]

# --- 2. CONFIG & STYLING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

st.markdown("""
    <style>
    .build-box { 
        border: 1px solid #00a8e8; 
        padding: 20px; 
        border-radius: 10px; 
        background: #f0faff;
    }
    .build-item {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        border-bottom: 1px solid #ddd;
    }
    .total-row {
        font-size: 22px;
        font-weight: bold;
        color: #00a8e8;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=300)
def load_all_data():
    url = "https://docs.google.com/spreadsheets/d/1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4/export?format=csv&gid=1309359556"
    try:
        res = requests.get(url, timeout=10)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def get_items_from_col(df, col_idx, start_title):
    data = []
    found = False
    headers = ["PROCESSORS", "CPU COOLERS", "CASES", "MOTHER BOARDS", "INTERNAL STORAGE", "RAMS", "DDR3", "DDR4", "DDR5", "POWER SUPPLIES", "GRAPHICS CARDS"]
    for i in range(len(df)):
        cell_val = str(df.iloc[i, col_idx]).strip().upper()
        if not found:
            if cell_val == start_title.upper(): found = True
            continue
        if found:
            if cell_val in headers: break
            name = str(df.iloc[i, col_idx]).strip()
            if not name or name.lower() == "nan": continue
            try:
                price = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                data.append({"ITEM": name, "PRICE": int(float(price))})
            except: continue
    return pd.DataFrame(data)

# --- 4. APP INTERFACE ---
raw_df = load_all_data()

if not raw_df.empty:
    rid = st.session_state.rid
    
    with st.sidebar:
        st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=180)
        st.button("🔄 Reset Selections", on_click=hard_reset, use_container_width=True)
        st.divider()
        st.write("📞 70 449900")

    # Load categories
    cpu_df = get_items_from_col(raw_df, 0, 'PROCESSORS')
    mb_df  = get_items_from_col(raw_df, 3, 'MOTHER BOARDS')
    gpu_df = get_items_from_col(raw_df, 9, 'GRAPHICS CARDS')
    st_df  = get_items_from_col(raw_df, 3, 'INTERNAL STORAGE')

    st.title("Technodel PC Builder Pro")

    col1, col2 = st.columns(2)
    with col1:
        cpu_c = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key=f"c_{rid}")
        mb_c = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_df.iterrows()], key=f"m_{rid}")
        
        if 'r_cnt' not in st.session_state: st.session_state.r_cnt = 1
        for i in range(st.session_state.r_cnt):
            st.selectbox(f"RAM {i+1}", ["Select"] + ["8GB DDR4 - $30", "16GB DDR4 - $55"], key=f"r_{i}_{rid}")
        if st.button("➕ Add RAM"): 
            st.session_state.r_cnt += 1
            st.rerun()

    with col2:
        gpu_c = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key=f"g_{rid}")
        
        if 's_cnt' not in st.session_state: st.session_state.s_cnt = 1
        for i in range(st.session_state.s_cnt):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in st_df.iterrows()], key=f"s_{i}_{rid}")
        if st.button("➕ Add Storage"): 
            st.session_state.s_cnt += 1
            st.rerun()

    # --- 5. SUMMARY & TXT DOWNLOAD ---
    st.divider()
    total = 0
    items_text = "TECHNODEL PC QUOTE\n" + "-"*20 + "\n"
    html_items = ""

    # Check selections
    all_keys = [f'c_{rid}', f'm_{rid}', f'g_{rid}']
    all_keys += [f'r_{i}_{rid}' for i in range(st.session_state.r_cnt)]
    all_keys += [f's_{i}_{rid}' for i in range(st.session_state.s_cnt)]

    for k in all_keys:
        val = st.session_state.get(k)
        if val and val != "Select":
            name, price = val.split(" - $")
            total += int(price)
            items_text += f"{val}\n"
            html_items += f'<div class="build-item"><span>{name}</span><b>${price}</b></div>'

    if total > 0:
        st.subheader("Build Summary")
        st.markdown(f'<div class="build-box">{html_items}<div class="total-row">Total: ${total}</div></div>', unsafe_allow_html=True)
        
        items_text += f"\nTOTAL: ${total}"
        
        c1, c2 = st.columns(2)
        with c1:
            # SAVE AS TXT
            st.download_button(
                label="📄 Save as Text File",
                data=items_text,
                file_name="Technodel_Quote.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c2:
            wa_url = f"https://wa.me/96170449900?text={urllib.parse.quote(items_text)}"
            st.link_button("🟢 Order via WhatsApp", wa_url, use_container_width=True)
