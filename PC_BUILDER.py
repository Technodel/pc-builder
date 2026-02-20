# --- 1. UPDATED PARSING LOGIC (Using Index instead of Name) ---
def parse_section(df, keyword):
    if df is None or df.empty: return pd.DataFrame()
    data = []
    found_section = False
    
    for _, row in df.iterrows():
        # Column A (Index 0) contains your table tags
        val_a = str(row.iloc[0]).strip() if pd.notnull(row.iloc[0]) else ""
        
        if not found_section:
            if f"table_{keyword.lower()}" in val_a.lower():
                found_section = True
            continue
        
        # Stop at the next table tag or empty row
        if not val_a or val_a == "nan" or "table_" in val_a.lower():
            break
            
        try:
            # Column B (Index 1) is ITEM NAME
            # Column C (Index 2) is PRICE
            name = str(row.iloc[1]) 
            price_val = str(row.iloc[2]).replace('$', '').replace(',', '').strip()
            clean_price = int(round(float(price_val), 0))
            
            data.append({"ITEM": name, "PRICE": clean_price})
        except:
            continue
            
    return pd.DataFrame(data)

# --- 2. UPDATED UI EXECUTION ---
raw_df = load_all_data()

if raw_df is not None and not raw_df.empty:
    st.success("✅ SUCCESS! Data loaded from Hardware tab.")
    
    sections = ["cpu", "mb", "ram", "gpu", "case", "psu", "coo", "storage"]
    dfs = {s: parse_section(raw_df, s) for s in sections}

    st.title("Build Your PC")
    
    # URL Parameter handling [cite: 2026-02-19]
    params = st.query_params
    
    # 3. CPU SELECTION (The part that crashed)
    if not dfs['cpu'].empty:
        cpu_list = ["Select CPU"] + dfs['cpu']['ITEM'].tolist()
        
        # Look for 'c' in the URL (e.g., ?c=Intel+i9) [cite: 2026-02-19]
        url_cpu = params.get("c", "Select CPU")
        default_idx = cpu_list.index(url_cpu) if url_cpu in cpu_list else 0
        
        selected_cpu = st.selectbox("Step 1: Choose Processor", cpu_list, index=default_idx, key="c")
    else:
        st.error("Could not find 'table_cpu' in your Excel sheet.")
