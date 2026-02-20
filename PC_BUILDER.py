import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import urllib.parse
import re

# --- 1. CONFIG & PREMIUM STYLING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide", page_icon="🖥️")

st.markdown("""
    <style>
    .build-box { 
        border: 1px solid rgba(0, 168, 232, 0.3); 
        padding: 25px; 
        border-radius: 15px; 
        background: linear-gradient(135deg, #ffffff 0%, #f0f8ff 100%);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        color: #1a1a1a;
    }
    .build-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    .total-row {
        margin-top: 15px;
        font-size: 24px;
        font-weight: bold;
        color: #00a8e8;
        text-align: right;
    }
    .social-link {
        display: block;
        padding: 10px;
        margin: 5px 0;
        text-decoration: none;
        color: #333;
        border-radius: 5px;
        background: #f1f1f1;
        transition: 0.3s;
    }
    .social-link:hover { background: #00a8e8; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC & HELPERS ---
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

def reset_build():
    """Wipes session state and restarts app"""
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

def generate_real_pdf(html_rows_text, total_val):
    """Generates a proper PDF document"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="TECHNODEL PC QUOTATION", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    # Clean up build items for PDF
    items = html_rows_text.replace('<span>', '').replace('</span>', '').replace('<b>', ' - ').replace('</b>', '').split('<div class="build-item">')
    for item in items:
        if item.strip():
            pdf.cell(0, 10, txt=item.strip(), ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=f"TOTAL: ${total_val:,}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. DATA ENGINE (MODERN CONNECTION) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_all_data():
    # Targets the HARDWARE tab updated by your Sync Bot
    return conn.read(worksheet="HARDWARE", header=None)

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

# --- 4. APP INTERFACE ---
raw_df = load_all_data()

if not raw_df.empty:
    with st.sidebar:
        st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=200)
        st.subheader("Connect with us")
        st.markdown("""
            <a href="https://instagram.com/technodel" class="social-link">📸 Instagram</a>
            <a href="https://facebook.com/technodel" class="social-link">📘 Facebook</a>
            <a href="https://wa.me/96170449900" class="social-link">💬 WhatsApp Admin</a>
        """, unsafe_allow_html=True)
        st.divider()
        if st.button("🔄 Reset PC Build", on_click=reset_build, use_container_width=True):
            pass
        st.info("🛡️ 1 Year Hardware Warranty\n\n🚀 Ready in 24h")

    # Data Extraction
    cpu_df = get_items_from_col(raw_df, 0, 'PROCESSORS')
    coo_df = get_items_from_col(raw_df, 0, 'CPU COOLERS')
    cas_df = get_items_from_col(raw_df, 0, 'CASES')
    mb_df  = get_items_from_col(raw_df, 3, 'MOTHER BOARDS')
    st_df  = get_items_from_col(raw_df, 3, 'INTERNAL STORAGE')
    psu_df = get_items_from_col(raw_df, 9, 'POWER SUPPLIES')
    gpu_df = get_items_from_col(raw_df, 9, 'GRAPHICS CARDS')

    st.title("Technodel PC Builder Pro")

    col1, col2 = st.columns(2)
    with col1:
        cpu_c = st.selectbox("Processor", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cpu_df.iterrows()], key="c")
        mb_l = mb_df[mb_df['ITEM'].apply(lambda x: is_compat(cpu_c, x))] if "Select" not in cpu_c else mb_df
        mb_c = st.selectbox("Motherboard", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in mb_l.iterrows()], key="m")
        
        if "Select" not in mb_c:
            tech = "DDR5" if "DDR5" in mb_c.upper() else "DDR3" if "DDR3" in mb_c.upper() else "DDR4"
            ram_df = get_items_from_col(raw_df, 6, tech, exclude_laptop=True)
            if 'r_cnt' not in st.session_state: st.session_state.r_cnt = 1
            for i in range(st.session_state.r_cnt):
                st.selectbox(f"{tech} RAM {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in ram_df.iterrows()], key=f"r_{i}")
            if st.button("➕ Add RAM"): st.session_state.r_cnt += 1; st.rerun()

    with col2:
        gpu_c = st.selectbox("GPU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in gpu_df.iterrows()], key="g")
        psu_c = st.selectbox("PSU", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in psu_df.iterrows()], key="p")
        cas_c = st.selectbox("Case", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in cas_df.iterrows()], key="ca")
        coo_c = st.selectbox("Cooler", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in coo_df.iterrows()], key="co")
        
        if 's_cnt' not in st.session_state: st.session_state.s_cnt = 1
        for i in range(st.session_state.s_cnt):
            st.selectbox(f"Storage {i+1}", ["Select"] + [f"{r['ITEM']} - ${r['PRICE']}" for _,r in st_df.iterrows()], key=f"s_{i}")
        if st.button("➕ Add Storage"): st.session_state.s_cnt += 1; st.rerun()

    # --- 5. BUILD SUMMARY & EXPORT ---
    st.divider()
    total = 0
    html_rows = ""
    whatsapp_items = ""
    
    # Process static parts
    parts_map = [('c', 'CPU'), ('m', 'Motherboard'), ('g', 'GPU'), ('p', 'PSU'), ('ca', 'Case'), ('co', 'Cooler')]
    for k, label in parts_map:
        val = st.session_state.get(k)
        if val and "Select" not in val:
            name, price = val.split(" - $")
            total += int(price.replace(",", ""))
            html_rows += f'<div class="build-item"><span>{label}: {name}</span><b>${price}</b></div>'
            whatsapp_items += f"- {label}: {name} (${price})\n"

    # Process dynamic RAM/Storage
    for i in range(st.session_state.get('r_cnt', 1)):
        v = st.session_state.get(f"r_{i}")
        if v and "Select" not in v:
            name, price = v.split(" - $")
            total += int(price.replace(",", ""))
            html_rows += f'<div class="build-item"><span>RAM {i+1}: {name}</span><b>${price}</b></div>'
            whatsapp_items += f"- RAM: {name} (${price})\n"
            
    for i in range(st.session_state.get('s_cnt', 1)):
        v = st.session_state.get(f"s_{i}")
        if v and "Select" not in v:
            name, price = v.split(" - $")
            total += int(price.replace(",", ""))
            html_rows += f'<div class="build-item"><span>Storage {i+1}: {name}</span><b>${price}</b></div>'
            whatsapp_items += f"- Storage: {name} (${price})\n"

    if total > 0:
        st.subheader("🖥️ Build Quotation")
        st.markdown(f"""
            <div class="build-box">
                {html_rows}
                <div class="total-row">Total Build: ${total:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(" ")
        c_pdf, c_wa = st.columns(2)
        
        with c_pdf:
            pdf_data = generate_real_pdf(html_rows, total)
            st.download_button(
                label="📄 Download PDF Quotation",
                data=pdf_data,
                file_name="Technodel_Quote.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with c_wa:
            wa_text = f"Hello Technodel! I want to order this build:\n\n{whatsapp_items}\nTotal: ${total:,}"
            wa_url = f"https://wa.me/9613659872?text={urllib.parse.quote(wa_text)}"
            st.link_button("🟢 Place Order via WhatsApp", wa_url, use_container_width=True)

else:
    st.error("Sheet data could not be loaded. Check your connection.")
