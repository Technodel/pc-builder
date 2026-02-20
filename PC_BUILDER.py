import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY DATA LOADER ---
def get_hardware_data():
    try:
        # Your specific Sheet ID [2026-02-20]
        sheet_id = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        
        # !!! CHANGE THIS NUMBER !!! 
        # Click the 'hardware' tab in your browser and copy the gid number from the URL
        hardware_gid = "123456789" # <--- Replace this with your actual GID
        
        # The 'gviz' link is often more stable than the 'export' link for 400 errors
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={hardware_gid}"
        
        df = pd.read_csv(url)
        
        # Skip junk rows to start at Row 4 [2026-02-16]
        # In this format, Row 4 is usually index 2 or 3. Let's start at 2.
        df = df.iloc[2:].copy()
        
        # Drop rows where Name (Column B / Index 1) is empty
        df = df.dropna(subset=[df.columns[1]])
        return df
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_hardware_data()

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
                    price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_str), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                default_idx = 0
                if cat in params:
                    for idx, opt in enumerate(options):
                        if opt['name'] == params[cat]:
                            default_idx = idx
                
                sel = st.selectbox(f"Select {cat}", options, index=default_idx, 
                                   format_func=lambda x: f"{x['name']} (${x['price']})")
                build[cat] = sel
                total_price += sel['price']

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK ---
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
