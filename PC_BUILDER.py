import streamlit as st
import pandas as pd
import urllib.parse
import glob
import os

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE DYNAMIC FILE FINDER ---
def get_data():
    try:
        # Scan the directory for any Excel or Macro-Enabled Excel file
        excel_files = glob.glob("*.xlsx") + glob.glob("*.xlsm")
        
        if not excel_files:
            st.error("⚠️ No .xlsx or .xlsm file found in the GitHub directory!")
            return None
            
        # Pick the first excel file found
        target_file = excel_files[0]
        
        # Load the 'hardware' tab specifically [2026-02-16]
        df = pd.read_excel(target_file, sheet_name="hardware")
        
        # Yesterday's Logic: Start from Row 4 (skip 2 rows)
        df = df.iloc[2:].copy()
        
        # Filter for rows with Name and Price
        df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
        return df
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_data()

if df is not None:
    params = st.query_params
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Search Column A (Index 0) for the category name
            cat_df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
            
            options = []
            for _, row in cat_df.iterrows():
                try:
                    name = str(row.iloc[1])
                    # Clean price formatting ($ and ,) [2026-02-16]
                    price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_str), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                # Yesterday's Share Build auto-selection logic
                default_idx = 0
                if cat in params:
                    for idx, opt in enumerate(options):
                        if opt['name'] == params[cat]:
                            default_idx = idx
                
                sel = st.selectbox(f"Select {cat}", options, index=default_idx, 
                                   format_func=lambda x: f"{x['name']} (${x['price']})")
                build[cat] = sel
                total_price += sel['price']
            else:
                st.warning(f"Category '{cat}' not found in the file.")

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK GENERATION ---
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.info("Copy this link to send to your customer:")
    st.code(base_url + query_string)
