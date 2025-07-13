import streamlit as st
import pandas as pd
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# --- Constants ---
CREDENTIALS_FILE = 'credentials.json'
GOOGLE_SHEET_ID = '1UGrGEtWy5coI7nduIY8J8Vjh9S0Ahej7ekDG_4nl-SQ'
DRIVE_FOLDER_ID = '1l6N7Gfd8T1V8t3hR2OuLn5CDtBuzjsKu'

# --- Google Sheets Auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

# --- Google Drive Auth ---
gauth = GoogleAuth()
gauth.DEFAULT_SETTINGS['client_config_file'] = CREDENTIALS_FILE
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# --- Load ACCT_ID master CSV ---
if not os.path.exists("IDF_ACCT_ID.csv"):
    st.error("❌ 'IDF_ACCT_ID.csv' not found in app folder.")
    st.stop()

df = pd.read_csv("IDF_ACCT_ID.csv")

# --- UI ---
st.title("Supervisor Field Survey – IDF Cases")
st.caption("Please fill this form after on-site verification.")

acct_id = st.text_input("Enter ACCT_ID", max_chars=10)

if acct_id:
    match = df[df["ACCT_ID"].astype(str) == acct_id.strip()]
    if match.empty:
        st.error("❌ ACCT_ID not found.")
    else:
        row = match.iloc[0]
        fields = {
            "ZONE": row["ZONE"],
            "CIRCLE": row["CIRCLE"],
            "DIVISION": row["DIVISION"],
            "SUB-DIVISION": row["SUB-DIVISION"]
        }

        st.success("✅ ACCT_ID matched:")
        cols = st.columns(len(fields))
        for col, (label, value) in zip(cols, fields.items()):
            col.markdown(f"**{label}**: {value}")

        remark_options = {
            "OK": ["METER SERIAL NUMBER", "METER IMAGE", "READING", "DEMAND"],
            "NO METER AT SITE": ["PREMISES IMAGE"],
            "PDC": ["METER IMAGE", "PREMISES IMAGE", "DOCUMENT RELATED TO PDC"]
        }

        selected_remark = st.selectbox("Select REMARK", [""] + list(remark_options.keys()))
        if selected_remark:
            st.subheader("Additional Inputs")
            mobile = st.text_input("Consumer Mobile Number (10 digits)")

            images = {}
            inputs = {}

            for field in remark_options[selected_remark]:
                if "IMAGE" in field or "DOCUMENT" in field:
                    uploaded = st.file_uploader(f"Upload {field}", type=["jpg", "jpeg", "png"])
                    if uploaded:
                        file_name = f"{acct_id}_{field.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                        file_drive = drive.CreateFile({
                            'title': file_name,
                            'parents': [{'id': DRIVE_FOLDER_ID}]
                        })
                        file_drive.SetContentFile(uploaded.name)
                        with open(uploaded.name, 'wb') as f:
                            f.write(uploaded.read())
                        file_drive.Upload()
                        images[field] = file_drive['alternateLink']
                else:
                    inputs[field] = st.text_input(f"{field}")

            if st.button("✅ Submit"):
                row_data = [
                    acct_id,
                    selected_remark,
                    fields["ZONE"],
                    fields["CIRCLE"],
                    fields["DIVISION"],
                    fields["SUB-DIVISION"],
                    mobile,
                    "",  # REQUIRED_REMARK placeholder
                    inputs.get("METER SERIAL NUMBER", ""),
                    inputs.get("READING", ""),
                    inputs.get("DEMAND", ""),
                    images.get("METER IMAGE", ""),
                    images.get("PREMISES IMAGE", ""),
                    images.get("DOCUMENT RELATED TO PDC", "")
                ]
                sheet.append_row(row_data)
                st.success("✅ Data and images saved permanently!")
