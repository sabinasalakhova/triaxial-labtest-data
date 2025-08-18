import streamlit as st
import pandas as pd
import io

from AGS3 import AGS3_to_dataframe
from AGS4 import AGS4_to_dataframe
from archival_util import analyze_ags_content

st.set_page_config(page_title="AGS File Processor", layout="wide")
st.title("📄 AGS File Processor (.ags ➜ DataFrame + Excel)")

uploaded_file = st.file_uploader("Upload an AGS file", type=["ags"])

if uploaded_file:
    st.info("🔍 Analyzing file content...")

    file_bytes = uploaded_file.read()
    file_stream_for_analysis = io.BytesIO(file_bytes)
    analysis_results = analyze_ags_content(file_stream_for_analysis)
    buffer = io.StringIO(file_bytes.decode('latin-1', errors='replace'))

    version = "AGS3" if analysis_results["AGS3"] == "Yes" else "AGS4" if analysis_results["AGS4"] == "Yes" else "Unknown"
    st.markdown(f"### 📌 **Detected AGS Version:** `{version}`")

    if version == "Unknown":
        st.error("❌ Could not detect AGS version. Please upload a valid AGS3 or AGS4 file.")
    else:
        try:
            if version == "AGS3":
                dataframes, headings, faulty_tables = AGS3_to_dataframe(buffer, collect_faulty_lines=True)
            elif version == "AGS4":
                dataframes, headings, faulty_tables = AGS4_to_dataframe(buffer, collect_faulty_lines=True)

            st.success(f"✅ Parsed `{len(dataframes)}` GROUP(s) from `{version}` file.")

            if faulty_tables:
                st.warning(f"⚠️ Skipped {len(faulty_tables)} faulty GROUP(s) during parsing.")
                for item in faulty_tables:
                    if len(item) == 2:
                        group, error = item
                        st.markdown(f"**GROUP `{group}`:** {error}")
                    elif len(item) == 3:
                        group, error, line = item
                        st.markdown(f"**GROUP `{group}` (Line {line}):** {error}")

            if dataframes:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    for group, df in dataframes.items():
                        st.subheader(f"📁 Group: `{group}`")
                        st.dataframe(df.head())
                        df.to_excel(writer, sheet_name=group[:31], index=False)
                    writer.save()

                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_buffer.getvalue(),
                    file_name="ags_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ No valid dataframes could be parsed from the file.")

        except Exception as e:
            st.error(f"⚠️ Unexpected error: {e}")