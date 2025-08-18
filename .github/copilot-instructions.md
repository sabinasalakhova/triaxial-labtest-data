# Copilot Instructions for triaxial-labtest-data

## Project Overview
This repository is focused on extracting, analyzing, and visualizing triaxial lab test data from AGS files (geotechnical data format). The main user workflow is via a Streamlit app (`app.py`) that allows users to upload AGS files, parses relevant test data, and plots s' vs t' graphs for geotechnical analysis.

## Key Files & Structure
- `app.py`: Main Streamlit application. Handles file upload, AGS parsing, data extraction, and plotting. All user interaction is through this file.
- AGS files: Uploaded by users, parsed for borehole name, specimen depth, test type, s', t', soil type, and source file.
- No test suite or build scripts are present; the workflow is interactive and data-driven.

## Data Flow & Patterns
- **File Upload**: User uploads a `.ags` file via Streamlit UI.
- **Parsing**: `parse_ags()` reads the file line-by-line, extracting:
  - Borehole name (lines starting with 'NOL')
  - Soil type (lines containing 'soil type')
  - Triaxial test data (lines containing test type keywords: CUS, CUM, CU, UU, CD)
  - s', t', and depth values (extracted via regex from test data lines)
- **Visualization**: `plot_st_graph()` uses matplotlib to plot s' vs t' and overlays a user-defined reference line.
- **No CSV Upload**: Only AGS files are supported for input; CSV parsing is not part of the current workflow.

## Conventions & Patterns
- All data extraction is performed in-memory; no persistent storage or database.
- DataFrames are used for all tabular data manipulation and display.
- UI is minimal: file upload, data table, reference line input, and plot.
- Error handling is user-facing (Streamlit info messages if data is missing).
- All plotting and data extraction logic is in `app.py`.

## Integration Points & Dependencies
- **Streamlit**: For UI and app logic.
- **pandas**: For data manipulation.
- **matplotlib**: For plotting.
- **re**: For regex-based parsing.

## Example Patterns
- Extracting s', t', and depth:
  ```python
  numbers = re.findall(r'(\d+\.\d+|\d+)', line)
  depth = float(numbers[0]) if len(numbers) > 0 else None
  s_val = float(numbers[1]) if len(numbers) > 1 else None
  t_val = float(numbers[2]) if len(numbers) > 2 else None
  ```
- Plotting reference line:
  ```python
  s_range = [df["s'"] .min(), df["s'"] .max()]
  t_ref = [ref_slope * s + ref_yint for s in s_range]
  ax.plot(s_range, t_ref, color='red', label='Reference Line')
  ```

## How to Extend
- To support new AGS fields, update `parse_ags()` to extract additional columns.
- For new visualizations, add plotting functions and UI elements in `app.py`.

## No Build/Test Workflow
- There are no build scripts, test runners, or CI/CD. All development is interactive via Streamlit.

---

If any section is unclear or missing, please provide feedback so this guide can be improved for future AI agents.
