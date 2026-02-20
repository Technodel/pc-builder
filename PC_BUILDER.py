import streamlit as st
import pandas as pd
import urllib.parse
import glob

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. DATA LOADING (The "Perfect" Logic) ---
def get_data():
    try:
        # Scan GitHub folder for any Excel file
        excel_files = glob.glob("*.xlsx") + glob.glob("*.xlsm")
        
        if not excel_files:
            st.error("⚠️ No Excel file found in GitHub! Please upload your .xlsx or .xlsm file.")
            return None
            
        # Select the first file found
        target_file = excel_files[0]
        
        # Load the very first tab (index 0)
        df = pd.read_excel(target_file, sheet_name=0)
        
        # We skip the first 2 rows to start at Row 4 [2026-02-16]
        df = df.iloc[2:].copy()
        
        # Clean: Remove empty rows in the Name column (Column B)
        df = df.dropna(subset=[df.columns[1]]) 
        return df
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_data()

if df is not None:
    # URL Sharing logic for technodel-builder.streamlit.app [2026-02-19]
    params = st.query_params
    
    # Categories based on your Excel structure
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Filter Column A (index 0) for category name
            cat_df = df[df.iloc[:, 0].astype(str).str.contains(cat, case=False, na=False)]
            
            options = []
            for _, row in cat_df.iterrows():
                try:
                    name = str(row.iloc[1])
                    # Clean price formatting ($ and ,) [2026-02-16]
                    price_val = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_val), 0))
                    options.append({"name": name, "price": price})
                except:
                    continue
            
            if options:
                # Share Build auto-selection logic
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

    # --- 4. SHARE BUILD LINK ---
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
