import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG & CONNECTION ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")
SHEET_URL = st.secrets["gsheets_url"]

# --- 2. GOOGLE SHEETS DATA LOAD ---
def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Reads the 'search' sheet from your Google Sheet [cite: 2026-02-16]
    df = conn.read(spreadsheet=SHEET_URL, worksheet="search", ttl=600)
    # Filter only for rows that have both a Name and Price
    df = df.dropna(subset=[df.columns[1], df.columns[2]]) 
    return df

# --- 3. UI ---
st.image("https://technodel.net/wp-content/uploads/2024/08/technodel-site-logo-01.webp", width=120)
st.title("🖥️ Technodel PC Builder")

try:
    df = get_data()
    
    # Create the selection list (Column B - Product Names)
    # Using Column B (index 1) for the names [cite: 2026-02-16]
    items_list = df.iloc[2:, 1].tolist() 
    
    st.write("### ابني جهازك (Build Your PC)")
    
    selected_parts = st.multiselect("Select Components:", items_list)
    
    if selected_parts:
        st.write("---")
        total_price = 0
        
        # Display table of selected parts
        summary_data = []
        for part in selected_parts:
            # Find the price in Column C (index 2) [cite: 2026-02-16]
            price = df[df.iloc[:, 1] == part].iloc[0, 2]
            try:
                price_val = int(float(str(price).replace('$', '').replace(',', '')))
                total_price += price_val
                summary_data.append({"Component": part, "Price": f"${price_val}"})
            except:
                continue
        
        st.table(summary_data)
        st.markdown(f"## **Total Price: ${total_price}**")
        
        # Share Build Feature [cite: 2026-02-19]
        if st.button("Generate Share Link"):
            # This is a placeholder for the custom URL logic we discussed
            st.info(f"Link ready for technodel-builder.streamlit.app")

except Exception as e:
    st.error(f"Please check your Google Sheets connection: {e}")
