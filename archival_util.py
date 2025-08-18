import zipfile
import io
import openpyxl
from openpyxl import Workbook
import os
import pathlib
import csv

def analyze_ags_content(ags_file_stream):
    """
    Analyzes the content of a single AGS file stream for specific keywords and structures.

    Args:
        ags_file_stream: A file-like object (stream) of the AGS file content.

    Returns:
        A dictionary containing the results of the analysis.
    """
    results = {
        "AGS3": "No",
        "AGS4": "No",
        "Contains **HOLE": "No",
        'Contains "LOCA"': "No",
    }

    try:
        # Use 'latin-1' encoding which is robust for various data files.
        # Read all lines into a list for multiple checks without re-reading the stream.
        ags_content_wrapper = io.TextIOWrapper(ags_file_stream, encoding='latin-1')
        lines = list(ags_content_wrapper)

        if not lines:
            return results # Return default values for empty files

        # --- Analyze the first line to see if AGS3 or AGS4---
        
        for line in lines:
            if line.startswith('"GROUP"'):
                results["AGS4"] = "Yes"

                # --- Check for "GROUP" or "LOCA" in any line ---
                for line in lines:
                    if '"GROUP","LOCA"' in line.strip(' '):
                        results['Contains "LOCA"'] = "Yes"
                        break
                break
        
        # --- Check for AGS3 ---
            elif line.startswith('"**PROJ"'):
                results["AGS3"] = "Yes"

                # --- Check for '**HOLE' in any line ---
                for line in lines:
                    if "**HOLE" in line:
                        results["Contains **HOLE"] = "Yes"
                        break
                break
        
    except Exception as e:
        print(f"  - Warning: Could not fully analyze an AGS file. Error: {e}")
        # Return default values if any error occurs during analysis
        return results

    return results


def analyze_zip_files(main_zip_path, output_excel_path):
    """
    Analyzes a zip file that contains other zip files, extracting detailed
    information about the contents and saving the summary to an Excel file.

    Args:
        main_zip_path (str): The path to the main zip file.
        output_excel_path (str): The path to save the output Excel file.
    """
    # Create a new Excel workbook and select the active sheet
    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Zip File Analysis"

        # Define and write the headers for the new columns
        headers = [
            "Sub-ZIP File Name", "Sub-Folder", "Content File Name",
            'AGS3', 'AGS4', "Contains **HOLE", 'Contains "LOCA"'
        ]
        sheet.append(headers)
    except Exception as e:
        print(f"Error creating Excel workbook: {e}")
        return

    # Check if the main zip file exists
    if not os.path.exists(main_zip_path):
        print(f"Error: The file '{main_zip_path}' was not found.")
        return

    try:
        # Open the main zip file for reading
        with zipfile.ZipFile(main_zip_path, 'r') as main_zip:
            # Iterate through each item in the main zip archive
            for sub_zip_info in main_zip.infolist():
                if sub_zip_info.filename.lower().endswith('.zip'):
                    sub_zip_filename = sub_zip_info.filename
                    print(f"Processing sub-zip: {sub_zip_filename}")

                    try:
                        # Read the sub-zip file into an in-memory buffer to avoid extraction
                        sub_zip_data = main_zip.read(sub_zip_info.filename)
                        sub_zip_buffer = io.BytesIO(sub_zip_data)

                        with zipfile.ZipFile(sub_zip_buffer, 'r') as sub_zip:
                            # Iterate through each file within the sub-zip
                            for content_file_info in sub_zip.infolist():
                                # --- Requirement: Delete pure folder rows ---
                                # is_dir() correctly identifies directory entries in a zip file.
                                if content_file_info.is_dir():
                                    continue

                                # --- Requirement: Add the sub-folder as a column ---
                                # Use pathlib to easily separate path and filename
                                full_path = pathlib.Path(content_file_info.filename)
                                sub_folder = str(full_path.parent)
                                # Display '.' as empty for root files for clarity
                                if sub_folder == '.':
                                    sub_folder = ''
                                content_filename = full_path.name

                                # Initialize analysis results with default values
                                analysis_results = {
                                    "AGS3": "N/A",
                                    "AGS4": "N/A",
                                    "Contains **HOLE": "N/A",
                                    'Contains "LOCA"': "N/A",
                                }

                                # If the file is an .ags file, perform the detailed analysis
                                if content_filename.lower().endswith('.ags'):
                                    with sub_zip.open(content_file_info) as ags_file:
                                        analysis_results = analyze_ags_content(ags_file)

                                # Assemble the row for the Excel sheet
                                row_data = [
                                    sub_zip_filename,
                                    sub_folder,
                                    content_filename,
                                    analysis_results["AGS3"],
                                    analysis_results["AGS4"],
                                    analysis_results["Contains **HOLE"],
                                    analysis_results['Contains "LOCA"'],
                                ]
                                sheet.append(row_data)

                    except zipfile.BadZipFile:
                        print(f"  - Skipping corrupted or invalid zip file: {sub_zip_filename}")
                        sheet.append([sub_zip_filename, "Error: Bad Zip File", "N/A", "N/A", "N/A", "N/A", "N/A"])
                    except Exception as e:
                        print(f"  - An error occurred while processing {sub_zip_filename}: {e}")
                        sheet.append([sub_zip_filename, f"Error: {e}", "N/A", "N/A", "N/A", "N/A", "N/A"])

    except FileNotFoundError:
        print(f"Error: Main zip file not found at '{main_zip_path}'")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    # Save the final Excel workbook
    try:
        workbook.save(output_excel_path)
        print(f"\nAnalysis complete. Results saved to '{output_excel_path}'")
    except Exception as e:
        print(f"Error saving Excel file: {e}")


