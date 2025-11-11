import streamlit as st
import pandas as pd
import base64
import requests
import subprocess
import os

# ==========================================
# 🧩 Common Helper Functions
# ==========================================
def load_table(file_name):
    """Load Excel to list of dicts"""
    if os.path.exists(file_name):
        return pd.read_excel(file_name).to_dict("records")
    return []

def save_table(file_name, data):
    """Save list of dicts to Excel"""
    pd.DataFrame(data).to_excel(file_name, index=False)

def delete_row(data_list, index):
    """Remove one row"""
    if 0 <= index < len(data_list):
        data_list.pop(index)

# Set folder for saving uploaded files
SAVE_DIR = "uploaded_data"
os.makedirs(SAVE_DIR, exist_ok=True)

st.title("📊 Upload Excel with 'first' and 'current' sheets")

uploaded_file = st.file_uploader("Upload your Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Save the uploaded file locally
    save_path = os.path.join(SAVE_DIR, "first.xlsx")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File saved to: {save_path}")

    try:
        # Read the two required sheets
        df_first = pd.read_excel(uploaded_file, sheet_name="first")
        df_current = pd.read_excel(uploaded_file, sheet_name="current")

        st.subheader("📄 Preview - 'first' Sheet")
        st.dataframe(df_first)

        st.subheader("📄 Preview - 'current' Sheet")
        st.dataframe(df_current)

    except ValueError as e:
        st.error("❌ Error: Missing 'first' or 'current' sheet.")
        st.info("Please make sure the Excel file has both sheets named exactly: 'first' and 'current'.")


# ==========================================
# 💀 DEAD KPI TABLE
# ==========================================
st.header("💀 Dead Rate Table")

DEAD_FILE = "dead_table.xlsx"
if "dead_data" not in st.session_state:
    st.session_state.dead_data = load_table(DEAD_FILE)

# --- Upload Existing Dead Table ---
uploaded_dead = st.file_uploader("📤 Upload Dead Table (.xlsx)", type=["xlsx"], key="upload_dead")
if uploaded_dead is not None:
    df_uploaded = pd.read_excel(uploaded_dead)
    st.session_state.dead_data = df_uploaded.to_dict("records")
    save_table(DEAD_FILE, st.session_state.dead_data)
    st.success("✅ Dead Table loaded from your file!")

# --- Input Form ---
with st.form("dead_form", clear_on_submit=True):
    power_start = st.number_input("Power Start (Dead)", min_value=0, step=1_000_000, format="%d")
    power_end = st.number_input("Power End (Dead)", min_value=0, step=1_000_000, format="%d")
    dead_dkp = st.number_input("Dead DKP", min_value=0, step=50_000, format="%d")
    submitted_dead = st.form_submit_button("➕ Add Dead Row")

    if submitted_dead and power_end > power_start:
        st.session_state.dead_data.append({
            "POWER_START": power_start,
            "POWER_END": power_end,
            "DEAD_DKP": dead_dkp
        })
        save_table(DEAD_FILE, st.session_state.dead_data)
        st.success("✅ Added to Dead Table!")

# --- Display + Actions ---
if st.session_state.dead_data:
    dead_df = pd.DataFrame(st.session_state.dead_data)
    dead_df.index += 1
    st.subheader("📊 Dead Rate Table")

    # 💾 Download current Dead Table
    st.download_button(
        label="💾 Download Dead Table (.xlsx)",
        data=dead_df.to_excel(index=False, engine="openpyxl"),
        file_name="dead_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 🗑️ Clear All
    if st.button("🗑️ Xóa toàn bộ Dead Table"):
        st.session_state.dead_data = []
        if os.path.exists(DEAD_FILE):
            os.remove(DEAD_FILE)
        st.success("✅ Dead Table cleared.")
        st.stop()

    # 🔸 Display rows + delete each
    for i, row in enumerate(st.session_state.dead_data):
        cols = st.columns([3, 3, 3, 1])
        cols[0].write(f"**Start:** {row['POWER_START']:,}")
        cols[1].write(f"**End:** {row['POWER_END']:,}")
        cols[2].write(f"**Dead DKP:** {row['DEAD_DKP']:,}")
        if cols[3].button("❌", key=f"dead_del_{i}"):
            delete_row(st.session_state.dead_data, i)
            save_table(DEAD_FILE, st.session_state.dead_data)
            st.experimental_rerun()
else:
    st.info("📝 No Dead data yet.")

# ==========================================
# ⚔️ DKP POWER TABLE
# ==========================================
st.markdown("---")
st.header("⚔️ Power DKP Table")

DKP_FILE = "dkp_table.xlsx"
if "dkp_data" not in st.session_state:
    st.session_state.dkp_data = load_table(DKP_FILE)

# --- Upload Existing DKP Table ---
uploaded_dkp = st.file_uploader("📤 Upload DKP Table (.xlsx)", type=["xlsx"], key="upload_dkp")
if uploaded_dkp is not None:
    df_uploaded = pd.read_excel(uploaded_dkp)
    st.session_state.dkp_data = df_uploaded.to_dict("records")
    save_table(DKP_FILE, st.session_state.dkp_data)
    st.success("✅ DKP Table loaded from your file!")

# --- Input Form ---
with st.form("dkp_form", clear_on_submit=True):
    power_start = st.number_input("Power Start (DKP)", min_value=0, step=1_000_000, format="%d")
    power_end = st.number_input("Power End (DKP)", min_value=0, step=1_000_000, format="%d")
    dkp_value = st.number_input("DKP Value", min_value=0, step=50_000, format="%d")
    submitted_dkp = st.form_submit_button("➕ Add DKP Row")

    if submitted_dkp and power_end > power_start:
        st.session_state.dkp_data.append({
            "POWER_START": power_start,
            "POWER_END": power_end,
            "DKP": dkp_value
        })
        save_table(DKP_FILE, st.session_state.dkp_data)
        st.success("✅ Added to DKP Table!")

# --- Display + Actions ---
if st.session_state.dkp_data:
    dkp_df = pd.DataFrame(st.session_state.dkp_data)
    dkp_df.index += 1
    st.subheader("📊 Power DKP Table")

    # 💾 Download current DKP Table
    st.download_button(
        label="💾 Download DKP Table (.xlsx)",
        data=dkp_df.to_excel(index=False, engine="openpyxl"),
        file_name="dkp_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 🗑️ Clear All
    if st.button("🗑️ Xóa toàn bộ DKP Table"):
        st.session_state.dkp_data = []
        if os.path.exists(DKP_FILE):
            os.remove(DKP_FILE)
        st.success("✅ DKP Table cleared.")
        st.stop()

    # 🔸 Display rows + delete each
    for i, row in enumerate(st.session_state.dkp_data):
        cols = st.columns([3, 3, 3, 1])
        cols[0].write(f"**Start:** {row['POWER_START']:,}")
        cols[1].write(f"**End:** {row['POWER_END']:,}")
        cols[2].write(f"**DKP:** {row['DKP']:,}")
        if cols[3].button("❌", key=f"dkp_del_{i}"):
            delete_row(st.session_state.dkp_data, i)
            save_table(DKP_FILE, st.session_state.dkp_data)
            st.experimental_rerun()
else:
    st.info("📝 No DKP data yet.")

