import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. SIDEBAR FILE UPLOADER ---
st.sidebar.header("Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload your Hardware Excel", type=["xlsx", "xlsm"])

# --- 3. THE DATA LOADING ENGINE ---
def get_data(file):
    try:
        # Yesterday's Logic: Points to the 'hardware' sheet [cite: 2026-02-16]
        df = pd.read_excel(file, sheet_name="hardware")
        
        # Data starts at Row 4 (skipping first 2 rows of headers) [cite: 2026-02-16]
        df = df.iloc[2:].copy()
        
        # Clean: Remove empty rows based on Name and Price columns [cite: 2026-02-16]
        df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
        return df
    except Exception as e:
        st.error(f"⚠️ Error: Ensure your sheet is named 'hardware'. {e}")
        return None

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

if uploaded_file is not None:
    df = get_data(uploaded_file)
    
    if df is not None:
        params = st.query_params
        
        # The specific categories from your tables [cite: 2026-02-19]
        categories = ["table_cpu", "table_gpu", "table_ram", "table_motherboard", "table_storage", "table_psu", "table_case"]
        build = {}
        total_price = 0
        
        cols = st.columns(3)
        
        for i, cat in enumerate(categories):
            with cols[i % 3]:
                # Search Column A (Index 0) for your table identifiers
                cat_df = df[df.iloc[:, 0].astype(str).str.contains(cat, case=False, na=False)]
                
                options = []
                for _, row in cat_df.iterrows():
                    try:
                        name = str(row.iloc[1])
                        # Clean price ($ and ,) [cite: 2026-02-16]
                        price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                        price = int(round(float(price_str), 0))
                        options.append({"name": name, "price": price})
                    except:
                        continue
                
                if options:
                    # 'Share Build' auto-selection [cite: 2026-02-19]
                    default_idx = 0
                    if cat in params:
                        for idx, opt in enumerate(options):
                            if opt['name'] == params[cat]:
                                default_idx = idx
                    
                    # Create the dropdown for each category
                    label = cat.replace("table_", "").upper()
                    sel = st.selectbox(
                        f"Select {label}", 
                        options, 
                        index=default_idx, 
                        format_func=lambda x: f"{x['name']} (${x['price']})"
                    )
                    build[cat] = sel
                    total_price += sel['price']
                else:
                    st.warning(f"Category '{cat}' not found in the sheet.")

        st.divider()
        st.header(f"Total Price: ${total_price}")

        # --- 5. THE SHARE LINK ---
        # Direct link for technodel-builder.streamlit.app [cite: 2026-02-19]
        base_url = "https://technodel-builder.streamlit.app/?"
        query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
        
        st.subheader("🔗 Share Build Link")
        st.code(base_url + query_string)
else:
    st.info("👈 Please upload your Excel file in the sidebar to begin.")
