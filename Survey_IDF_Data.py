import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- File Paths (Relative paths for cloud) ---
input_file = 'IDF_ACCT_ID.csv'
output_file = 'load_data.csv'
image_folder = 'idf_images'
os.makedirs(image_folder, exist_ok=True)

# --- Input File Check ---
if not os.path.exists(input_file):
    st.error(f"❌ File not found: {input_file}")
    st.stop()

# --- Load Master Data ---
df = pd.read_csv(input_file)

# --- Title ---
st.title("Supervisor Field Survey – IDF Cases")
st.caption("Please fill this form after on-site verification of IDF accounts.")

# --- Step 1: ACCT_ID Input ---
acct_id_input = st.text_input("**ENTER ACCT_ID**", max_chars=10)
if acct_id_input and (not acct_id_input.isdigit() or not (1 <= len(acct_id_input) <= 10)):
    st.error("❌ ACCT_ID should be numeric and 1 to 10 digits only.")
    st.stop()

# --- Step 2: Match ACCT_ID ---
if acct_id_input:
    match = df[df["ACCT_ID"].astype(str) == acct_id_input.strip()]

    if not match.empty:
        st.success("✅ ACCT_ID matched. Details below:")

        fields = {
            "ZONE": match.iloc[0]["ZONE"],
            "CIRCLE": match.iloc[0]["CIRCLE"],
            "DIVISION": match.iloc[0]["DIVISION"],
            "SUB-DIVISION": match.iloc[0]["SUB-DIVISION"]
        }

        cols = st.columns(len(fields))
        for col, (label, value) in zip(cols, fields.items()):
            col.markdown(f"<b>{label}:</b><br>{value}", unsafe_allow_html=True)

        st.markdown("---")

        # --- Step 3: Remark Dropdown ---
        remark_options = {
            "OK": ["METER SERIAL NUMBER", "METER IMAGE", "READING", "DEMAND"],
            "DEFECTIVE METER": ["METER SERIAL NUMBER", "METER IMAGE"],
            "LINE DISCONNECTED": ["METER SERIAL NUMBER", "METER IMAGE"],
            "NO METER AT SITE": ["PREMISES IMAGE"],
            "METER MIS MATCH": ["METER SERIAL NUMBER", "METER IMAGE", "METER READING", "DEMAND"],
            "HOUSE LOCK": ["PREMISES IMAGE"],
            "METER CHANGE NOT ADVISE": ["METER SERIAL NUMBER", "METER IMAGE", "METER READING", "DEMAND"],
            "PDC": ["METER IMAGE", "PREMISES IMAGE", "DOCUMENT RELATED TO PDC"]
        }

        required_remark_map = {
            "OK": "BILL REVISION REQUIRED",
            "DEFECTIVE METER": "METER REPLACEMENT REQUIRED",
            "LINE DISCONNECTED": "NEED RECONNECTION AFTER PAYMENT",
            "NO METER AT SITE": "PD/METER INSTALLATION",
            "METER MIS MATCH": "NEED METER NUMBER UPDATION",
            "PDC": "MASTER UPDATION REQUIRED"
        }

        selected_remark = st.selectbox("Select REMARK", [""] + list(remark_options.keys()))

        if selected_remark:
            mobile_no = ""
            if selected_remark != "HOUSE LOCK":
                mobile_no = st.text_input("**ENTER COUNSUMER MOBILE NUMBER**", max_chars=10)

            required_remark = required_remark_map.get(selected_remark, "")
            if required_remark:
                st.markdown(f"📝 **Required Remark:** `{required_remark}`")

            st.markdown("#### Enter Required Details:")

            input_data = {
                "MOBILE_NO": mobile_no if selected_remark != "HOUSE LOCK" else "",
                "REQUIRED_REMARK": required_remark,
                "METER_SERIAL_NUMBER": "",
                "READING": "",
                "DEMAND": ""
            }

            meter_images = []
            premises_images = []
            document_image = ""
            missing_fields = []

            for field in remark_options[selected_remark]:
                field_clean = field.replace(" ", "_").upper()

                if "IMAGE" in field or "DOCUMENT" in field:
                    image = st.camera_input(f"Capture {field}")
                    if image:
                        image_filename = f"{acct_id_input}_{field_clean}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                        image_path = os.path.join(image_folder, image_filename)
                        with open(image_path, "wb") as f:
                            f.write(image.getbuffer())
                        st.success(f"📸 {field} photo saved!")

                        if "METER IMAGE" in field.upper():
                            meter_images.append(image_path)
                        elif "PREMISES IMAGE" in field.upper():
                            premises_images.append(image_path)
                        elif "DOCUMENT RELATED TO PDC" in field.upper():
                            document_image = image_path
                    else:
                        missing_fields.append(field)
                else:
                    value = st.text_input(f"{field}")
                    if not value:
                        missing_fields.append(field)
                    key = field.replace(" ", "_").upper()
                    input_data[key] = value

            if selected_remark != "HOUSE LOCK" and (not mobile_no.isdigit() or len(mobile_no) != 10):
                st.warning("📵 Valid mobile number is required.")
                missing_fields.append("MOBILE_NO")

            if missing_fields:
                st.warning(f"⚠ Please fill required fields: {', '.join(missing_fields)}")
            else:
                if st.button("✅ Submit"):
                    record = {
                        "ACCT_ID": acct_id_input,
                        "REMARK": selected_remark,
                        **fields,
                        **input_data,
                        "METER_IMAGE_ALL": "; ".join(meter_images),
                        "PREMISES_IMAGE_ALL": "; ".join(premises_images),
                        "DOCUMENT_IMAGE": document_image
                    }

                    # Enforce column order
                    column_order = [
                        "ACCT_ID", "REMARK", "ZONE", "CIRCLE", "DIVISION", "SUB-DIVISION",
                        "MOBILE_NO", "REQUIRED_REMARK", "METER_SERIAL_NUMBER", "READING", "DEMAND",
                        "METER_IMAGE_ALL", "PREMISES_IMAGE_ALL", "DOCUMENT_IMAGE"
                    ]

                    result_df = pd.DataFrame([record])
                    result_df = result_df.reindex(columns=column_order)
                    write_header = not os.path.exists(output_file)
                    result_df.to_csv(output_file, mode='a', header=write_header, index=False)

                    st.success("🎉 Data submitted successfully!")

        else:
            st.info("Please select a remark to continue.")
    else:
        st.error("❌ ACCT_ID not found. Please check and try again.")
