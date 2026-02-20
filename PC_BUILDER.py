import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE DATA SOURCE (GOOGLE SHEETS) ---
def get_data():
    try:
        # This is your specific Sheet ID from the link you provided
        SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        
        # We force Google to export the 'hardware' tab as a CSV
        # This is the most stable way to replace a local Excel file
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=hardware"
        
        df = pd.read_csv(URL)
        
        # Yesterday's Logic: Skip the first 2 rows to start at Row 4 [2026-02-16]
        df = df.iloc[2:].copy()
        
        # Clean up: Only keep rows where Column B (Name) and Column C (Price) are not empty
        df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
        return df
    except Exception as e:
        st.error(f"⚠️ Sheet Connection Error: {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_data()

if df is not None:
    # URL Parameters for the "Share Build" feature [2026-02-19]
    params = st.query_params
    
    # Categories based on your 'hardware' sheet structure
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Filter Column A (Index 0) for the category name
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
                # Share Build auto-selection logic
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
                st.warning(f"Category '{cat}' not found in the sheet.")

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK GENERATION ---
    # Generates a link that automatically pre-fills the build for a customer
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.info("Copy this link to send to your customer:")
    st.code(base_url + query_string)
