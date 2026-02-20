import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. SIDEBAR FILE UPLOADER (Yesterday's Feature) ---
st.sidebar.header("Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload your Hardware Excel", type=["xlsx", "xlsm"])

# --- 3. DATA LOADING LOGIC ---
def get_data(file):
    try:
        # Points specifically to the 'hardware' sheet as we agreed
        df = pd.read_excel(file, sheet_name="hardware")
        
        # Yesterday's Logic: Start at Row 4 (Skip first 2 rows of junk)
        df = df.iloc[2:].copy()
        
        # Clean: Drop rows where Name (Col B) or Price (Col C) is empty
        df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
        return df
    except Exception as e:
        st.error(f"⚠️ Error: Could not find a sheet named 'hardware' in this file. {e}")
        return None

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

if uploaded_file is not None:
    df = get_data(uploaded_file)
    
    if df is not None:
        # URL parameters for 'Share Build' links [cite: 2026-02-19]
        params = st.query_params
        
        # Categories matching your hardware sheet structure
        categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
        build = {}
        total_price = 0
        
        cols = st.columns(3)
        
        for i, cat in enumerate(categories):
            with cols[i % 3]:
                # Filter Column A (Index 0) for the category name
                cat_df = df[df.iloc[:, 0].astype(str).str.contains(cat, case=False, na=False)]
                
                options = []
                for _, row in cat_df.iterrows():
                    try:
                        name = str(row.iloc[1])
                        # Clean price formatting ($ and ,) [cite: 2026-02-16]
                        price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                        price = int(round(float(price_str), 0))
                        options.append({"name": name, "price": price})
                    except:
                        continue
                
                if options:
                    # Pre-select if shared via a 'Share Build' link
                    default_idx = 0
                    if cat in params:
                        for idx, opt in enumerate(options):
                            if opt['name'] == params[cat]:
                                default_idx = idx
                    
                    sel = st.selectbox(
                        f"Select {cat}", 
                        options, 
                        index=default_idx, 
                        format_func=lambda x: f"{x['name']} (${x['price']})"
                    )
                    build[cat] = sel
                    total_price += sel['price']
                else:
                    st.warning(f"No items found for: {cat}")

        st.divider()
        st.header(f"Total Price: ${total_price}")

        # --- 5. SHARE BUILD LINK ---
        base_url = "https://technodel-builder.streamlit.app/?"
        query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
        
        st.subheader("🔗 Share Build Link")
        st.info("Copy this link to send to your customer:")
        st.code(base_url + query_string)
else:
    st.info("👈 Please upload your Excel file in the sidebar to begin.")
