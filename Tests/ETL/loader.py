import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from normaliser import normalize_column_names

# Load environment variables
load_dotenv()

RAW_DATA = os.getenv("RAW_DATA")
PROCESSED_DATA = os.getenv("PROCESSED_DATA")

def load_excel(file_path):
    """
    Read an Excel file using the second row as the header.
    """

    try:

        df = pd.read_excel(
            file_path,
            header=1
        )

        df = normalize_column_names(df)

        return df

    except Exception as e:

        print(f"❌ Error reading {file_path.name}")

        print(e)

        return None

def load_excel(file_path):
    """
    Read an Excel file using the second row as the header.
    """

    try:

        df = pd.read_excel(
            file_path,
            header=1
        )

        df = normalize_column_names(df)

        return df

    except Exception as e:

        print(f"❌ Error reading {file_path.name}")

        print(e)

        return None

def display_info(file_name, df):

    print("\n" + "=" * 70)

    print(f"File : {file_name}")

    print(f"Rows : {df.shape[0]}")

    print(f"Columns : {df.shape[1]}")

    print("\nColumn Names")

    print(df.columns.tolist())

    print("=" * 70)

def save_processed(file_name, df):

    output_name = file_name.replace(".xlsx", ".csv")

    output_path = os.path.join(
        PROCESSED_DATA,
        output_name
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(f"✅ Saved : {output_name}")

def process_all_files():

    raw_folder = Path(RAW_DATA)

    excel_files = list(raw_folder.glob("*.xlsx"))

    print(f"\nFound {len(excel_files)} Excel files\n")

    for file in excel_files:

        print(f"\nLoading {file.name}")

        df = load_excel(file)

        if df is not None:

            display_info(file.name, df)

            save_processed(file.name, df)

if __name__ == "__main__":

    process_all_files()