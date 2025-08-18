# -*- coding: utf-8 -*-
"""
Created on Mon Aug 18 16:17:49 2025

@author: Sabina.Salakhova
"""

import streamlit as st
import pandas as pd
import io
import zipfile

from ags3_parser import AGS3_to_dataframe  # Your AGS3 parser
from ags4_parser import AGS4_to_dataframe  # Your AGS4 parser (assumed)

def detect_ags_version(file_content):
    """Detect AGS version based on file content."""
    text = file_content.decode('utf-8', errors='ignore')
    if '**AGS' in text:
        if '**AGS4' in text:
            return 'AGS4'
        elif '**AGS3' in text:
            return 'AGS3'
    return 'Unknown'

st.title("AGS File Processor (.ags ➜ DataFrame + Excel)")

uploaded_file = st.file_uploader("Upload an AGS file", type=["ags"])

if uploaded_file:
    content = uploaded_file.read()
    version = detect_ags_version(content)

    st.write(f"**Detected AGS Version:** {version}")

    if version == 'Unknown':
        st.error("Could not detect AGS version. Please upload a valid AGS3 or AGS4 file.")
    else:
        buffer = io.StringIO(content.decode('utf-8', errors='replace'))

        if version == 'AGS3':
            dataframes, headings = AGS3_to_dataframe(buffer)
        elif version == 'AGS4':
            dataframes, headings = AGS4_to_dataframe(buffer)

        st.success(f"Parsed {len(dataframes)} GROUP(s) from {version} file.")

        # Display and prepare Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            for group, df in dataframes.items():
                st.subheader(f"Group: {group}")
                st.dataframe(df.head())
                df.to_excel(writer, sheet_name=group[:31], index=False)
            writer.save()

        st.download_button(
            label="📥 Download Excel File",
            data=excel_buffer.getvalue(),
            file_name="ags_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
