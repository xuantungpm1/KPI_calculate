import streamlit as st
import pandas as pd

st.set_page_config(page_title="Excel Viewer", layout="wide")

st.title("📊 Excel File Viewer")

# Upload Excel file
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        st.success("✅ File loaded successfully!")
        
        # Display column and row info
        st.write(f"**Columns:** {list(df.columns)}")
        st.write(f"**Total Rows:** {len(df)}")

        # Display data
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("👆 Please upload an Excel file to begin.")

st.set_page_config(page_title="DKP KPI Table", layout="centered")

st.title("⚔️ DKP KPI Table (Power Range - DKP)")

# --- Khởi tạo dữ liệu ---
if "dkp_data" not in st.session_state:
    st.session_state.dkp_data = []

# --- Nhập dữ liệu ---
st.header("🧮 Nhập dữ liệu DKP")

with st.form("dkp_form", clear_on_submit=True):
    power_start = st.number_input("Power Start", min_value=0, step=1_000_000, format="%d")
    power_end = st.number_input("Power End", min_value=0, step=1_000_000, format="%d")
    dkp_value = st.number_input("DKP (Goal)", min_value=0, step=50_000, format="%d")

    submitted = st.form_submit_button("➕ Thêm dòng")
    if submitted and power_end > power_start:
        st.session_state.dkp_data.append({
            "POWER_START": power_start,
            "POWER_END": power_end,
            "DKP": dkp_value
        })
        st.success("✅ Đã thêm dòng mới!")

# --- Hiển thị bảng DKP ---
if st.session_state.dkp_data:
    df = pd.DataFrame(st.session_state.dkp_data)
    df.index += 1
    st.session_state.dkp_df = df.copy()

    st.subheader("📊 Bảng DKP theo Power Range")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "💾 Tải xuống Excel",
        data=df.to_excel(index=False, engine="openpyxl"),
        file_name="dkp_table.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("👆 Nhập ít nhất một dòng để bắt đầu.")

# --- Tính DKP theo Power thực tế ---
st.markdown("---")
st.header("⚡ Tính DKP theo Power")

if "dkp_df" in st.session_state:
    df = st.session_state.dkp_df
    power_input = st.number_input("Nhập Power thực tế:", min_value=0, step=1_000_000, format="%d")

    if st.button("🔍 Tính DKP"):
        matched = df[(df["POWER_START"] <= power_input) & (power_input < df["POWER_END"])]

        if not matched.empty:
            dkp_result = matched.iloc[0]["DKP"]
            st.success(f"💰 Power {power_input:,} có DKP = {dkp_result:,}")
        else:
            st.warning("⚠️ Power không nằm trong khoảng nào của bảng DKP.")
else:
    st.info("⚠️ Vui lòng nhập bảng DKP trước khi tính toán.")
