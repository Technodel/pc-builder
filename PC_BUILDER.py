import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS (Must be first) ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY GOOGLE SHEETS LOGIC ---
def load_category_from_gsheets(tab_name):
    try:
        # Accesses the URL from the Secrets
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Forces a CSV export for a specific tab
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
    except Exception as e:
        return []

# --- 3. SMART LINK LOGIC ---
# Reads URL parameters to auto-fill selections [cite: 2026-02-19]
params = st.query_params

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")
st.write("Prices sync automatically from the Master Price List.")

# Ensure these match your Google Sheet Tab names exactly!
categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
build = {}
total_price = 0

cols = st.columns(3)

for i, cat in enumerate(categories):
    with cols[i % 3]:
        options = load_category_from_gsheets(cat)
        if options:
            default_index = 0
            # If a part name matches a URL parameter, auto-select it [cite: 2026-02-19]
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

st.divider()

# --- 5. SHARE BUILD SECTION ---
st.header(f"Total Price: ${total_price}")

# Replace the URL below with your actual deployed app link [cite: 2026-02-19]
base_share_url = "https://technodel-pc-builder.streamlit.app/?"
encoded_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
full_share_url = base_share_url + encoded_params

st.subheader("🔗 Share with Customer")
st.info("When the customer opens this link, all selected parts will be pre-filled.")
st.code(full_share_url)
