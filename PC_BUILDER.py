import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. DATA LOADER ---
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

# --- 2. THE BOT'S BRAIN (RESTORED) ---
def parse_by_title(df, title_keyword):
    if df is None or df.empty: return pd.DataFrame()
    data = []
    found = False
    # List of your actual titles from the Excel
    all_titles = ["PROCESSORS", "MOTHER BOARDS", "INTERNAL STORAGE", "CPU COOLERS", 
                  "CASES", "RAMS", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]

    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip().upper()
        if not found:
            if title_keyword.upper() in val_a:
                found = True
            continue
        # Stop at next title or empty cell
        if not val_a or val_a == "NAN" or any(t for t in all_titles if t == val_a and t != title_keyword.upper()):
            if len(data) > 0: break
            else: continue
        try:
            name = str(row.iloc[0]) # Column A
            price_raw = str(row.iloc[1]).replace('$', '').replace(',', '').strip() # Column B
            data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
        except: continue
    return pd.DataFrame(data)

# --- 3. UI EXECUTION ---
raw_df = load_all_data()

if not raw_df.empty:
    # 4. MAP TITLES TO KEYS
    cats = {
        "CPU": "PROCESSORS", "MB": "MOTHER BOARDS", "STORAGE": "INTERNAL STORAGE",
        "COOLER": "CPU COOLERS", "CASE": "CASES", "RAM": "RAMS", 
        "PSU": "POWER SUPPLIES", "GPU": "GRAPHICS CARDS", "UPS": "UPS"
    }
    dfs = {k: parse_by_title(raw_df, v) for k, v in cats.items()}
    
    st.title("Technodel PC Builder")
    
    # 5. BUILDER LOGIC
    choices = {}
    col1, col2 = st.columns(2)
    
    for i, (key, title) in enumerate(cats.items()):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if not dfs[key].empty:
                # Using 'ITEM' key safely
                item_list = ["Select " + key] + dfs[key]['ITEM'].tolist()
                selected = st.selectbox(f"Choose {title}", item_list, key=key)
                
                if "Select" not in selected:
                    price = dfs[key][dfs[key]['ITEM'] == selected]['PRICE'].values[0]
                    choices[key] = {"name": selected, "price": price}
    
    # 6. TOTAL PRICE CALCULATION
    st.divider()
    total = sum(item['price'] for item in choices.values())
    st.metric(label="Total Build Price", value=f"${total:,}")

    if choices:
        with st.expander("View Build Summary"):
            for k, v in choices.items():
                st.write(f"**{k}:** {v['name']} - ${v['price']}")

else:
    st.error("Connection Failed. Ensure Sheet is 'Published to Web'.")
