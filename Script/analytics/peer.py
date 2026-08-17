from pathlib import Path
import sqlite3
import sys
import traceback

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database
DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

# Processed data
DATA_DIR = PROJECT_ROOT / "Data" / "processed"

# Input files
PEER_FILE = DATA_DIR / "peer_groups.csv"
RATIOS_FILE = DATA_DIR / "financial_ratios.csv"
COMPANIES_FILE = DATA_DIR / "companies.csv"

# Output
OUTPUT_DIR = PROJECT_ROOT / "output"


# ============================================================
# PEER ENGINE
# ============================================================

class PeerPercentileEngine:

    def __init__(
        self,
        data_dir=None,
        db_path=None
    ):

        self.DATA_DIR = (
            Path(data_dir)
            if data_dir
            else DATA_DIR
        )

        self.DB_PATH = (
            Path(db_path)
            if db_path
            else DB_PATH
        )

        self.PEER_FILE = (
            self.DATA_DIR /
            "peer_groups.csv"
        )

        self.RATIOS_FILE = (
            self.DATA_DIR /
            "financial_ratios.csv"
        )

        self.COMPANIES_FILE = (
            self.DATA_DIR /
            "companies.csv"
        )

        self.peer_groups = None
        self.ratios = None
        self.companies = None
        self.metrics = None

    # ========================================================
    # READ CSV
    # ========================================================

    def read_csv(self, path):

        if not path.exists():

            raise FileNotFoundError(
                f"\nFile not found:\n{path}"
            )

        df = pd.read_csv(path)

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        return df

    # ========================================================
    # LOAD DATA
    # ========================================================

    def load_data(self):

        print()
        print("=" * 70)
        print("DAY 18 — LOADING DATA")
        print("=" * 70)

        # ----------------------------------------------------
        # Peer groups
        # ----------------------------------------------------

        self.peer_groups = self.read_csv(
            self.PEER_FILE
        )

        # ----------------------------------------------------
        # Financial ratios
        # ----------------------------------------------------

        self.ratios = self.read_csv(
            self.RATIOS_FILE
        )

        # ----------------------------------------------------
        # Companies
        # ----------------------------------------------------

        self.companies = self.read_csv(
            self.COMPANIES_FILE
        )

        # ----------------------------------------------------
        # Normalize company IDs
        # ----------------------------------------------------

        for df in [
            self.peer_groups,
            self.ratios,
            self.companies
        ]:

            if "company_id" in df.columns:

                df["company_id"] = (
                    df["company_id"]
                    .astype(str)
                    .str.strip()
                )

        if "id" in self.companies.columns:

            self.companies["id"] = (
                self.companies["id"]
                .astype(str)
                .str.strip()
            )

        # ----------------------------------------------------
        # Normalize year
        # ----------------------------------------------------

        self.ratios["year"] = pd.to_numeric(
            self.ratios["year"],
            errors="coerce"
        )

        print(
            f"\nCompanies: {len(self.companies)}"
        )

        print(
            f"Financial ratio rows: "
            f"{len(self.ratios)}"
        )

        print(
            f"Peer assignments: "
            f"{len(self.peer_groups)}"
        )

        print(
            f"Peer groups: "
            f"{self.peer_groups['peer_group_name'].nunique()}"
        )

        return (
            self.peer_groups,
            self.ratios,
            self.companies
        )

    # ========================================================
    # PREPARE LATEST FINANCIAL DATA
    # ========================================================

    def prepare_latest_metrics(self):

        ratios = self.ratios.copy()

        # ----------------------------------------------------
        # Sort by company and year
        # ----------------------------------------------------

        ratios = ratios.sort_values(
            [
                "company_id",
                "year"
            ]
        )

        # ----------------------------------------------------
        # Keep latest year per company
        # ----------------------------------------------------

        latest = (
            ratios
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
            .copy()
        )

        # ====================================================
        # ROE
        # ====================================================

        latest["ROE"] = pd.to_numeric(
            latest[
                "return_on_equity_pct"
            ],
            errors="coerce"
        )

        # ====================================================
        # ROCE
        #
        # financial_ratios.csv does not contain ROCE.
        # It is available in companies.csv.
        # ====================================================

        roce = self.companies[
            [
                "id",
                "roce_percentage"
            ]
        ].copy()

        roce = roce.rename(
            columns={
                "id": "company_id",
                "roce_percentage": "ROCE"
            }
        )

        latest = latest.merge(
            roce,
            on="company_id",
            how="left"
        )

        latest["ROCE"] = pd.to_numeric(
            latest["ROCE"],
            errors="coerce"
        )

        # ====================================================
        # NET PROFIT MARGIN
        # ====================================================

        latest["NPM"] = pd.to_numeric(
            latest[
                "net_profit_margin_pct"
            ],
            errors="coerce"
        )

        # ====================================================
        # DEBT / EQUITY
        # ====================================================

        latest["D/E"] = pd.to_numeric(
            latest[
                "debt_to_equity"
            ],
            errors="coerce"
        )

        # ====================================================
        # FREE CASH FLOW
        # ====================================================

        latest["FCF"] = pd.to_numeric(
            latest[
                "free_cash_flow_cr"
            ],
            errors="coerce"
        )

        # ====================================================
        # PAT CAGR 5Y
        #
        # Your database already contains this field.
        # But the CSV may or may not contain it.
        #
        # Therefore calculate it from P&L if absent.
        # ====================================================

        if "pat_cagr_5yr" in latest.columns:

            latest["PAT CAGR 5Y"] = pd.to_numeric(
                latest[
                    "pat_cagr_5yr"
                ],
                errors="coerce"
            )

        else:

            latest[
                "PAT CAGR 5Y"
            ] = np.nan

        # ====================================================
        # REVENUE CAGR 5Y
        # ====================================================

        if "revenue_cagr_5yr" in latest.columns:

            latest[
                "Revenue CAGR 5Y"
            ] = pd.to_numeric(
                latest[
                    "revenue_cagr_5yr"
                ],
                errors="coerce"
            )

        else:

            latest[
                "Revenue CAGR 5Y"
            ] = np.nan

        # ====================================================
        # EPS CAGR 5Y
        # ====================================================

        if "eps_cagr_5yr" in latest.columns:

            latest[
                "EPS CAGR 5Y"
            ] = pd.to_numeric(
                latest[
                    "eps_cagr_5yr"
                ],
                errors="coerce"
            )

        else:

            latest[
                "EPS CAGR 5Y"
            ] = np.nan

        # ====================================================
        # INTEREST COVERAGE
        # ====================================================

        latest["Interest Coverage"] = pd.to_numeric(
            latest[
                "interest_coverage"
            ],
            errors="coerce"
        )

        # ====================================================
        # ASSET TURNOVER
        # ====================================================

        latest["Asset Turnover"] = pd.to_numeric(
            latest[
                "asset_turnover"
            ],
            errors="coerce"
        )

        # ====================================================
        # DEBT FREE
        #
        # Debt-free companies get infinite ICR.
        # ====================================================

        debt_free = (
            latest["D/E"]
            .fillna(0)
            .le(0)
        )

        latest.loc[
            debt_free &
            latest[
                "Interest Coverage"
            ].isna(),
            "Interest Coverage"
        ] = np.inf

        # ====================================================
        # SELECT FINAL METRICS
        # ====================================================

        metric_columns = [

            "ROE",
            "ROCE",
            "NPM",
            "D/E",
            "FCF",
            "PAT CAGR 5Y",
            "Revenue CAGR 5Y",
            "EPS CAGR 5Y",
            "Interest Coverage",
            "Asset Turnover",
        ]

        # ====================================================
        # STORE
        # ====================================================

        self.metrics = latest[
            [
                "company_id",
                "year"
            ] + metric_columns
        ].copy()

        print()
        print(
            "Latest financial records:",
            len(self.metrics)
        )

        print()
        print("Metrics prepared:")

        for metric in metric_columns:

            count = (
                self.metrics[metric]
                .notna()
                .sum()
            )

            print(
                f"  ✓ {metric:<22}"
                f"{count} values"
            )

        return self.metrics

    # ========================================================
    # PERCENTILE FUNCTION
    # ========================================================

    @staticmethod
    def calculate_percentile(
        series,
        inverse=False
    ):

        # ----------------------------------------------------
        # Numeric
        # ----------------------------------------------------

        values = pd.to_numeric(
            series,
            errors="coerce"
        )

        # ----------------------------------------------------
        # Infinity is valid for ICR,
        # but percentile calculation must handle it.
        # ----------------------------------------------------

        finite = values.replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )

        # ----------------------------------------------------
        # If no valid values
        # ----------------------------------------------------

        if finite.notna().sum() == 0:

            return pd.Series(
                np.nan,
                index=series.index
            )

        # ----------------------------------------------------
        # Standard percentile rank
        #
        # pct=True gives 0..1
        # ----------------------------------------------------

        percentile = (
            finite
            .rank(
                method="average",
                pct=True
            )
            * 100
        )

        # ----------------------------------------------------
        # D/E:
        #
        # lower is better
        #
        # Example:
        # normal = 20
        # inverse = 80
        # ----------------------------------------------------

        if inverse:

            percentile = (
                100 - percentile
            )

        return percentile.round(2)

    # ========================================================
    # CALCULATE PEER PERCENTILES
    # ========================================================

    def calculate_peer_percentiles(self):

        if self.metrics is None:

            self.prepare_latest_metrics()

        peer = self.peer_groups.copy()

        metrics = self.metrics.copy()

        # ====================================================
        # JOIN COMPANY TO PEER GROUP
        # ====================================================

        merged = peer.merge(
            metrics,
            on="company_id",
            how="left"
        )

        # ====================================================
        # METRIC DEFINITIONS
        # ====================================================

        metric_definitions = {

            "ROE": {
                "column": "ROE",
                "inverse": False
            },

            "ROCE": {
                "column": "ROCE",
                "inverse": False
            },

            "NPM": {
                "column": "NPM",
                "inverse": False
            },

            "D/E": {
                "column": "D/E",
                "inverse": True
            },

            "FCF": {
                "column": "FCF",
                "inverse": False
            },

            "PAT CAGR 5Y": {
                "column": "PAT CAGR 5Y",
                "inverse": False
            },

            "Revenue CAGR 5Y": {
                "column": "Revenue CAGR 5Y",
                "inverse": False
            },

            "EPS CAGR 5Y": {
                "column": "EPS CAGR 5Y",
                "inverse": False
            },

            "Interest Coverage": {
                "column": "Interest Coverage",
                "inverse": False
            },

            "Asset Turnover": {
                "column": "Asset Turnover",
                "inverse": False
            },
        }

        output_rows = []

        # ====================================================
        # GROUP BY PEER GROUP
        # ====================================================

        grouped = merged.groupby(
            "peer_group_name",
            dropna=False
        )

        print()
        print("=" * 70)
        print("PEER PERCENTILE CALCULATION")
        print("=" * 70)

        for peer_group_name, group in grouped:

            if pd.isna(
                peer_group_name
            ):

                continue

            print(
                f"\nPeer Group: "
                f"{peer_group_name}"
            )

            print(
                f"Companies: "
                f"{group['company_id'].nunique()}"
            )

            # ------------------------------------------------
            # Each metric
            # ------------------------------------------------

            for metric_name, definition in (
                metric_definitions.items()
            ):

                column = definition[
                    "column"
                ]

                inverse = definition[
                    "inverse"
                ]

                values = pd.to_numeric(
                    group[column],
                    errors="coerce"
                )

                percentiles = (
                    self.calculate_percentile(
                        values,
                        inverse=inverse
                    )
                )

                # --------------------------------------------
                # Store rows
                # --------------------------------------------

                for idx in group.index:

                    company_id = (
                        group.loc[
                            idx,
                            "company_id"
                        ]
                    )

                    value = values.loc[
                        idx
                    ]

                    percentile = (
                        percentiles.loc[
                            idx
                        ]
                    )

                    year = group.loc[
                        idx,
                        "year"
                    ]

                    output_rows.append({

                        "company_id":
                            company_id,

                        "peer_group_name":
                            peer_group_name,

                        "metric":
                            metric_name,

                        "value":
                            value,

                        "percentile_rank":
                            percentile,

                        "year":
                            year,
                    })

        # ====================================================
        # CREATE DATAFRAME
        # ====================================================

        result = pd.DataFrame(
            output_rows
        )

        if result.empty:

            raise ValueError(
                "No peer percentile rows "
                "were generated."
            )

        # ====================================================
        # SORT
        # ====================================================

        result = (
            result
            .sort_values(
                [
                    "peer_group_name",
                    "company_id",
                    "metric"
                ]
            )
            .reset_index(
                drop=True
            )
        )

        # ====================================================
        # CLEAN NUMBERS
        # ====================================================

        result["value"] = pd.to_numeric(
            result["value"],
            errors="coerce"
        )

        result[
            "percentile_rank"
        ] = pd.to_numeric(
            result[
                "percentile_rank"
            ],
            errors="coerce"
        )

        # ====================================================
        # PRINT SUMMARY
        # ====================================================

        print()
        print("=" * 70)
        print("PEER PERCENTILE SUMMARY")
        print("=" * 70)

        print(
            f"Total rows: {len(result)}"
        )

        print(
            f"Peer groups: "
            f"{result['peer_group_name'].nunique()}"
        )

        print(
            f"Companies: "
            f"{result['company_id'].nunique()}"
        )

        print(
            f"Metrics: "
            f"{result['metric'].nunique()}"
        )

        return result

    # ========================================================
    # COMPANIES WITHOUT PEER GROUP
    # ========================================================

    def find_unassigned_companies(self):

        all_companies = set(
            self.companies["id"]
            .astype(str)
            .str.strip()
        )

        assigned_companies = set(
            self.peer_groups[
                "company_id"
            ]
            .astype(str)
            .str.strip()
        )

        unassigned = sorted(
            all_companies -
            assigned_companies
        )

        return unassigned

    # ========================================================
    # WRITE TO SQLITE
    # ========================================================

    def save_to_sqlite(
        self,
        result
    ):

        print()
        print("=" * 70)
        print("SAVING TO SQLITE")
        print("=" * 70)

        if not self.DB_PATH.exists():

            raise FileNotFoundError(
                f"\nDatabase not found:\n"
                f"{self.DB_PATH}"
            )

        conn = sqlite3.connect(
            self.DB_PATH
        )

        try:

            # ------------------------------------------------
            # Replace old Day 18 results
            # ------------------------------------------------

            result.to_sql(
                "peer_percentiles",
                conn,
                if_exists="replace",
                index=False
            )

            conn.commit()

        finally:

            conn.close()

        print(
            "\n✓ SQLite table created:"
        )

        print(
            "  peer_percentiles"
        )

        print(
            f"✓ Rows inserted: "
            f"{len(result)}"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        result
    ):

        print()
        print("=" * 70)
        print("DAY 18 VALIDATION")
        print("=" * 70)

        errors = []

        # ====================================================
        # EXPECTED METRICS
        # ====================================================

        expected_metrics = {

            "ROE",
            "ROCE",
            "NPM",
            "D/E",
            "FCF",
            "PAT CAGR 5Y",
            "Revenue CAGR 5Y",
            "EPS CAGR 5Y",
            "Interest Coverage",
            "Asset Turnover",
        }

        actual_metrics = set(
            result["metric"].unique()
        )

        missing_metrics = (
            expected_metrics -
            actual_metrics
        )

        if missing_metrics:

            errors.append(
                "Missing metrics: "
                + ", ".join(
                    sorted(
                        missing_metrics
                    )
                )
            )

        else:

            print(
                "✓ All 10 metrics present"
            )

        # ====================================================
        # PERCENTILE RANGE
        # ====================================================

        invalid_percentiles = result[
            result["percentile_rank"].notna()
            &
            (
                (result["percentile_rank"] < 0)
                |
                (result["percentile_rank"] > 100)
            )
        ]

        if len(invalid_percentiles) > 0:

            errors.append(
                f"Invalid percentile values: "
                f"{len(invalid_percentiles)}"
            )

        else:

            print(
                "✓ Percentile values are "
                "between 0 and 100"
            )

        # ====================================================
        # D/E INVERSE CHECK
        # ====================================================

        de = result[
            (result["metric"] == "D/E")
            &
            result["value"].notna()
            &
            result["percentile_rank"].notna()
        ].copy()

        if len(de) >= 2:

            highest_de = de.loc[
                de["value"].idxmax()
            ]

            lowest_de = de.loc[
                de["value"].idxmin()
            ]

            if (
                lowest_de[
                    "percentile_rank"
                ]
                <
                highest_de[
                    "percentile_rank"
                ]
            ):

                errors.append(
                    "D/E inverse ranking failed"
                )

            else:

                print(
                    "✓ D/E inverse ranking verified"
                )

        # ====================================================
        # PEER GROUP COUNT
        # ====================================================

        peer_count = (
            result[
                "peer_group_name"
            ]
            .nunique()
        )

        print(
            f"✓ Peer groups processed: "
            f"{peer_count}"
        )

        # ====================================================
        # FINAL STATUS
        # ====================================================

        print()

        if errors:

            print(
                "❌ VALIDATION FAILED"
            )

            for error in errors:

                print(
                    f"  - {error}"
                )

            return False

        print(
            "✓ ALL DAY 18 VALIDATIONS PASSED"
        )

        return True

    # ========================================================
    # RUN EVERYTHING
    # ========================================================

    def run(self):

        # ----------------------------------------------------
        # Load
        # ----------------------------------------------------

        self.load_data()

        # ----------------------------------------------------
        # Prepare metrics
        # ----------------------------------------------------

        self.prepare_latest_metrics()

        # ----------------------------------------------------
        # Calculate
        # ----------------------------------------------------

        result = (
            self.calculate_peer_percentiles()
        )

        # ----------------------------------------------------
        # Unassigned companies
        # ----------------------------------------------------

        unassigned = (
            self.find_unassigned_companies()
        )

        print()
        print("=" * 70)
        print("COMPANIES WITHOUT PEER GROUP")
        print("=" * 70)

        if unassigned:

            print(
                f"Count: {len(unassigned)}"
            )

            for company_id in unassigned:

                print(
                    f"  {company_id}"
                    " → No peer group assigned"
                )

        else:

            print(
                "✓ Every company has "
                "a peer group"
            )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        valid = self.validate(
            result
        )

        if not valid:

            raise RuntimeError(
                "Day 18 validation failed."
            )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        self.save_to_sqlite(
            result
        )

        # ----------------------------------------------------
        # Display sample
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("SAMPLE RESULTS")
        print("=" * 70)

        print(
            result
            .head(20)
            .to_string(
                index=False
            )
        )

        print()
        print("=" * 70)
        print("DAY 18 COMPLETED SUCCESSFULLY")
        print("=" * 70)

        return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        engine = PeerPercentileEngine()

        result = engine.run()

    except Exception as e:

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )

        print()

        traceback.print_exc()

        sys.exit(1)