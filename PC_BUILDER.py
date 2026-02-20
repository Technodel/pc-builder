import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE HARDWARE SELECTOR LOGIC ---
def load_hardware_tab(tab_name):
    try:
        # Pulls the URL from your Secrets
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # KEY FIX: We add '&sheet=' to the URL to force it to look at the correct tab
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&sheet={tab_name}"
        
        df = pd.read_csv(csv_url)
        
        items = []
        # Row 4 logic: skip index 0 and 1. Name=Col B (1), Price=Col C (2) [cite: 2026-02-16]
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
    except Exception:
        return []

# --- 3. SMART LINK LOGIC ---
params = st.query_params

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

# IMPORTANT: These names must match your Google Sheet Tab names EXACTLY [cite: 2026-02-16]
# If your tab is named "CPUs" change "CPU" to "CPUs" below.
categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
build = {}
total_price = 0

cols = st.columns(3)

for i, cat in enumerate(categories):
    with cols[i % 3]:
        options = load_hardware_tab(cat)
        
        if options:
            default_index = 0
            if cat in params:
                for idx, opt in enumerate(options):
                    if opt['name'] == params[cat]:
                        default_index = idx
            
            selection = st.selectbox(
                f"Select {cat}", 
                options, 
                index=default_index,
                format_func=lambda x: f"{x['name']} (${x['price']})"
            )
            build[cat] = selection
            total_price += selection['price']
        else:
            # This error shows if the tab name doesn't exist in your Google Sheet
            st.error(f"Could not find hardware tab named: '{cat}'")

st.divider()

# --- 5. PRICE & SHARE ---
st.header(f"Total Price: ${total_price}")

# Replace with your actual builder URL once deployed [cite: 2026-02-19]
base_share_url = "https://technodel-builder.streamlit.app/?"
encoded_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
full_share_url = base_share_url + encoded_params

st.subheader("🔗 Share Build Link")
st.code(full_share_url)
