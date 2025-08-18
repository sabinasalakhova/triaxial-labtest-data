# Adopted to AGS3 based on the python_ags4
#
# Copyright (C) 2020-2025  Asitha Senanayake
#
# This file is part of python_ags4.
#
# python_ags4 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# https://github.com/asitha-sena/python-ags4
# https://gitlab.com/ags-data-format-wg/ags-python-library

import pandas as pd
import logging

logger = logging.getLogger(__name__)


# Read functions #

def AGS3_to_dict(filepath_or_buffer, encoding='utf-8'):
    """Load all the data in a AGS3 file to a dictionary of dictionaries.
    This GROUP in the AGS3 file is assigned its own dictionary.

    'AGS3_to_dataframe' uses this funtion to load AGS3 data in to Pandas
    dataframes.

    Parameters
    ----------
    filepath_or_buffer : File path (str, pathlib.Path), or StringIO.
        Path to AGS3 file or any object with a read() method (such as an open file or StringIO).

    Returns
    -------
    data : dict
        Python dictionary populated with data from the AGS3 file with AGS3 headers as keys
    headings : dict
        Dictionary with the headings in the each GROUP (This will be needed to
        recall the correct column order when writing pandas dataframes back to AGS3
        files. i.e. input for 'dataframe_to_AGS3()' function)
    """

    if is_file_like(filepath_or_buffer):
        f = filepath_or_buffer
        close_file = False
    else:
        # Read file with errors="replace" to catch UnicodeDecodeErrors
        f = open(filepath_or_buffer, "r", encoding=encoding, errors="replace")
        close_file = True

    try:

        data = {}

        # dict to save and output the headings. This is not really necessary
        # for the read AGS3 function but will be needed to write the columns
        # of pandas dataframes when writing them back to AGS3 files.
        # (The HEADING column needs to be the first column in order to preserve
        # the AGS data format. Other columns in certain groups have a
        # preferred order as well)
        
        headings = {}

        for i, line in enumerate(f, start=1):
            temp = line.rstrip().split('","')
            temp = [item.strip('"') for item in temp]

            if '**' in temp[0]: # GROUP
                row = 0
                group = temp[0][2:]
                data[group] = {}

            elif '*' in temp[0]: # HEADING
                row += 1
                cleaned_headings = [item[1:] for item in temp]
                
                if row==1:
                    headings[group] = cleaned_headings
                
                # for the exceptions where the columns are split into different rows
                else: 
                    headings[group].extend(cleaned_headings)
                    
                ## Catch duplicate headings
                try:
                    assert len(headings[group])==len(set(headings[group]))
                except AssertionError:
                    item_count = {}

                    for i, item in enumerate(headings[group]):
                        if item not in item_count:
                            item_count[item] = {'i': i, 'count': 0}
                        else:
                            item_count[item]['i'] = i
                            item_count[item]['count'] += 1

                            headings[group][i] = headings[group][i]+'_'+str(item_count[item]['count'])
                
                for item in headings[group]:
                    data[group][item] = []
                    
            elif '<CONT>' in temp[0]:
                # for the exceptions where the columns are split into 
                # different rows
                for i in range(1, len(temp)):
                    data[group][headings[group][i]][-1] += temp[i]
                    
            elif len(temp[0])==0 and len(temp)==1: # GROUP BREAKS
                continue
                
            else: # DATA / UNITS
                for i in range(len(temp)):
                    data[group][headings[group][i]].append(temp[i])
                
    finally:
        if close_file:
            f.close()

    return data, headings


def AGS3_to_dataframe(filepath_or_buffer, encoding='utf-8'):
    """Load all the tables in a AGS3 file to a Pandas dataframes. The output is
    a Python dictionary of dataframes with the name of each AGS3 table (i.e.
    GROUP) as the primary key.

    Parameters
    ----------
    filepath_or_buffer : str, StringIO
        Path to AGS3 file or any file like object (open file or StringIO)

    Returns
    -------
    data : dict
        Python dictionary populated with Pandas dataframes. Each GROUP in the AGS3 files is assigned to its a dataframe.
    headings : dict
        Dictionary with the headings in the each GROUP (This will be needed to
        recall the correct column order when writing pandas dataframes back to AGS3
        files. i.e. input for 'dataframe_to_AGS3()' function)
    """

    from pandas import DataFrame

    # Extract AGS3 file into a dictionary of dictionaries
    data, headings = AGS3_to_dict(filepath_or_buffer, encoding=encoding)
    
    # Convert dictionary of dictionaries to a dictionary of Pandas dataframes
    df = {}
    for key in data:
        try:
            table = DataFrame(data[key])
            if len(table) == 0: 
                continue
            #table[1:] = table[1:].apply(pd.to_numeric, errors='ignore')
            df[key] = table
        except ValueError:
            splitted = filepath_or_buffer.rsplit("/",2)
            splitted = str(splitted[1:2])
            print(splitted + ": ")
            print ('check file: {} is not exported'.format(key))
            
            continue
    return df, headings


def is_file_like(obj):
    """Check if object is file like

    Returns
    -------
    bool
        Return True if obj is file like, otherwise return False
    """

    if not (hasattr(obj, 'read') or hasattr(obj, 'write')):
        return False

    if not hasattr(obj, "__iter__"):
        return False

    return True
