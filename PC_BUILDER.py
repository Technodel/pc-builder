import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY DATA LOADER ---
def get_hardware_data():
    try:
        # Your specific Sheet ID
        sheet_id = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        
        # Direct CSV export link - this bypasses st.connection bugs
        # We use the tab name 'hardware'
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet=hardware"
        
        df = pd.read_csv(url)
        
        # Skip the first 2 rows to start at Row 4
        df = df.iloc[2:].copy()
        
        # Remove any rows that don't have a Name in Column B (index 1)
        df = df.dropna(subset=[df.columns[1]])
        return df
    except Exception as e:
        st.error(f"❌ Direct Connection Failed: {e}")
        st.info("Trying alternative: Ensure your tab is named 'hardware' exactly.")
        return None

# --- 3. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_hardware_data()

if df is not None:
    params = st.query_params
    # These must match the text in your 'Category' column (Column A)
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
                    # Clean currency formatting ($ and ,)
                    price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_str), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                # Handle auto-filling from a shared link
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
                st.warning(f"⚠️ No items found for '{cat}' in the 'hardware' tab.")

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK ---
    # Your builder URL
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
