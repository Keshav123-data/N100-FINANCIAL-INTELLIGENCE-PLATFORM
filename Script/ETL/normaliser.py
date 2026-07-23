import pandas as pd 

def normalize_year(value):
    """
    convert different year formats into an integer year.
    example:
    '2023' -> 2023
    2023.0 -> 2023
    """
    if pd.isna(value):
        return None

    try:
        return int(float(value))
    except (ValueError,TypeError):
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