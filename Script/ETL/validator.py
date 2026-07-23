import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# ======================================================
# Load Environment Variables
# ======================================================

load_dotenv()

PROCESSED_DATA = os.getenv("PROCESSED_DATA")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

os.makedirs(OUTPUT_DIR, exist_ok=True)

validation_failures = []


# ======================================================
# Utility Function
# ======================================================

def add_failure(rule,
                severity,
                table,
                row,
                column,
                message):

    validation_failures.append({

        "Rule": rule,
        "Severity": severity,
        "Table": table,
        "Row": row,
        "Column": column,
        "Message": message

    })


# ======================================================
# Load All CSV Files
# ======================================================

def load_tables():

    tables = {}

    processed_folder = Path(PROCESSED_DATA)

    csv_files = processed_folder.glob("*.csv")

    for file in csv_files:

        print(f"Loading {file.name}")

        tables[file.stem] = pd.read_csv(file)

    return tables


# ======================================================
# DQ01
# Primary Key Validation
# ======================================================

def dq01_primary_key(df,
                     table,
                     pk_column):

    print(f"Running DQ01 : {table}")

    duplicates = df[df[pk_column].duplicated()]

    if duplicates.empty:

        print("Passed")

        return

    for index, row in duplicates.iterrows():

        add_failure(

            "DQ01",
            "CRITICAL",
            table,
            index + 1,
            pk_column,
            "Duplicate Primary Key"

        )


# ======================================================
# DQ02
# Company-Year Duplicate
# ======================================================

def dq02_company_year(df,
                      table):

    if "company_id" not in df.columns:
        return

    if "year" not in df.columns:
        return

    print(f"Running DQ02 : {table}")

    duplicates = df[df.duplicated(

        subset=["company_id", "year"]

    )]

    if duplicates.empty:

        print("Passed")

        return

    for index, row in duplicates.iterrows():

        add_failure(

            "DQ02",
            "CRITICAL",
            table,
            index + 1,
            "company_id,year",
            "Duplicate Company-Year"

        )


# ======================================================
# DQ03
# Foreign Key
# ======================================================

def dq03_foreign_key(companies,
                     child,
                     table):

    if "company_id" not in child.columns:
        return

    print(f"Running DQ03 : {table}")

    invalid = child[
        ~child["company_id"].isin(
            companies["id"]
        )
    ]

    if invalid.empty:

        print("Passed")

        return

    for index, row in invalid.iterrows():

        add_failure(

            "DQ03",
            "CRITICAL",
            table,
            index + 1,
            "company_id",
            "Invalid Company ID"

        )
def dq04_balance_sheet(df, table):

    required = [
        "total_assets",
        "total_liabilities",
        "equity"
    ]

    if not all(col in df.columns for col in required):
        return

    print(f"Running DQ04 : {table}")

    for index, row in df.iterrows():

        assets = row["total_assets"]
        liabilities = row["total_liabilities"]
        equity = row["equity"]

        if pd.isna(assets) or pd.isna(liabilities) or pd.isna(equity):
            continue

        difference = abs(assets - (liabilities + equity))

        if assets != 0 and difference > (assets * 0.01):

            add_failure(
                "DQ04",
                "WARNING",
                table,
                index + 1,
                "total_assets",
                "Balance Sheet mismatch (>1%)"
            )

def dq05_opm(df, table):

    required = [
        "sales",
        "operating_profit",
        "opm_percentage"
    ]

    if not all(col in df.columns for col in required):
        return

    print(f"Running DQ05 : {table}")

    for index, row in df.iterrows():

        if row["sales"] == 0:
            continue

        calculated = (
            row["operating_profit"] /
            row["sales"]
        ) * 100

        if abs(calculated - row["opm_percentage"]) > 1:

            add_failure(
                "DQ05",
                "WARNING",
                table,
                index + 1,
                "opm_percentage",
                "Incorrect OPM"
            )

