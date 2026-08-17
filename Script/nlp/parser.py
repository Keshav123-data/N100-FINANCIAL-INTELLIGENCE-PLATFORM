from __future__ import annotations

import re
import sqlite3
import traceback
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ANALYSIS_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "analysis.xlsx"
)

DATABASE_FILE = (
    PROJECT_ROOT
    / "DB"
    / "nifty100.db"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "output"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


PARSED_FILE = (
    OUTPUT_DIR
    / "analysis_parsed.csv"
)

FAILURES_FILE = (
    OUTPUT_DIR
    / "parse_failures.csv"
)

DIVERGENCE_FILE = (
    OUTPUT_DIR
    / "cagr_divergence_review.csv"
)

COVERAGE_FILE = (
    OUTPUT_DIR
    / "parse_company_coverage.csv"
)


# ============================================================
# TARGET METRICS
# ============================================================

TARGET_METRICS = {
    "compounded_sales_growth":
        "compounded_sales_growth",

    "compounded_profit_growth":
        "compounded_profit_growth",

    "stock_price_cagr":
        "stock_price_cagr",

    "roe":
        "roe",
}


# ============================================================
# REQUIRED REGEX
# ============================================================

# Required Sprint 5 regex:
#
# (\d+)\s*Years?:?\s*([\d.]+)%
#
# Extended here to support:
# - negative values
# - optional whitespace
#
YEARS_REGEX = re.compile(
    r"(\d+)\s*Years?:?\s*([+-]?\d+(?:\.\d+)?)\s*%",
    flags=re.IGNORECASE,
)


# Supports:
#
# 1 Year: -2%
# 1 Years: 5%
#
ONE_YEAR_REGEX = re.compile(
    r"1\s*Years?:?\s*([+-]?\d+(?:\.\d+)?)\s*%",
    flags=re.IGNORECASE,
)


# Supports:
#
# TTM: 43%
# Last Year: 17%
#
SPECIAL_REGEX = re.compile(
    r"(TTM|Last\s+Year):?\s*([+-]?\d+(?:\.\d+)?)\s*%",
    flags=re.IGNORECASE,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_column_name(value):
    """
    Convert Excel column names to normalized names.
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = re.sub(
        r"\s+",
        "_",
        text,
    )

    text = re.sub(
        r"[^a-z0-9_]+",
        "",
        text,
    )

    return text


def clean_text(value):
    """
    Convert a cell into clean text.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


def safe_float(value):
    """
    Safely convert a value to float.
    """

    try:

        if value is None:
            return np.nan

        value = float(value)

        if pd.isna(value):
            return np.nan

        return value

    except (
        TypeError,
        ValueError,
    ):

        return np.nan


# ============================================================
# LOAD EXCEL WITH AUTOMATIC HEADER DETECTION
# ============================================================

def detect_header_row(raw_df):
    """
    Find the row containing the actual analysis headers.

    Expected headers include:

        id
        company_id
        compounded_sales_growth
        compounded_profit_growth
        stock_price_cagr
        roe
    """

    required = {
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    }

    for index in range(len(raw_df)):

        row_values = {
            normalize_column_name(value)
            for value in raw_df.iloc[index].tolist()
        }

        matched = required.intersection(
            row_values
        )

        if len(matched) >= 4:

            return index

    return None


def load_analysis_file():
    """
    Load analysis.xlsx while handling the title row.
    """

    print()
    print("=" * 70)
    print("LOADING ANALYSIS FILE")
    print("=" * 70)

    if not ANALYSIS_FILE.exists():

        raise FileNotFoundError(
            f"Analysis file not found:\n"
            f"{ANALYSIS_FILE}"
        )

    print(
        f"File: {ANALYSIS_FILE}"
    )

    raw_df = pd.read_excel(
        ANALYSIS_FILE,
        sheet_name="Analysis",
        header=None,
    )

    print(
        f"Raw rows: {len(raw_df)}"
    )

    print(
        f"Raw columns: {len(raw_df.columns)}"
    )

    header_row = detect_header_row(
        raw_df
    )

    if header_row is None:

        raise ValueError(
            "Could not detect the analysis "
            "header row."
        )

    print(
        f"Detected header row: "
        f"{header_row + 1}"
    )

    headers = [
        normalize_column_name(value)
        for value in raw_df.iloc[
            header_row
        ].tolist()
    ]

    df = raw_df.iloc[
        header_row + 1:
    ].copy()

    df.columns = headers

    # Remove completely empty columns
    df = df.dropna(
        axis=1,
        how="all",
    )

    # Remove completely empty rows
    df = df.dropna(
        axis=0,
        how="all",
    )

    df = df.reset_index(
        drop=True
    )

    print(
        f"Rows after header detection: "
        f"{len(df)}"
    )

    print()
    print("Detected columns:")

    for column in df.columns:

        print(
            f"  - {column}"
        )

    print()

    missing = [
        column
        for column in TARGET_METRICS
        if column not in df.columns
    ]

    if missing:

        print(
            "WARNING — Missing target fields:"
        )

        for column in missing:

            print(
                f"  ✗ {column}"
            )

    else:

        print(
            "✓ All four target metric columns "
            "detected."
        )

    return df


# ============================================================
# COMPANY ID
# ============================================================

def get_company_ids(df):
    """
    Get company identifiers.

    Your actual analysis.xlsx already contains:

        company_id

    so this function preserves those values.
    """

    if "company_id" not in df.columns:

        raise ValueError(
            "\nanalysis.xlsx must contain "
            "company_id."
        )

    result = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result = result.replace(
        {
            "NAN": "",
            "NONE": "",
        }
    )

    return result


# ============================================================
# PARSE SINGLE VALUE
# ============================================================

def parse_metric_value(raw_value):
    """
    Parse one analysis cell.

    Examples:

        10 Years: 21%
            -> period_years = 10
            -> value_pct = 21

        5 Years: -3%
            -> period_years = 5
            -> value_pct = -3

        TTM: 43%
            -> period_years = NaN
            -> value_pct = 43

        Last Year: 17%
            -> period_years = 1
            -> value_pct = 17

        1 Year: -2%
            -> period_years = 1
            -> value_pct = -2
    """

    text = clean_text(
        raw_value
    )

    if not text:

        return {
            "matched": False,
            "period_years": np.nan,
            "value_pct": np.nan,
            "period_label": None,
        }

    # --------------------------------------------------------
    # Required YEARS regex
    # --------------------------------------------------------

    match = YEARS_REGEX.search(
        text
    )

    if match:

        period = int(
            match.group(1)
        )

        value = float(
            match.group(2)
        )

        return {
            "matched": True,
            "period_years": period,
            "value_pct": value,
            "period_label":
                f"{period} Years",
        }

    # --------------------------------------------------------
    # 1 YEAR
    # --------------------------------------------------------

    match = ONE_YEAR_REGEX.search(
        text
    )

    if match:

        value = float(
            match.group(1)
        )

        return {
            "matched": True,
            "period_years": 1,
            "value_pct": value,
            "period_label": "1 Year",
        }

    # --------------------------------------------------------
    # TTM / LAST YEAR
    # --------------------------------------------------------

    match = SPECIAL_REGEX.search(
        text
    )

    if match:

        label = (
            match.group(1)
            .strip()
            .lower()
        )

        value = float(
            match.group(2)
        )

        if label == "last year":

            period_years = 1

        else:

            period_years = np.nan

        return {
            "matched": True,
            "period_years":
                period_years,
            "value_pct": value,
            "period_label":
                match.group(1),
        }

    return {
        "matched": False,
        "period_years": np.nan,
        "value_pct": np.nan,
        "period_label": None,
    }


# ============================================================
# PARSE ANALYSIS
# ============================================================

def parse_analysis(df):
    """
    Parse all four target metrics.
    """

    print()
    print("=" * 70)
    print("PARSING ANALYSIS TEXT")
    print("=" * 70)

    company_ids = get_company_ids(
        df
    )

    results = []
    failures = []

    for row_index, row in df.iterrows():

        company_id = (
            company_ids.loc[row_index]
        )

        if not company_id:

            failures.append({

                "row_number":
                    row_index + 1,

                "company_id":
                    "",

                "metric_type":
                    "",

                "raw_text":
                    "",

                "failure_reason":
                    "Missing company_id",
            })

            continue

        for source_column, metric_type in (
            TARGET_METRICS.items()
        ):

            if (
                source_column
                not in df.columns
            ):
                continue

            raw_value = row[
                source_column
            ]

            parsed = parse_metric_value(
                raw_value
            )

            if parsed["matched"]:

                results.append({

                    "company_id":
                        company_id,

                    "metric_type":
                        metric_type,

                    "period_years":
                        parsed[
                            "period_years"
                        ],

                    "value_pct":
                        parsed[
                            "value_pct"
                        ],
                })

            else:

                # Empty values are not treated
                # as parsing failures.
                if clean_text(
                    raw_value
                ):

                    failures.append({

                        "row_number":
                            row_index + 1,

                        "company_id":
                            company_id,

                        "metric_type":
                            metric_type,

                        "raw_text":
                            clean_text(
                                raw_value
                            ),

                        "failure_reason":
                            "Regex did not match",
                    })

    parsed_df = pd.DataFrame(
        results,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failures,
        columns=[
            "row_number",
            "company_id",
            "metric_type",
            "raw_text",
            "failure_reason",
        ],
    )

    if not parsed_df.empty:

        parsed_df[
            "period_years"
        ] = pd.to_numeric(
            parsed_df[
                "period_years"
            ],
            errors="coerce",
        )

        parsed_df[
            "value_pct"
        ] = pd.to_numeric(
            parsed_df[
                "value_pct"
            ],
            errors="coerce",
        )

        parsed_df = (
            parsed_df
            .sort_values(
                [
                    "company_id",
                    "metric_type",
                    "period_years",
                ],
                na_position="last",
            )
            .reset_index(
                drop=True
            )
        )

    print(
        f"Parsed rows: {len(parsed_df)}"
    )

    print(
        f"Parse failures: "
        f"{len(failures_df)}"
    )

    return (
        parsed_df,
        failures_df,
    )


# ============================================================
# SAVE PARSED RESULTS
# ============================================================

def save_parsed_results(
    parsed_df,
    failures_df,
):
    """
    Save parser outputs.
    """

    parsed_df.to_csv(
        PARSED_FILE,
        index=False,
    )

    failures_df.to_csv(
        FAILURES_FILE,
        index=False,
    )

    print()
    print(
        f"✓ Saved: {PARSED_FILE}"
    )

    print(
        f"✓ Saved: {FAILURES_FILE}"
    )


# ============================================================
# LOAD RATIO ENGINE DATA
# ============================================================

def load_ratio_data():
    """
    Load financial_ratios from SQLite.
    """

    print()
    print("=" * 70)
    print("LOADING RATIO ENGINE DATA")
    print("=" * 70)

    if not DATABASE_FILE.exists():

        print(
            "WARNING — Database not found."
        )

        return pd.DataFrame()

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    try:

        query = """
            SELECT *
            FROM financial_ratios
        """

        df = pd.read_sql_query(
            query,
            connection,
        )

    finally:

        connection.close()

    print(
        f"Rows loaded: {len(df)}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    return df


# ============================================================
# CAGR COLUMN DETECTION
# ============================================================

def find_column(
    df,
    candidates,
):
    """
    Case-insensitive column lookup.
    """

    if df.empty:

        return None

    mapping = {
        normalize_column_name(
            column
        ): column
        for column in df.columns
    }

    for candidate in candidates:

        normalized = (
            normalize_column_name(
                candidate
            )
        )

        if normalized in mapping:

            return mapping[
                normalized
            ]

    return None


# ============================================================
# CROSS VALIDATION
# ============================================================

def cross_validate_cagr(
    parsed_df,
    ratio_df,
):
    """
    Cross-validate 5-year parsed CAGR values
    against financial_ratios.

    Divergence > 5 percentage points is flagged.
    """

    print()
    print("=" * 70)
    print("CAGR CROSS-VALIDATION")
    print("=" * 70)

    if parsed_df.empty:

        print(
            "No parsed data available."
        )

        return pd.DataFrame()

    if ratio_df.empty:

        print(
            "Ratio Engine data unavailable."
        )

        return pd.DataFrame()

    company_column = find_column(
        ratio_df,
        [
            "company_id",
        ],
    )

    year_column = find_column(
        ratio_df,
        [
            "year",
        ],
    )

    revenue_cagr_column = find_column(
        ratio_df,
        [
            "revenue_cagr_5yr",
            "revenue_cagr_5y",
            "revenue_cagr_5_year",
        ],
    )

    pat_cagr_column = find_column(
        ratio_df,
        [
            "pat_cagr_5yr",
            "pat_cagr_5y",
            "pat_cagr_5_year",
        ],
    )

    if not company_column:

        print(
            "WARNING — company_id missing "
            "from financial_ratios."
        )

        return pd.DataFrame()

    if not year_column:

        print(
            "WARNING — year missing "
            "from financial_ratios."
        )

        return pd.DataFrame()

    if (
        not revenue_cagr_column
        and not pat_cagr_column
    ):

        print(
            "WARNING — no 5-year CAGR "
            "columns found in financial_ratios."
        )

        return pd.DataFrame()

    ratio_df = ratio_df.copy()

    ratio_df[
        company_column
    ] = (
        ratio_df[
            company_column
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    ratio_df[
        year_column
    ] = pd.to_numeric(
        ratio_df[
            year_column
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Latest year for each company
    # --------------------------------------------------------

    ratio_df = (
        ratio_df
        .sort_values(
            [
                company_column,
                year_column,
            ]
        )
        .groupby(
            company_column,
            as_index=False,
        )
        .tail(1)
    )

    # --------------------------------------------------------
    # Keep relevant columns
    # --------------------------------------------------------

    selected_columns = [
        company_column,
    ]

    if revenue_cagr_column:

        selected_columns.append(
            revenue_cagr_column
        )

    if pat_cagr_column:

        selected_columns.append(
            pat_cagr_column
        )

    ratio_latest = ratio_df[
        selected_columns
    ].copy()

    ratio_latest = (
        ratio_latest
        .rename(
            columns={
                company_column:
                    "company_id",
            }
        )
    )

    # --------------------------------------------------------
    # Parsed 5-year data only
    # --------------------------------------------------------

    parsed_5y = parsed_df[
        parsed_df[
            "period_years"
        ] == 5
    ].copy()

    if parsed_5y.empty:

        print(
            "No 5-year parsed CAGR values "
            "available."
        )

        return pd.DataFrame()

    # --------------------------------------------------------
    # Convert metric names
    # --------------------------------------------------------

    sales_parsed = (
        parsed_5y[
            parsed_5y[
                "metric_type"
            ]
            == "compounded_sales_growth"
        ]
        [
            [
                "company_id",
                "value_pct",
            ]
        ]
        .rename(
            columns={
                "value_pct":
                    "parsed_revenue_cagr_5yr"
            }
        )
    )

    profit_parsed = (
        parsed_5y[
            parsed_5y[
                "metric_type"
            ]
            == "compounded_profit_growth"
        ]
        [
            [
                "company_id",
                "value_pct",
            ]
        ]
        .rename(
            columns={
                "value_pct":
                    "parsed_pat_cagr_5yr"
            }
        )
    )

    comparison = ratio_latest.copy()

    comparison[
        "company_id"
    ] = (
        comparison[
            "company_id"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Merge sales
    # --------------------------------------------------------

    comparison = comparison.merge(
        sales_parsed,
        on="company_id",
        how="outer",
    )

    # --------------------------------------------------------
    # Merge profit
    # --------------------------------------------------------

    comparison = comparison.merge(
        profit_parsed,
        on="company_id",
        how="outer",
    )

    # --------------------------------------------------------
    # Revenue divergence
    # --------------------------------------------------------

    if revenue_cagr_column:

        comparison[
            "ratio_revenue_cagr_5yr"
        ] = pd.to_numeric(
            comparison[
                revenue_cagr_column
            ],
            errors="coerce",
        )

        comparison[
            "revenue_divergence_pct"
        ] = (
            comparison[
                "parsed_revenue_cagr_5yr"
            ]
            - comparison[
                "ratio_revenue_cagr_5yr"
            ]
        ).abs()

    else:

        comparison[
            "ratio_revenue_cagr_5yr"
        ] = np.nan

        comparison[
            "revenue_divergence_pct"
        ] = np.nan

    # --------------------------------------------------------
    # PAT divergence
    # --------------------------------------------------------

    if pat_cagr_column:

        comparison[
            "ratio_pat_cagr_5yr"
        ] = pd.to_numeric(
            comparison[
                pat_cagr_column
            ],
            errors="coerce",
        )

        comparison[
            "pat_divergence_pct"
        ] = (
            comparison[
                "parsed_pat_cagr_5yr"
            ]
            - comparison[
                "ratio_pat_cagr_5yr"
            ]
        ).abs()

    else:

        comparison[
            "ratio_pat_cagr_5yr"
        ] = np.nan

        comparison[
            "pat_divergence_pct"
        ] = np.nan

    # --------------------------------------------------------
    # Flag divergence > 5 percentage points
    # --------------------------------------------------------

    comparison[
        "revenue_flag"
    ] = (
        comparison[
            "revenue_divergence_pct"
        ]
        > 5
    )

    comparison[
        "pat_flag"
    ] = (
        comparison[
            "pat_divergence_pct"
        ]
        > 5
    )

    comparison[
        "manual_review"
    ] = (
        comparison[
            "revenue_flag"
        ]
        | comparison[
            "pat_flag"
        ]
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    output_columns = [

        "company_id",

        "parsed_revenue_cagr_5yr",

        "ratio_revenue_cagr_5yr",

        "revenue_divergence_pct",

        "parsed_pat_cagr_5yr",

        "ratio_pat_cagr_5yr",

        "pat_divergence_pct",

        "revenue_flag",

        "pat_flag",

        "manual_review",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in comparison.columns
    ]

    comparison = comparison[
        output_columns
    ].copy()

    comparison.to_csv(
        DIVERGENCE_FILE,
        index=False,
    )

    flagged = comparison[
        comparison[
            "manual_review"
        ]
        == True
    ]

    print(
        f"Companies checked: "
        f"{len(comparison)}"
    )

    print(
        f"Manual review flags: "
        f"{len(flagged)}"
    )

    print(
        f"✓ Saved: "
        f"{DIVERGENCE_FILE}"
    )

    return comparison


# ============================================================
# COMPANY COVERAGE
# ============================================================

def generate_company_coverage(
    parsed_df,
):
    """
    Verify parsed coverage by company.
    """

    print()
    print("=" * 70)
    print("COMPANY COVERAGE CHECK")
    print("=" * 70)

    if parsed_df.empty:

        return pd.DataFrame()

    companies = sorted(
        parsed_df[
            "company_id"
        ]
        .dropna()
        .unique()
    )

    rows = []

    for company_id in companies:

        company_df = parsed_df[
            parsed_df[
                "company_id"
            ] == company_id
        ]

        metrics = set(
            company_df[
                "metric_type"
            ]
        )

        rows.append({

            "company_id":
                company_id,

            "parsed_rows":
                len(company_df),

            "metrics_found":
                len(metrics),

            "sales_growth":
                "compounded_sales_growth"
                in metrics,

            "profit_growth":
                "compounded_profit_growth"
                in metrics,

            "stock_price_cagr":
                "stock_price_cagr"
                in metrics,

            "roe":
                "roe"
                in metrics,

            "complete":
                metrics
                == set(
                    TARGET_METRICS.values()
                ),
        })

    coverage = pd.DataFrame(
        rows
    )

    coverage.to_csv(
        COVERAGE_FILE,
        index=False,
    )

    print(
        f"Companies parsed: "
        f"{len(coverage)}"
    )

    print(
        f"Complete companies: "
        f"{coverage['complete'].sum()}"
    )

    print(
        f"Incomplete companies: "
        f"{(~coverage['complete']).sum()}"
    )

    print(
        f"✓ Saved: {COVERAGE_FILE}"
    )

    return coverage


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    parsed_df,
    failures_df,
    comparison_df,
):
    """
    Print final Sprint 5 Day 29 summary.
    """

    print()
    print("=" * 70)
    print("SPRINT 5 — DAY 29 SUMMARY")
    print("=" * 70)

    print(
        f"Analysis rows parsed : "
        f"{len(parsed_df)}"
    )

    print(
        f"Companies            : "
        f"{parsed_df['company_id'].nunique() }"
        if not parsed_df.empty
        else 0
    )

    print(
        f"Parse failures       : "
        f"{len(failures_df)}"
    )

    if (
        comparison_df is not None
        and not comparison_df.empty
        and "manual_review"
        in comparison_df.columns
    ):

        print(
            f"CAGR manual reviews  : "
            f"{comparison_df['manual_review'].sum()}"
        )

    print()
    print("Generated files:")

    print(
        f"  ✓ {PARSED_FILE}"
    )

    print(
        f"  ✓ {FAILURES_FILE}"
    )

    if DIVERGENCE_FILE.exists():

        print(
            f"  ✓ {DIVERGENCE_FILE}"
        )

    if COVERAGE_FILE.exists():

        print(
            f"  ✓ {COVERAGE_FILE}"
        )

    print()
    print(
        "DAY 29 PARSER COMPLETED."
    )

    print("=" * 70)


# ============================================================
# MAIN RUNNER
# ============================================================

def run():
    """
    Complete Day 29 pipeline.
    """

    print()
    print("=" * 70)
    print(
        "SPRINT 5 — DAY 29"
    )
    print(
        "NLP ANALYSIS TEXT PARSER"
    )
    print("=" * 70)

    print()
    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Analysis     : {ANALYSIS_FILE}"
    )

    print(
        f"Database     : {DATABASE_FILE}"
    )

    print(
        f"Output       : {OUTPUT_DIR}"
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    analysis_df = load_analysis_file()

    # --------------------------------------------------------
    # PARSE
    # --------------------------------------------------------

    parsed_df, failures_df = (
        parse_analysis(
            analysis_df
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_parsed_results(
        parsed_df,
        failures_df,
    )

    # --------------------------------------------------------
    # COVERAGE
    # --------------------------------------------------------

    generate_company_coverage(
        parsed_df
    )

    # --------------------------------------------------------
    # RATIO ENGINE
    # --------------------------------------------------------

    ratio_df = load_ratio_data()

    # --------------------------------------------------------
    # CROSS VALIDATION
    # --------------------------------------------------------

    comparison_df = (
        cross_validate_cagr(
            parsed_df,
            ratio_df,
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print_summary(
        parsed_df,
        failures_df,
        comparison_df,
    )

    return {
        "parsed":
            parsed_df,

        "failures":
            failures_df,

        "comparison":
            comparison_df,
    }


# ============================================================
# COMMAND LINE ENTRY
# ============================================================

if __name__ == "__main__":

    try:

        run()

    except Exception as error:

        print()
        print("=" * 70)
        print("DAY 29 ERROR")
        print("=" * 70)

        print(
            type(error).__name__,
            ":",
            error,
        )

        traceback.print_exc()

        raise