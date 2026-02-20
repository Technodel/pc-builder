import streamlit as st
import pandas as pd
from groq import Groq

# --- 1. UI SETTINGS ---
st.set_page_config(page_title="Technodel PC Builder 🖥️", layout="wide")

# --- 2. AI SETUP ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# --- 3. THE STURDY GOOGLE SHEETS LOGIC ---
def load_category_from_gsheets(tab_name):
    try:
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # We target the specific tab (CPU, GPU, etc.) [2026-02-19]
        csv_url = f"{base_url.rstrip('/')}/export?format=csv&sheet={tab_name}"
        
        df = pd.read_csv(csv_url)
        
        items = []
        # Logic: Skip first 2 rows. Name=Col B (1), Price=Col C (2) [2026-02-16]
        for index, row in df.iloc[2:].iterrows():
            name_val = row.iloc[1]   
            price_val = row.iloc[2]  
            if pd.notna(name_val) and pd.notna(price_val):
                try:
                    clean_price = str(price_val).replace('$', '').replace(',', '').strip()
                    price = int(round(float(clean_price), 0))
                    items.append({"name": str(name_val), "price": price})
                except: continue
        return items
    except Exception as e:
        st.error(f"Error loading {tab_name}: {e}")
        return []

# --- 4. APP INTERFACE ---
st.title("Technodel Custom PC Builder")
st.write("Build your dream PC online. Prices sync automatically from our main sheet.")

# Define your categories based on your Sheet Tabs
categories = ["CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case"]
build = {}
total_price = 0

# Create columns for a clean selection UI
cols = st.columns(3)

for i, cat in enumerate(categories):
    with cols[i % 3]:
        options = load_category_from_gsheets(cat)
        if options:
            selection = st.selectbox(f"Select {cat}", options, format_func=lambda x: f"{x['name']} (${x['price']})")
            build[cat] = selection
            total_price += selection['price']

st.divider()

# --- 5. THE BUILD SUMMARY & AI REVIEW ---
col_left, col_right = st.columns(2)

with col_left:
    st.header(f"Total: ${total_price}")
    if st.button("🔥 Review My Build"):
        build_details = "\n".join([f"{k}: {v['name']}" for k, v in build.items()])
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional PC hardware expert at Technodel Lebanon. Speak in Lebanese Arabic. Check if the parts are compatible and if the PSU is enough."},
                {"role": "user", "content": f"Review this build:\n{build_details}"}
            ],
        )
        st.session_state.pc_review = completion.choices[0].message.content

with col_right:
    if "pc_review" in st.session_state:
        st.markdown(f"### Expert Advice\n{st.session_state.pc_review}")

# --- 6. SHARE BUILD LINK (NEW FEATURE) ---
st.subheader("🔗 Share this Build")
# Create a unique URL that encodes the parts (Draft logic)
share_link = f"https://technodel-builder.streamlit.app/?total={total_price}"
st.text_input("Copy this link to send to a customer:", share_link)