def extract_nested_zips(main_zip_path, selected_names, output_base_path):
    """
    Extracts contents from selected nested zip files within a main archive
    into folders named after the nested zips, avoiding extra nested folders.

    This version assumes the nested zips (e.g., '10000.zip') already contain
    a root folder of the same name (e.g., '10000/').

    Args:
        main_zip_path (str or pathlib.Path):
            The full path to the main .zip file.

        selected_names (list of str):
            A list of the base names of the nested zips to extract.
            Example: ['10000', '20000']

        output_base_path (str or pathlib.Path):
            The path to the directory where the new folder structure will be created.
            Example: 'path/to/output/main'
    """
    # --- 1. Setup Paths and Validate Inputs ---
    main_zip_path = pathlib.Path(main_zip_path)
    output_base_path = pathlib.Path(output_base_path)

    if not main_zip_path.is_file():
        print(f"Error: Main zip file not found at '{main_zip_path}'")
        return

    # Create the main output directory (e.g., 'main'). This is the ONLY
    # directory we create ourselves.
    try:
        output_base_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create base output directory '{output_base_path}'. Reason: {e}")
        return

    selected_set = set(selected_names)

    print(f"Starting process for '{main_zip_path}'...")
    print(f"Output will be saved in '{output_base_path}'")

    # --- 2. Open the Main Zip and Process Each Nested Zip ---
    try:
        with zipfile.ZipFile(main_zip_path, 'r') as main_zip:
            for zip_info in main_zip.infolist():
                if zip_info.is_dir() or not zip_info.filename.lower().endswith('.zip'):
                    continue

                file_stem = pathlib.Path(zip_info.filename).stem

                if file_stem in selected_set:
                    print(f"\nProcessing selected sub-zip: '{zip_info.filename}'")

                    # --- CORE LOGIC CHANGE ---
                    # We no longer create the sub-directory manually.
                    # We will extract directly into the 'output_base_path' and let
                    # the zip utility create the '10000/' folder for us.

                    # a) Read the nested zip into an in-memory byte stream
                    sub_zip_data = main_zip.read(zip_info.filename)
                    sub_zip_stream = io.BytesIO(sub_zip_data)

                    # b) Open the in-memory stream and extract its contents
                    with zipfile.ZipFile(sub_zip_stream, 'r') as sub_zip:
                        print(f"  -> Extracting contents into '{output_base_path}'...")
                        
                        # THE FIX: The 'path' is now the main output directory.
                        # The zip file's internal folder structure will be
                        # created relative to this path.
                        sub_zip.extractall(path=output_base_path)

    except zipfile.BadZipFile:
        print(f"Error: '{main_zip_path}' is not a valid zip file or is corrupted.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    print("\nProcess complete.")