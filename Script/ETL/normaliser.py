import re
import pandas as pd

def normalize_year(value):
    """
    Convert different year formats into an integer year.

    Examples:
        '2023'      -> 2023
        2023.0      -> 2023
        'Dec 2025'  -> 2025
        'Mar-2018'  -> 2018
        'FY2021'    -> 2021
    """

    if pd.isna(value):
        return None

    # Already numeric
    if isinstance(value, (int, float)):
        return int(value)

    value = str(value).strip()

    # Find a 4-digit year anywhere in the string
    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    return None

def normalize_ticker(value):
     """
        standerdize stock ticker names.
        example:
        'tcs' -> 'TCS'
     """

     if pd.isna(value):
         return None
        
     return str(value).strip().upper()

def normalize_text(value):
    """
    Remove leading/trailing spaces.
    """
    if pd.isna(value):
        return None 

    return str(value).strip()

def normalize_column_names(df):
    """
    convert column names to lowercase with underscores.
    example:
    Company Name -> Company_name
    """
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ","_")
    )
    return df 