def dq06_positive_sales(df, table):

    if "sales" not in df.columns:
        return

    print(f"Running DQ06 : {table}")

    invalid = df[df["sales"] < 0]

    for index, row in invalid.iterrows():

        add_failure(
            "DQ06",
            "CRITICAL",
            table,
            index + 1,
            "sales",
            "Negative Sales"
        )

def dq07_cashflow(df, table):

    required = [
        "cash_from_operating_activity",
        "cash_from_investing_activity",
        "cash_from_financing_activity",
        "net_cash_flow"
    ]

    if not all(col in df.columns for col in required):
        return

    print(f"Running DQ07 : {table}")

    for index, row in df.iterrows():

        calculated = (

            row["cash_from_operating_activity"]

            +

            row["cash_from_investing_activity"]

            +

            row["cash_from_financing_activity"]

        )

        if abs(calculated - row["net_cash_flow"]) > 1:

            add_failure(

                "DQ07",

                "WARNING",

                table,

                index + 1,

                "net_cash_flow",

                "Net Cash Flow mismatch"

            )

def dq08_tax(df, table):

    if "tax_percentage" not in df.columns:
        return

    invalid = df[

        (df["tax_percentage"] < 0)

        |

        (df["tax_percentage"] > 100)

    ]

    for index, row in invalid.iterrows():

        add_failure(

            "DQ08",

            "WARNING",

            table,

            index + 1,

            "tax_percentage",

            "Invalid Tax Percentage"

        )

def dq09_dividend(df, table):

    required = [

        "dividend_payout",

        "net_profit"

    ]

    if not all(col in df.columns for col in required):

        return

    for index, row in df.iterrows():

        if row["dividend_payout"] > row["net_profit"]:

            add_failure(

                "DQ09",

                "WARNING",

                table,

                index + 1,

                "dividend_payout",

                "Dividend exceeds Net Profit"

            )

def dq10_url(df):

    if "website" not in df.columns:

        return

    for index, row in df.iterrows():

        url = str(row["website"])

        if not (

            url.startswith("http://")

            or

            url.startswith("https://")

        ):

            add_failure(

                "DQ10",

                "WARNING",

                "companies",

                index + 1,

                "website",

                "Invalid Website URL"

            )

def dq11_eps(df, table):

    required = [

        "eps",

        "net_profit"

    ]

    if not all(col in df.columns for col in required):

        return

    for index, row in df.iterrows():

        if (

            row["net_profit"] > 0

            and

            row["eps"] < 0

        ):

            add_failure(

                "DQ11",

                "WARNING",

                table,

                index + 1,

                "eps",

                "EPS Sign Incorrect"

            )

def dq12_nulls(df, table):

    mandatory = [

        "company_id"

    ]

    for column in mandatory:

        if column not in df.columns:

            continue

        nulls = df[df[column].isnull()]

        for index, row in nulls.iterrows():

            add_failure(

                "DQ12",

                "CRITICAL",

                table,

                index + 1,

                column,

                "Mandatory Value Missing"

            )

def dq13_duplicates(df, table):

    duplicates = df[df.duplicated()]

    for index, row in duplicates.iterrows():

        add_failure(

            "DQ13",

            "WARNING",

            table,

            index + 1,

            "Entire Row",

            "Duplicate Row"

        )

def dq14_years(df, table):

    if "company_id" not in df.columns:

        return

    if "year" not in df.columns:

        return

    counts = df.groupby(

        "company_id"

    )["year"].count()

    for company, total in counts.items():

        if total < 5:

            add_failure(

                "DQ14",

                "WARNING",

                table,

                "-",

                "year",

                f"{company} has only {total} years"

            )

def dq15_year(df, table):

    if "year" not in df.columns:

        return

    invalid = df[

        pd.to_numeric(

            df["year"],

            errors="coerce"

        ).isna()

    ]

    for index, row in invalid.iterrows():

        add_failure(

            "DQ15",

            "CRITICAL",

            table,

            index + 1,

            "year",

            "Year is not numeric"

        )

