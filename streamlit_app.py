import streamlit as st
import pandas as pd
import subprocess
import os
from pathlib import Path

st.title("Upload Excel and Commit first.xlsx from Streamlit")

uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.dataframe(df)

    if st.button("Save and Commit first.xlsx"):
        filename = "first.xlsx"
        df.to_excel(filename, index=False)
        st.success(f"✅ File saved as {filename}")

        try:
            # Ensure git identity (Streamlit environments often lack this)
            subprocess.run(["git", "config", "user.name", "streamlit-bot"], check=False)
            subprocess.run(["git", "config", "user.email", "bot@example.com"], check=False)

            # Check we are in a git repo
            repo_check = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                                        capture_output=True, text=True)
            if repo_check.returncode != 0:
                st.error("❌ Not inside a Git repository.")
            else:
                # Check if file changed
                diff = subprocess.run(["git", "status", "--porcelain", filename],
                                      capture_output=True, text=True)
                if diff.stdout.strip() == "":
                    st.warning(f"No changes to commit for {filename}.")
                else:
                    subprocess.run(["git", "add", filename], check=True)
                    subprocess.run(["git", "commit", "-m", f"Update {filename}"], check=True)
                    st.success(f"✅ {filename} committed successfully!")

                    # Optional: push (requires token or SSH)
                    subprocess.run(["git", "push"], check=True)
                    st.info("Pushed to GitHub successfully.")

        except subprocess.CalledProcessError as e:
            st.error(f"❌ Git error: {e}")


st.set_page_config(page_title="DKP & Dead KPI Tables", layout="centered")

st.title("⚔️ DKP & 💀 Dead KPI Manager")

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

# ==========================================
# 💀 DEAD KPI TABLE
# ==========================================
st.header("💀 Dead Rate Table")

DEAD_FILE = "dead_table.xlsx"
if "dead_data" not in st.session_state:
    st.session_state.dead_data = load_table(DEAD_FILE)

# --- Input form ---
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

# --- Table Display + Actions ---
if st.session_state.dead_data:
    dead_df = pd.DataFrame(st.session_state.dead_data)
    dead_df.index += 1
    st.subheader("📊 Dead Rate Table")

    # Xóa toàn bộ
    if st.button("🗑️ Xóa toàn bộ Dead Table"):
        st.session_state.dead_data = []
        if os.path.exists(DEAD_FILE):
            os.remove(DEAD_FILE)
        st.success("✅ Dead Table cleared.")
        st.stop()

    # Hiển thị bảng với nút xóa từng dòng
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

# --- Input form ---
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

# --- Table Display + Actions ---
if st.session_state.dkp_data:
    dkp_df = pd.DataFrame(st.session_state.dkp_data)
    dkp_df.index += 1
    st.subheader("📊 Power DKP Table")

    # Xóa toàn bộ
    if st.button("🗑️ Xóa toàn bộ DKP Table"):
        st.session_state.dkp_data = []
        if os.path.exists(DKP_FILE):
            os.remove(DKP_FILE)
        st.success("✅ DKP Table cleared.")
        st.stop()

    # Hiển thị bảng với nút xóa từng dòng
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

# ==========================================
# 🔍 Lookup Tool
# ==========================================
st.markdown("---")
st.header("🔍 Lookup DKP / Dead Rate by Power")

power_value = st.number_input("Enter current Power:", min_value=0, step=1_000_000, format="%d")

if st.button("🔎 Calculate Results"):
    result_msg = ""

    # DKP lookup
    if st.session_state.dkp_data:
        match = [r for r in st.session_state.dkp_data if r["POWER_START"] <= power_value < r["POWER_END"]]
        if match:
            result_msg += f"⚔️ DKP: **{match[0]['DKP']:,}**\n"
        else:
            result_msg += "⚔️ DKP: Not found\n"

    # Dead lookup
    if st.session_state.dead_data:
        match = [r for r in st.session_state.dead_data if r["POWER_START"] <= power_value < r["POWER_END"]]
        if match:
            result_msg += f"💀 Dead DKP: **{match[0]['DEAD_DKP']:,}**"
        else:
            result_msg += "💀 Dead DKP: Not found"

    if result_msg:
        st.success(result_msg)
