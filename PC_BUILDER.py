import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY DATA LOADER (Same as Marketing Bot) ---
def get_hardware_data():
    try:
        # Your specific Sheet URL [2026-02-20]
        base_url = "https://docs.google.com/spreadsheets/d/1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        
        # Force export as CSV and target the 'hardware' tab
        # This is the most reliable way to avoid 400/404 errors
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&sheet=hardware"
        
        df = pd.read_csv(csv_url)
        
        # Skip headers/junk to start at Row 4 [2026-02-16]
        df = df.iloc[2:].copy()
        
        # Only keep rows where the Name (Column B / Index 1) is not empty
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
    # Check for URL parameters (Share Build feature) [2026-02-19]
    params = st.query_params
    
    # Categories based on your hardware sheet structure
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
                # Logic for the Share Build link auto-selection
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
                st.warning(f"Category '{cat}' not found in 'hardware' tab.")

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK GENERATION ---
    # The URL where your app is deployed
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.info("Send this link to your customer to pre-fill their build:")
    st.code(base_url + query_string)
