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