def dq16_null_percentage(df, table):

    for column in df.columns:

        percentage = (

            df[column]

            .isnull()

            .mean()

        ) * 100

        if percentage > 20:

            add_failure(

                "DQ16",

                "WARNING",

                table,

                "-",

                column,

                f"{percentage:.2f}% NULL values"

            )

# =====================================================
# RUN ALL VALIDATIONS
# =====================================================

def run_validations(tables):

    print("\nStarting Data Quality Validation...\n")

    companies = tables.get("companies")
    balancesheet = tables.get("balancesheet")
    profitandloss = tables.get("profitandloss")
    cashflow = tables.get("cashflow")
    analysis = tables.get("analysis")
    documents = tables.get("documents")
    prosandcons = tables.get("prosandcons")
    financial_ratios = tables.get("financial_ratios")
    peer_groups = tables.get("peer_groups")
    stock_prices = tables.get("stock_prices")

    # -------------------------
    # DQ01
    # -------------------------
    if companies is not None:
        dq01_primary_key(companies, "companies", "id")

    # -------------------------
    # DQ02
    # -------------------------
    for name, table in [

        ("balancesheet", balancesheet),

        ("profitandloss", profitandloss),

        ("cashflow", cashflow),

        ("stock_prices", stock_prices)

    ]:

        if table is not None:
            dq02_company_year(table, name)

    # -------------------------
    # DQ03
    # -------------------------
    for name, table in [

        ("balancesheet", balancesheet),

        ("profitandloss", profitandloss),

        ("cashflow", cashflow),

        ("analysis", analysis),

        ("documents", documents),

        ("prosandcons", prosandcons),

        ("financial_ratios", financial_ratios),

        ("peer_groups", peer_groups),

        ("stock_prices", stock_prices)

    ]:

        if table is not None:
            dq03_foreign_key(companies, table, name)

    # -------------------------
    # DQ04 - DQ16
    # -------------------------

    for name, table in tables.items():

        dq04_balance_sheet(table, name)

        dq05_opm(table, name)

        dq06_positive_sales(table, name)

        dq07_cashflow(table, name)

        dq08_tax(table, name)

        dq09_dividend(table, name)

        dq13_duplicates(table, name)

        dq14_years(table, name)

        dq15_year(table, name)

        dq16_null_percentage(table, name)

    if companies is not None:

        dq10_url(companies)

    if profitandloss is not None:

        dq11_eps(profitandloss, "profitandloss")

        dq12_nulls(profitandloss, "profitandloss")

    if balancesheet is not None:

        dq12_nulls(balancesheet, "balancesheet")

    if cashflow is not None:

        dq12_nulls(cashflow, "cashflow")

# =====================================================
# SAVE VALIDATION REPORT
# =====================================================

def save_validation_report():

    report = pd.DataFrame(validation_failures)

    output_file = os.path.join(

        OUTPUT_DIR,

        "validation_failures.csv"

    )

    report.to_csv(

        output_file,

        index=False

    )

    print("\nValidation report saved successfully.")

    print(output_file)

# =====================================================
# SUMMARY
# =====================================================

def print_summary():

    print("\n" + "=" * 50)

    print("VALIDATION SUMMARY")

    print("=" * 50)

    total = len(validation_failures)

    critical = len([

        x for x in validation_failures

        if x["Severity"] == "CRITICAL"

    ])

    warning = len([

        x for x in validation_failures

        if x["Severity"] == "WARNING"

    ])

    print(f"Total Issues     : {total}")

    print(f"Critical Issues  : {critical}")

    print(f"Warnings         : {warning}")

    print("=" * 50)

    if critical == 0:

        print("Dataset Passed Validation")

    else:

        print("Critical Errors Found")

# =====================================================
# MAIN
# =====================================================

def main():

    print("=" * 60)

    print("NIFTY100 DATA VALIDATION")

    print("=" * 60)

    tables = load_tables()

    print(f"\nLoaded {len(tables)} tables.\n")

    run_validations(tables)

    save_validation_report()

    print_summary()

    print("\nValidation Completed Successfully.")


if __name__ == "__main__":

    main()

