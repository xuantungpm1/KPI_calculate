import os
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

# --- Helper functions ---
def get_dead_target(power_value, df_dead):
    for _, row in df_dead.iterrows():
        if row["Power_start"] <= power_value <= row["Power_end"]:
            return row["Target"]
    return 0

def get_dkp_target(power_value, df_dkp):
    for _, row in df_dkp.iterrows():
        if row["Power_start"] <= power_value <= row["Power_end"]:
            return (power_value * (row["Target"] / 100)).round(2)
    return 0

def get_point(type, df_point):
    for _, row in df_point.iterrows():
        if row['Type'] == type:
            return row['Points']
    return 0

# --- Safe conversion to gspread-compatible list of lists ---
def df_to_gspread(df: pd.DataFrame):
    df_safe = df.fillna("")  # Replace NaN with empty string
    # Convert all numpy types to native Python types (str/int/float)
    return [df_safe.columns.tolist()] + df_safe.astype(str).values.tolist()

# --- Folder setup ---
SAVE_DIR = "uploaded_data"
os.makedirs(SAVE_DIR, exist_ok=True)

st.title("📊 Upload data file and copy to Google Sheet")

uploaded_file = st.file_uploader("Upload your data file (KD3270_data.xlsx)", type=["xlsx"])

if uploaded_file:
    # --- Google auth ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open("KD3270 data sheet")

    # --- Read parameter tables ---
    df_dead = pd.DataFrame(spreadsheet.worksheet("dead_table").get_all_records())
    df_dkp = pd.DataFrame(spreadsheet.worksheet("dkp_table").get_all_records())
    df_point = pd.DataFrame(spreadsheet.worksheet("point_table").get_all_records())

    # --- Read uploaded Excel ---
    xls = pd.ExcelFile(uploaded_file)
    if "current" in xls.sheet_names:
        df_upload = pd.read_excel(uploaded_file, sheet_name="current")
        st.subheader("📄 Uploaded Data Preview")
        st.dataframe(df_upload)

        if "Power" not in df_upload.columns:
            st.error("❌ Uploaded file must have a 'Power' column.")
        else:
            # --- Compute targets and scores ---
            def make_first_data(df):
                df["Target DKP"] = df["Power"].apply(lambda x: get_dkp_target(x, df_dkp))
                df["Target Deads"] = df["Power"].apply(lambda x: get_dead_target(x, df_dead))
                df["Deads rate"] = ((df["Deads gained"] / df["Target Deads"]) * 100).round(2)
                df["Score"] = (
                    df["T4 Kills gained"] * get_point("T4", df_point) +
                    df["T5 Kills gained"] * get_point("T5", df_point) +
                    df["Deads gained"] * get_point("Dead", df_point)
                )
                df["DKP rate"] = ((df["Score"] / df["Target DKP"]) * 100).round(2)
                df["Rank"] = df["Score"].rank(ascending=False, method="min").astype(int)

                return df

            def compute_kpi(df):
                df["Deads rate"] = ((df["Deads gained"] / df["Target Deads"]) * 100).round(2)
                df["Score"] = (
                    df["T4 Kills gained"] * get_point("T4", df_point) +
                    df["T5 Kills gained"] * get_point("T5", df_point) +
                    df["Deads gained"] * get_point("Dead", df_point)
                )
                df["DKP rate"] = ((df["Score"] / df["Target DKP"]) * 100).round(2)
                df["Rank"] = df["Score"].rank(ascending=False, method="min").astype(int)

                return df

            st.subheader("Actions")
            row1_col1, row1_col2 = st.columns(2)
            if row1_col1.button("Create first data"):
                sheet_name = "data"
                sheet = spreadsheet.worksheet(sheet_name)
                df_final = make_first_data(df_upload)
                sheet.clear()
                sheet.update(df_to_gspread(df_final))
                st.success("✅ First data created successfully!")
            
            row2_col1, row2_col2 = st.columns(2)
            if row2_col1.button("Merge data"):
                try:
                    sheet = spreadsheet.worksheet("data")
                    df_old = pd.DataFrame(sheet.get_all_records())
                except gspread.exceptions.WorksheetNotFound:
                    st.error("❌ First data sheet not found. Please create first data first.")
                    st.stop()
                
                df_old["ID"] = df_old["ID"].astype(str)
                df_upload["ID"] = df_upload["ID"].astype(str)

                df_updated = df_old.copy()

                columns_to_update = ['Deads gained', 'KP gained', 'T5 Kills gained', 'T4 Kills gained']  # DataFrame column names

                for idx, row in df_upload.iterrows():
                    uid = row["ID"]
                    if uid in df_updated["ID"].values:
                        df_updated.loc[df_updated["ID"] == uid, columns_to_update] = row[columns_to_update]
                
                sheet.update(df_to_gspread(df_updated))
                st.success("✅ Existing IDs updated")

                start_row = 2
                for col_name in columns_to_update:
                    # 1. Find the column index (1-based)
                    col_index = df_upload.columns.get_loc(col_name) + 1
                    
                    # 2. Convert to column letter
                    col_letter = rowcol_to_a1(1, col_index)[:-1]  # 'A', 'B', ...
                    
                    # 3. Prepare the data (list of lists)
                    data_to_update = [[v] for v in df_upload[col_name].tolist()]
                    
                    # 4. Build range (from start_row to end_row)
                    end_row = start_row + len(data_to_update) - 1
                    cell_range = f"{col_letter}{start_row}:{col_letter}{end_row}"
                    
                    # 5. Update the sheet
                    sheet.update(cell_range, data_to_update)

                try:
                    sheet = spreadsheet.worksheet("data")
                    df_new = pd.DataFrame(sheet.get_all_records())
                except gspread.exceptions.WorksheetNotFound:
                    st.error("❌ First data sheet not found. Please create first data first.")
                    st.stop()
                
                df_final = compute_kpi(df_new)
                sheet.clear()
                sheet.update(df_to_gspread(df_final))
                st.success("✅ New data update successfully!")

    else:
        st.error("The uploaded Excel file does not contain a sheet named 'current'.")
