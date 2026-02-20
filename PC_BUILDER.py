import streamlit as st
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. THE STURDY CONNECTION ---
# This looks at the 'hardware' tab specifically [cite: 2026-02-19]
def get_hardware_data():
    try:
        # Use the official streamlit-gsheets connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Pull data from the 'hardware' tab [cite: 2026-02-16]
        # ttl=0 ensures prices update immediately when you change the sheet
        df = conn.read(worksheet="hardware", ttl=0)
        
        # Skip the first 2 rows to reach the data starting at Row 4 [cite: 2026-02-16]
        df = df.iloc[2:].copy()
        
        # Clean up: Only keep rows where Name (Col B) and Price (Col C) exist [cite: 2026-02-16]
        df = df.dropna(subset=[df.columns[1], df.columns[2]])
        return df
    except Exception as e:
        st.error(f"Connection Error: Check if your tab is named 'hardware' exactly. {e}")
        return None

# --- 3. SMART LINK LOGIC ---
# Reads parameters from the URL to auto-fill parts for the customer [cite: 2026-02-19]
params = st.query_params

# --- 4. MAIN INTERFACE ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=150)
st.title("Technodel PC Builder")
st.write("Building from the **hardware** tab online.")

df = get_hardware_data()

if df is not None:
    # We define the categories to filter from the 'hardware' tab
    # Ensure these names match the text in your 'Category' column
    categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
    build = {}
    total_price = 0
    
    cols = st.columns(3)
    
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            # Filter the 'hardware' sheet for rows matching this category
            # Assuming Category is Column A (index 0)
            cat_options_df = df[df.iloc[:, 0].str.contains(cat, case=False, na=False)]
            
            # Convert to a list of dictionaries for the selectbox
            options = []
            for _, row in cat_options_df.iterrows():
                try:
                    name = str(row.iloc[1])
                    # Clean price formatting (removing $, commas) [cite: 2026-02-16]
                    price_val = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
                    price = int(round(float(price_val), 0))
                    options.append({"name": name, "price": price})
                except: continue
            
            if options:
                # Logic for the Share Build link auto-selection [cite: 2026-02-19]
                default_index = 0
                if cat in params:
                    for idx, opt in enumerate(options):
                        if opt['name'] == params[cat]:
                            default_index = idx
                
                selection = st.selectbox(
                    f"Select {cat}", 
                    options, 
                    index=default_index,
                    format_func=lambda x: f"{x['name']} (${x['price']})"
                )
                build[cat] = selection
                total_price += selection['price']
            else:
                st.warning(f"No items found for {cat} in the hardware sheet.")

    st.divider()

    # --- 5. THE TOTAL & SHARE LINK ---
    st.header(f"Total Build: ${total_price}")

    # Generate the Smart Link for the customer [cite: 2026-02-19]
    # URL format: technodel-builder.streamlit.app
    base_url = "https://technodel-builder.streamlit.app/?"
    share_params = urllib.parse.urlencode({k: v['name'] for k, v in build.items()})
    
    st.subheader("🔗 Share Build Link")
    st.info("Copy this link to send to your customer:")
    st.code(base_url + share_params)
else:
    st.info("Please connect your Google Sheet in the Streamlit Secrets.")
