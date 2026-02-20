import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. PAGE CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide", page_icon="🖥️")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .social-icon { width: 25px; margin-right: 10px; vertical-align: middle; }
    </style>
    """, unsafe_allow_html=True)

# Logo and Header
col_l, col_r = st.columns([1, 3])
with col_l:
    st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=250)
with col_r:
    st.title("Technodel Pro PC Builder")
    st.info("✅ 1 Year warranty on all parts | 🚀 Ready for pickup within 24 hours")

# --- 2. SIDEBAR (CONTACT & SOCIALS) ---
with st.sidebar:
    st.header("📞 Contact Information")
    st.write("03 659872 | 70 449900")
    st.write("71 234002 | 07 345689")
    st.write("📧 Adarwich@engineer.com")
    st.write("🌐 [Technodel.net](https://technodel.net)")
    
    st.divider()
    st.header("📱 Our Social Media")
    
    # Social Media with Manual "Logos" (Unicode/Markdown)
    st.markdown("🔵 [**Facebook**](https://fb.com/technodel)")
    st.markdown("📸 [**Instagram**](https://instagram.com/technodel_computers)")
    st.markdown("🎵 [**TikTok**](https://tiktok.com/@technodel_computer) *(Exclusive Deals!)*")
    
    st.divider()
    st.caption("© 2026 Technodel Computers")

# --- 3. DATA & MULTI-COLUMN PARSING ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), header=None)
        return pd.DataFrame()
    except: return pd.DataFrame()

def find_component_data(df, title):
    # Scans all columns (A, D, G, J) for the title
    for col in df.columns:
        match = df[df[col].astype(str).str.contains(title, case=False, na=False)]
        if not match.empty:
            start_row = match.index[0] + 1
            data = []
            for i in range(start_row, len(df)):
                name = str(df.iloc[i, col]).strip()
                if not name or name == "nan" or any(t in name.upper() for t in ["PRICE", "PROCESSOR"]):
                    if len(data) > 0: break
                    continue
                try:
                    price_raw = str(df.iloc[i, col + 1]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_raw), 0))
                    data.append({"ITEM": name, "PRICE": price})
                except: continue
            return pd.DataFrame(data)
    return pd.DataFrame()

# --- 4. THE BUILDER ---
raw_df = load_all_data()

if not raw_df.empty:
    cats = {
        "CPU": "PROCESSORS", "MB": "MOTHER BOARDS", "STORAGE": "INTERNAL STORAGE",
        "COOLER": "CPU COOLERS", "CASE": "CASES", "RAM": "RAMS", 
        "PSU": "POWER SUPPLIES", "GPU": "GRAPHICS CARDS", "UPS": "UPS"
    }
    
    dfs = {k: find_component_data(raw_df, v) for k, v in cats.items()}
    choices = {}
    
    # Grid Layout for Components
    st.subheader("🛠️ Select Your Components")
    c1, c2, c3 = st.columns(3)
    
    # Distribute components across 3 columns
    for i, (key, title) in enumerate(cats.items()):
        target_col = [c1, c2, c3][i % 3]
        with target_col:
            if not dfs[key].empty:
                items = ["Select " + title] + dfs[key]['ITEM'].tolist()
                sel = st.selectbox(f"{title}", items, key=key)
                if "Select" not in sel:
                    price = dfs[key][dfs[key]['ITEM'] == sel]['PRICE'].values[0]
                    choices[key] = {"name": sel, "price": price}

    # --- 5. BUILD SUMMARY & QUOTE ---
    if choices:
        st.divider()
        st.subheader("📊 Your PC Build Summary")
        
        summary_list = []
        for k, v in choices.items():
            summary_list.append({"Component": k, "Description": v['name'], "Price": f"${v['price']:,}"})
        
        st.table(pd.DataFrame(summary_list))
        
        total = sum(item['price'] for item in choices.values())
        st.metric("Estimated Total", f"${total:,}")
        
        # Download Logic
        quote_text = f"TECHNODEL PC QUOTE\nWarranty: 1 Year\nReady within 24h\n\n"
        for k, v in choices.items():
            quote_text += f"{k}: {v['name']} (${v['price']})\n"
        quote_text += f"\nTOTAL: ${total:,}\n\nContact: 03 659872"
        
        st.download_button("💾 Download Quotation", quote_text, "Technodel_Quote.txt")
else:
    st.error("Failed to sync with Google Sheets. Please check your data source.")
