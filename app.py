import streamlit as st
import pandas as pd
import re
import os
import matplotlib.pyplot as plt

def parse_ags(uploaded_file):
    """
    Parses AGS file to extract borehole name, specimen depth, test type, s', t', soil type, and source file.
    Assumes s' and t' values are in lines with test type keywords.
    """
    test_types = ['CUS', 'CUM', 'CU', 'UU', 'CD']
    borehole_data = []
    current_borehole = None
    soil_type = None

    # Read file as text
    lines = uploaded_file.read().decode('utf-8', errors='ignore').splitlines()
    for line in lines:
        # Extract borehole name
        if line.startswith('"') and ',' in line:
            parts = [p.strip('"') for p in line.split(',')]
            if len(parts) > 1 and parts[0].startswith('NOL'):
                current_borehole = parts[0]
        # Extract soil type if present
        if 'soil type' in line.lower():
            match = re.search(r'soil type,([^\n,]+)', line, re.IGNORECASE)
            if match:
                soil_type = match.group(1).strip()
        # Extract triaxial test data
        if any(tt in line for tt in test_types):
            test_type = next(tt for tt in test_types if tt in line)
            # Try to extract depth, s', t' from line
            numbers = re.findall(r'(\d+\.\d+|\d+)', line)
            depth = float(numbers[0]) if len(numbers) > 0 else None
            s_val = float(numbers[1]) if len(numbers) > 1 else None
            t_val = float(numbers[2]) if len(numbers) > 2 else None
            borehole_data.append({
                'Borehole': current_borehole,
                'Depth': depth,
                "s'": s_val,
                "t'": t_val,
                'TestType': test_type,
                'SoilType': soil_type,
                'SourceFile': uploaded_file.name
            })
    return pd.DataFrame(borehole_data)

def plot_st_graph(df, ref_slope=None, ref_yint=None):
    fig, ax = plt.subplots()
    ax.scatter(df["s'"], df["t'"], label='Lab Data')
    if ref_slope is not None and ref_yint is not None:
        s_range = [df["s'"].min(), df["s'"].max()]
        t_ref = [ref_slope * s + ref_yint for s in s_range]
        ax.plot(s_range, t_ref, color='red', label='Reference Line')
    ax.set_xlabel("s' (kN/m2)")
    ax.set_ylabel("t' (kN/m2)")
    ax.legend()
    st.pyplot(fig)

st.title("Triaxial Lab Test Data Analyzer")

ags_file = st.file_uploader("Upload AGS File", type=['ags'])

if ags_file:
    ags_df = parse_ags(ags_file)
    st.subheader("Extracted Borehole/Test Data")
    st.dataframe(ags_df)

    ref_slope = st.number_input("Reference Line Slope", value=0.57)
    ref_yint = st.number_input("Reference Line Y-Intercept", value=3.27)

    if not ags_df.empty and "s'" in ags_df.columns and "t'" in ags_df.columns:
        st.subheader("Plot s' vs t' Graph")
        plot_st_graph(ags_df, ref_slope, ref_yint)
    else:
        st.info("No s' and t' data found in AGS file for plotting. Please check your AGS file format.")
else:
    st.info("Please upload an AGS file to proceed")
    