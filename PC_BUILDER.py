import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re
import urllib.parse
from fpdf import FPDF

# --- 1. CONFIG & RESET LOGIC ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# This 'form_id' is the secret. Changing it forces Streamlit to rebuild all menus.
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

st.markdown("""
    <style>
    .build-box { border: 1px solid rgba(0, 168, 232, 0.3); padding: 25px; border-radius: 15px; background: #f0f8ff; color: #1a1a1a; }
    .build-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
    .total-row { margin-top: 15px; font-size: 24px; font-weight: bold; color: #00a8e8; text-align: right; }
    .social-link { display: block; padding: 10px; margin: 5px 0; text-decoration: none; color: #333; border-radius: 5px; background: #f1f1f1; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=300)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        return pd.read_csv(BytesIO(res.content), header=None)
    except: return pd.DataFrame()

def get_items_from_col(df, col_idx, start_title, stop_at_next_header=True, exclude_laptop=False):
    data = []
    found = False
    headers = ["PROCESSORS", "CPU COOLERS", "CASES", "MOTHER BOARDS", "INTERNAL STORAGE", "RAMS", "DDR3", "DDR4", "DDR5", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]
    for i in range(len(df)):
        cell_val = str(df.iloc[i, col_idx]).strip().upper()
        if not found:
            if cell_val == start_title.upper(): found = True
            continue
        if found:
            if stop_at_next_header and cell_val in headers: break
            name = str(df.iloc[i, col_idx]).strip()
            if not name or name.lower() == "nan": continue
            if exclude_laptop and "LAPTOP" in name.upper(): continue
            try:
                price_raw = str(df.iloc[i, col_idx + 1]).replace('$','').replace(',','').strip()
                if price_raw and price_raw.lower() != "nan":
                    data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
            except: continue
    return pd.DataFrame(data)

# --- 3. INTERFACE ---
raw_df = load_all_data()

if not raw_df.empty:
    with st.sidebar:
        st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=200)
        # HARD RESET BUTTON
        if st.button("🔄 Reset Build", use_container_width=True):
            st.session_state.form_id += 1  # Changing this forces all keys to change
            st.rerun()
        st.info("🛡️ 1 Year Hardware Warranty")

    # Categories
    cpu_df = get_items_from_col(raw_df, 0, 'PROCESSORS')
    mb_df  = get_items_from_col(raw_df, 3, 'MOTHER BOARDS')
    gpu_df = get_items_from_col(raw_df, 9, 'GRAPHICS CARDS')
    
    fid = st.session_state.form_id # Our unique version ID

    st.title("Technodel PC Builder Pro")
    col1, col2 = st.columns(2)
    
    with col1:
        # Every key now includes the form_id. If form_id changes, the widget is DELETED and remade.
        cpu_c = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key=f"cpu_{fid}")
        mb_c = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_df.iterrows()], key=f"mb_{fid}")
        
    with col2:
        gpu_c = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key=f"gpu_{fid}")

    # --- 4. SUMMARY & PDF ---
    st.divider()
    total = 0
    summary_txt = "TECHNODEL QUOTATION\n"
    
    # Simple calculation check
    selected_parts = [cpu_c, mb_c, gpu_c]
    for p in selected_parts:
        if p != "Select":
            name, price = p.split(" - $")
            total += int(price.replace(",",""))
            summary_txt += f"- {name}: ${price}\n"

    if total > 0:
        st.markdown(f'<div class="build-box"><h3>Total: ${total:,}</h3></div>', unsafe_allow_html=True)
        
        # FIXING THE PDF CRASH
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=summary_txt)
        pdf.cell(0, 10, txt=f"TOTAL: ${total:,}", ln=True)
        
        # This is the magic line that fixes the Streamlit error:
        # We output to a string 'S', then encode to latin-1 bytes.
        pdf_output = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📄 Download PDF",
            data=pdf_output,
            file_name="Technodel_Quote.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        wa_url = f"https://wa.me/9613659872?text={urllib.parse.quote(summary_txt + f'TOTAL: ${total}')}"
        st.link_button("🟢 WhatsApp Order", wa_url, use_container_width=True)
