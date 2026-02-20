import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. DATA LOADING LOGIC ---
def load_hardware_category(tab_name):
    try:
        # Pull the base URL from your Secrets
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # This is the critical part: it tells Google which tab to open
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&sheet={tab_name}"
        
        df = pd.read_csv(csv_url)
        
        items = []
        # Skips headers. Column B (index 1) = Name, Column C (index 2) = Price
        for index, row in df.iloc[2:].iterrows():
            name_val = row.iloc[1]   
            price_val = row.iloc[2]  
            if pd.notna(name_val) and pd.notna(price_val):
                try:
                    # Clean price formatting
                    clean_price = str(price_val).replace('$', '').replace(',', '').strip()
                    price = int(round(float(clean_price), 0))
                    items.append({"name": str(name_val), "price": price})
                except: continue
        return items
    except Exception as e:
        # If it fails, it returns an empty list so the app doesn't crash
        return []

# --- 3. SMART LINK PARAMS ---
params = st.query_params

# --- 4. UI DESIGN ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")
st.write("Prices sync automatically from the Master Price List.")

# --- 5. THE SELECTION GRID ---
# LIST YOUR TAB NAMES HERE EXACTLY AS THEY APPEAR IN GOOGLE SHEETS
categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]

build = {}
total_price = 0

# Grid Layout
cols = st.columns(3)

for i, cat in enumerate(categories):
    with cols[i % 3]:
        # Fetch data for this specific hardware tab
        options = load_hardware_category(cat)
        
        if options:
            # Check if this part was shared in a link
            default_index = 0
            if cat in params:
                for idx, opt in enumerate(options):
                    if opt['name'] == params[cat]:
                        default_index = idx
            
            # THE DROPDOWN
            selection = st.selectbox(
                f"Select {cat}", 
                options, 
                index=default_index,
                format_func=lambda x: f"{x['name']} (${x['price']})"
            )
            build[cat] = selection
            total_price += selection['price']
        else:
            st.warning(f"No data found in tab: {cat}")

st.divider()

# --- 6. PRICE & SHARING ---
st.header(f"Total Price: ${total_price}")

# Replace with your actual deployed URL
base_share_url = "https://technodel-builder.streamlit.app/?"
encoded_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
full_share_url = base_share_url + encoded_params

st.subheader("🔗 Share with Customer")
st.code(full_share_url)
