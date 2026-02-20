import streamlit as st
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# --- UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

def get_hardware_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # We try to read the 'hardware' tab. 
        # TIP: Check your Google Sheet tab name right now! 
        # If it is "Hardware", change the text below to "Hardware"
        df = conn.read(worksheet="hardware", ttl=0)
        
        # Skip the first 2 rows to start at your parts [2026-02-16]
        df = df.iloc[2:].copy()
        
        # Drop rows where the Name (Column B) is empty
        df = df.dropna(subset=[df.columns[1]])
        return df
    except Exception as e:
        # This will print the EXACT error from Google to help us debug
        st.error(f"❌ Connection Failed: {e}")
        st.info("💡 Tip: Check if your tab is named 'hardware' exactly and 'Anyone with the link can view' is ON.")
        return None

# --- MAIN APP ---
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
            # This line searches Column A for your category name
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
                # Pre-fill from the 'Share Build' link [2026-02-19]
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
                st.warning(f"Category '{cat}' not found in the 'hardware' tab.")

    st.divider()
    st.header(f"Total: ${total_price}")

    # --- SHARE LINK ---
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
