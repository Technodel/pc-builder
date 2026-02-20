import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Technodel PC Builder", layout="wide")

# Center the Logo at the top
st.markdown("<h1 style='text-align: center;'>Technodel</h1>", unsafe_allow_html=True)
# If you have a logo URL: st.image("YOUR_LOGO_URL", width=200) 

# Sidebar: Contact & Social Media
with st.sidebar:
    st.title("Contact Us")
    st.write("📞 Phone: +XXX XXXXXXXX")
    st.write("📍 Location: Beirut, Lebanon")
    st.divider()
    st.write("📱 **Follow Us**")
    st.markdown("[Facebook](https://facebook.com/technodel)")
    st.markdown("[Instagram](https://instagram.com/technodel)")

# --- 2. DATA LOADER ---
@st.cache_data(ttl=600)
def load_all_data():
    SHEET_ID = "1GI3z-7FJqSHgV-Wy7lzvq3aTg4ovKa4T0ytMj9BJld4"
    HARDWARE_GID = "1309359556"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={HARDWARE_GID}"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), header=None)
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 3. RESTORED PARSER ---
def parse_by_title(df, title_keyword):
    if df is None or df.empty: return pd.DataFrame()
    data = []
    found = False
    all_titles = ["PROCESSORS", "MOTHER BOARDS", "INTERNAL STORAGE", "CPU COOLERS", 
                  "CASES", "RAMS", "POWER SUPPLIES", "GRAPHICS CARDS", "UPS"]

    for _, row in df.iterrows():
        val_a = str(row.iloc[0]).strip().upper()
        if not found:
            if title_keyword.upper() in val_a: found = True
            continue
        if not val_a or val_a == "NAN" or any(t for t in all_titles if t == val_a and t != title_keyword.upper()):
            if len(data) > 0: break
            else: continue
        try:
            name = str(row.iloc[0])
            price_raw = str(row.iloc[1]).replace('$', '').replace(',', '').strip()
            data.append({"ITEM": name, "PRICE": int(round(float(price_raw), 0))})
        except: continue
    return pd.DataFrame(data)

# --- 4. APP LOGIC ---
raw_df = load_all_data()

if not raw_df.empty:
    cats = {
        "CPU": "PROCESSORS", "MB": "MOTHER BOARDS", "STORAGE": "INTERNAL STORAGE",
        "COOLER": "CPU COOLERS", "CASE": "CASES", "RAM": "RAMS", 
        "PSU": "POWER SUPPLIES", "GPU": "GRAPHICS CARDS", "UPS": "UPS"
    }
    dfs = {k: parse_by_title(raw_df, v) for k, v in cats.items()}
    
    # Selection Interface
    choices = {}
    col1, col2 = st.columns(2)
    for i, (key, title) in enumerate(cats.items()):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if not dfs[key].empty:
                item_list = ["Select " + key] + dfs[key]['ITEM'].tolist()
                selected = st.selectbox(f"Choose {title}", item_list, key=key)
                if "Select" not in selected:
                    price = dfs[key][dfs[key]['ITEM'] == selected]['PRICE'].values[0]
                    choices[key] = {"name": selected, "price": price}

    # --- 5. SUMMARY & DOWNLOAD ---
    if choices:
        st.divider()
        st.subheader("📋 Build Summary")
        total = sum(item['price'] for item in choices.values())
        
        # Create Text Summary for Download
        summary_text = f"TECHNODEL PC BUILD\nTotal: ${total:,}\n" + "-"*20 + "\n"
        for k, v in choices.items():
            st.write(f"**{k}:** {v['name']} - ${v['price']}")
            summary_text += f"{k}: {v['name']} - ${v['price']}\n"

        st.metric("Total Price", f"${total:,}")
        
        # Download Button
        st.download_button(
            label="📩 Download Quote (Text)",
            data=summary_text,
            file_name="Technodel_Build.txt",
            mime="text/plain"
        )
else:
    st.error("Sheet Load Error. Please ensure Column A has 'PROCESSORS', 'RAMS', etc.")
