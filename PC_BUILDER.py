import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY SOURCE ---
def get_data():
    try:
        # Your clean Sheet ID
        sheet_id = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
        
        # We use the direct export link to target the 'hardware' tab
        # This replaces the local Excel file logic perfectly
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet=hardware"
        
        df = pd.read_csv(url)
        
        # Original Logic: Start from Row 4 (skipping first 2 junk rows)
        df = df.iloc[2:].copy()
        
        # Filter for rows that have a Name (Column B) and Price (Column C)
        df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
        return df
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

# --- 3. MAIN UI ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")

df = get_data()

if df is not None:
    # URL Parameters for sharing links with customers
    params = st.query_params
    
    # Categories exactly as they appear in your Category column (Col A)
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Search Column A for the specific category
            cat_df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
            
            options = []
            for _, row in cat_df.iterrows():
                try:
                    name = str(row.iloc[1])
                    # Clean currency formatting
                    price_str = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_str), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                # Set default from URL if customer clicked a shared link
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
                st.warning(f"Category '{cat}' not found in hardware sheet.")

    st.divider()
    st.header(f"Total Price: ${total_price}")

    # --- 4. SHARE LINK ---
    base_url = "https://technodel-builder.streamlit.app/?"
    query_string = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    st.subheader("🔗 Share Build Link")
    st.code(base_url + query_string)
