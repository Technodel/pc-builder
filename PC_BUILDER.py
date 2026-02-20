import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY GOOGLE SHEETS LOGIC ---
def load_category_from_gsheets(tab_name):
    try:
        # Pulls the URL from your [connections.gsheets] secrets
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Targets the specific tab (CPU, GPU, RAM, etc.)
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&sheet={tab_name}"
        
        df = pd.read_csv(csv_url)
        
        items = []
        # Row 4 logic: skip index 0 and 1. Name=Col B (1), Price=Col C (2)
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
        # This will show if a tab name is missing or the link is wrong
        st.error(f"Error loading tab '{tab_name}': {e}")
        return []

# --- 3. SMART LINK LOGIC ---
# This reads the URL to see if a customer clicked a shared link
params = st.query_params

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")
st.write("Prices sync automatically from the Master Price List.")

# Define your categories (Make sure these match your Google Sheet Tab names exactly!)
categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
build = {}
total_price = 0

# Create a 3-column layout for the selections
cols = st.columns(3)

for i, cat in enumerate(categories):
    with cols[i % 3]:
        options = load_category_from_gsheets(cat)
        if options:
            # Check if this part was in the shared link
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

st.divider()

# --- 5. THE "SHARE BUILD" SECTION ---
st.header(f"Total Build Price: ${total_price}")

# Generate the Smart Link for the customer
# Change 'technodel-builder.streamlit.app' to your actual deployed URL
base_share_url = "https://technodel-builder.streamlit.app/?"
encoded_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
full_share_url = base_share_url + encoded_params

st.subheader("🔗 Customer Share Link")
st.info("Copy this link and send it to your customer. All parts will be auto-selected for them.")
st.code(full_share_url)
