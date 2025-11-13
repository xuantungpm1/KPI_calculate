import os
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Helper functions ---
def get_dead_target(power_value, df_dead):
    for _, row in df_dead.iterrows():
        if row["Power_start"] <= power_value <= row["Power_end"]:
            return row["Target"]
    return 0

def get_dkp_target(power_value, df_dkp):
    for _, row in df_dkp.iterrows():
        if row["Power_start"] <= power_value <= row["Power_end"]:
            return power_value * (row["Target"] / 100)
    return 0

def get_point(type, df_point):
    for _, row in df_point.iterrows():
        if row['Type'] == type:  # ← fix: use ==, not "is"
            return row['Points']
    return 0

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

    spreadsheet = client.open("MyTestSheet")

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
    else:
        st.error("The uploaded Excel file does not contain a sheet named 'current'.")
        return

    if "Power" not in df_upload.columns:
        st.error("❌ Uploaded file must have a 'Power' column.")
    else:
        df_upload["Target DKP"] = df_upload["Power"].apply(lambda x: get_dkp_target(x, df_dkp))
        df_upload["Target Deads"] = df_upload["Power"].apply(lambda x: get_dead_target(x, df_dead))
    
    df_upload["Deads rate"] = ((df_upload["Deads gained"] / df_upload["Target Deads"]) * 100).round(2)
    df_upload["Score"] = (df_upload["T4 kill gained"] * df_point["T4"] + df_upload["T5 kill gained"] * df_point["T5"] + df_upload["Dead gained"] * df_point["Dead"])
    df_upload["DKP rate"] = ((df_upload["Score"] / df_upload["Target DKP"]) * 100).round(2)
    df_upload["Rank"] = df["Score"].rank(ascending=False, method="min").astype(int)

    # --- Prepare target sheet ---
    sheet_name = "data"
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        # optional: clear old data before writing new
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)

    # --- Write DataFrame to sheet ---
    # Convert DataFrame to list of lists (including header)
    data_to_write = [df_upload.columns.values.tolist()] + df_upload.values.tolist()
    sheet.update(data_to_write)

    st.success(f"✅ Uploaded data copied successfully to Google Sheet tab '{sheet_name}'!")
