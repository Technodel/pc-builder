import streamlit as st
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. DATA LOADING ---
def get_hardware_data():
    try:
        # Initializing the Google Sheets connection [cite: 2026-02-19]
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # We target the 'hardware' worksheet. ttl=0 for live updates [cite: 2026-02-16, 2026-02-19]
        # If your tab is named "Hardware", change it here to "Hardware"
        df = conn.read(worksheet="hardware", ttl=0)
        
        # Skip Row 1, 2, 3 to start at Row 4 [cite: 2026-02-16]
        df = df.iloc[2:].copy()
        
        # Drop rows where Name (Col B / Index 1) is empty [cite: 2026-02-16]
        df = df.dropna(subset=[df.columns[1]])
        return df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# --- 3. UI & CATEGORIES ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_hardware_data()

if df is not None:
    # Logic for URL parameters (Share Build) [cite: 2026-02-19]
    params = st.query_params
    
    # List of categories to find in your Column A [cite: 2026-02-19]
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Look for the category name in Column A (Index 0) [cite: 2026-02-16]
            cat_df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
            
            options = []
            for _, row in cat_df.iterrows():
                try:
                    name = str(row.iloc[1])
                    # Remove $ and commas for math [cite: 2026-02-16]
                    price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_str), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                # Pre-select if part is in the URL [cite: 2026-02-19]
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
                st.warning(f"Check your sheet for category: {cat}")

    st.divider()
    st.header(f"Total: ${total_price}")

    # --- 4. SHARE LINK GENERATION ---
    # Your builder URL [cite: 2026-02-19]
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
