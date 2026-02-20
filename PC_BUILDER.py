import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE TAB ID MAPPING (CRITICAL FIX) ---
# Replace the numbers below with the GID found in your browser URL for each tab
# Example: Click 'CPU' tab -> copy the number after 'gid=' in the URL
TAB_IDS = {
    "CPU": "0",          # Replace with your CPU tab GID
    "GPU": "12345678",   # Replace with your GPU tab GID
    "RAM": "87654321",   # Replace with your RAM tab GID
    "Motherboard": "111",# Replace with your Motherboard tab GID
    "Storage": "222",    # Replace with your Storage tab GID
    "PSU": "333",        # Replace with your PSU tab GID
    "Case": "444"         # Replace with your Case tab GID
}

def load_hardware_tab(cat_name):
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        gid = TAB_IDS.get(cat_name, "0")
        
        # KEY FIX: Using 'gid=' instead of 'sheet=' is the only way to force 
        # Google to stop defaulting to the first tab
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&gid={gid}"
        
        df = pd.read_csv(csv_url)
        
        items = []
        # Row 4 logic: index 2. Name=Col B (1), Price=Col C (2) [cite: 2026-02-16]
        for index, row in df.iloc[2:].iterrows():
            name_val = row.iloc[1]   
            price_val = row.iloc[2]  
            if pd.notna(name_val) and pd.notna(price_val):
                try:
                    clean_price = str(price_val).replace('$', '').replace(',', '').strip()
                    price = int(round(float(clean_price), 0))
                    items.append({"name": str(name_val), "price": price})
                except: continue
        return items
    except: return []

# --- 3. SMART LINK & UI ---
params = st.query_params
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

build = {}
total_price = 0
cols = st.columns(3)

for i, cat in enumerate(TAB_IDS.keys()):
    with cols[i % 3]:
        options = load_hardware_tab(cat)
        if options:
            default_index = 0
            if cat in params:
                for idx, opt in enumerate(options):
                    if opt['name'] == params[cat]:
                        default_index = idx
            
            selection = st.selectbox(
                f"Select {cat}", options, index=default_index,
                format_func=lambda x: f"{x['name']} (${x['price']})"
            )
            build[cat] = selection
            total_price += selection['price']

st.divider()
st.header(f"Total Price: ${total_price}")

# Replace with your deployed app URL [cite: 2026-02-19]
base_share_url = "https://technodel-builder.streamlit.app/?"
encoded_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
st.subheader("🔗 Share Build Link")
st.code(base_share_url + encoded_params)
