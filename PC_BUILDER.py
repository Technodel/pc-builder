import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. DATA LOADER (Stays the same) ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), header=None)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 2. HEADER-BASED PARSER (The Bot's Brain) ---
def parse_by_title(df, title_keyword):
    if df is None or df.empty: return pd.DataFrame()
    data = []
    found = False
    
    # List of all your category titles to know when one section ends and another begins
    all_titles = ["PROCESSORS", "MOTHER BOARDS", "INTERNAL STORAGE", "CPU COOLERS", 
                  "CASES", "RAMS", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]

    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip().upper()
        
        if not found:
            if title_keyword.upper() in val_a:
                found = True
            continue
        
        # Stop logic: If we hit a DIFFERENT category title or an empty row
        if not val_a or val_a == "NAN" or any(t for t in all_titles if t in val_a and t != title_keyword.upper()):
            if len(data) > 0: break
            else: continue
            
        try:
            name = str(row.iloc[0]) # Column A
            price_raw = str(row.iloc[1]).replace('$', '').replace(',', '').strip() # Column B
            data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
        except:
            continue
    return pd.DataFrame(data)

# --- 3. UI EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # 4. BOT IDENTIFIES ALL COMPONENTS
    components = {
        "CPU": "PROCESSORS",
        "MB": "MOTHER BOARDS",
        "STORAGE": "INTERNAL STORAGE",
        "COOLER": "CPU COOLERS",
        "CASE": "CASES",
        "RAM": "RAMS",
        "PSU": "POWER SUPPLIES",
        "GPU": "GRAPHICS CARDS",
        "UPS": "UPS"
    }
    
    # Create DataFrames for every category automatically
    dfs = {key: parse_by_title(raw_df, title) for key, title in components.items()}

    st.success("✅ Success! All categories identified from your Excel.")

    # 5. DISPLAY SELECT BOXES
    st.title("Technodel PC Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cpu = st.selectbox("Select Processor", ["Select CPU"] + dfs['CPU']['ITEM'].tolist())
        gpu = st.selectbox("Select Graphics Card", ["Select GPU"] + dfs['GPU']['ITEM'].tolist())
        ram = st.selectbox("Select RAM", ["Select RAM"] + dfs['RAM']['ITEM'].tolist())
        mb = st.selectbox("Select Motherboard", ["Select MB"] + dfs['MB']['ITEM'].tolist())
    
    with col2:
        storage = st.selectbox("Select Storage", ["Select Storage"] + dfs['STORAGE']['ITEM'].tolist())
        cooler = st.selectbox("Select Cooler", ["Select Cooler"] + dfs['COOLER']['ITEM'].tolist())
        psu = st.selectbox("Select Power Supply", ["Select PSU"] + dfs['PSU']['ITEM'].tolist())
        case = st.selectbox("Select Case", ["Select Case"] + dfs['CASE']['ITEM'].tolist())

else:
    st.error("Could not connect to the Google Sheet. Check your GID or Sharing settings.")
