# ============================================================
# SPRINT 3 — DAY 19
# PEER RADAR CHART ENGINE
#
# N100 FINANCIAL INTELLIGENCE PLATFORM
#
# Output:
# reports/radar_charts/*.png
#
# Radar axes:
#   1. ROE
#   2. ROCE
#   3. NPM
#   4. D/E
#   5. FCF Score
#   6. PAT CAGR 5Y
#   7. Revenue CAGR 5Y
#   8. Composite Score
# ============================================================

from pathlib import Path
import sqlite3
import sys
import traceback

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

PROCESSED_DATA = PROJECT_ROOT / "Data" / "processed"

REPORTS_DIR = PROJECT_ROOT / "reports"

RADAR_DIR = REPORTS_DIR / "radar_charts"


# ============================================================
# RADAR ENGINE
# ============================================================

class RadarChartEngine:

    def __init__(self):

        self.database_path = DATABASE_PATH

        self.processed_data = PROCESSED_DATA

        self.radar_dir = RADAR_DIR

        self.peer_percentiles = None

        self.peer_groups = None

        self.companies = None

        self.radar_data = None

        # Create output directory
        self.radar_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # LOAD SQLITE DATA
    # ========================================================

    def load_database(self):

        print()
        print("=" * 70)
        print("DAY 19 — LOADING DATABASE")
        print("=" * 70)

        if not self.database_path.exists():

            raise FileNotFoundError(
                f"\nDatabase not found:\n"
                f"{self.database_path}"
            )

        print(
            f"Database:\n"
            f"{self.database_path}"
        )

        conn = sqlite3.connect(
            self.database_path
        )

        try:

            # ------------------------------------------------
            # Check tables
            # ------------------------------------------------

            tables = pd.read_sql_query(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """,
                conn
            )

            table_names = set(
                tables["name"].tolist()
            )

            print()
            print("Database tables:")

            for table in sorted(
                table_names
            ):

                print(
                    f"  ✓ {table}"
                )

            # ------------------------------------------------
            # Peer percentile table
            # ------------------------------------------------

            if (
                "peer_percentiles"
                not in table_names
            ):

                raise RuntimeError(
                    "\npeer_percentiles table "
                    "does not exist.\n"
                    "Run Day 18 first:\n"
                    "python "
                    "Script\\analytics\\peer.py"
                )

            self.peer_percentiles = (
                pd.read_sql_query(
                    """
                    SELECT *
                    FROM peer_percentiles
                    """,
                    conn
                )
            )

            # ------------------------------------------------
            # Peer groups
            # ------------------------------------------------

            if (
                "peer_groups"
                in table_names
            ):

                self.peer_groups = (
                    pd.read_sql_query(
                        """
                        SELECT *
                        FROM peer_groups
                        """,
                        conn
                    )
                )

            # ------------------------------------------------
            # Companies
            # ------------------------------------------------

            if (
                "companies"
                in table_names
            ):

                self.companies = (
                    pd.read_sql_query(
                        """
                        SELECT *
                        FROM companies
                        """,
                        conn
                    )
                )

        finally:

            conn.close()

        # ----------------------------------------------------
        # Clean columns
        # ----------------------------------------------------

        self.peer_percentiles.columns = (
            self.peer_percentiles
            .columns
            .astype(str)
            .str.strip()
        )

        if self.peer_groups is not None:

            self.peer_groups.columns = (
                self.peer_groups
                .columns
                .astype(str)
                .str.strip()
            )

        if self.companies is not None:

            self.companies.columns = (
                self.companies
                .columns
                .astype(str)
                .str.strip()
            )

        print()
        print(
            "Peer percentile rows:",
            len(self.peer_percentiles)
        )

        print(
            "Peer groups:",
            self.peer_percentiles[
                "peer_group_name"
            ].nunique()
        )

        print(
            "Companies:",
            self.peer_percentiles[
                "company_id"
            ].nunique()
        )

    # ========================================================
    # PREPARE RADAR DATA
    # ========================================================

    def prepare_data(self):

        print()
        print("=" * 70)
        print("PREPARING RADAR DATA")
        print("=" * 70)

        df = self.peer_percentiles.copy()

        # ----------------------------------------------------
        # Required columns
        # ----------------------------------------------------

        required_columns = {
            "company_id",
            "peer_group_name",
            "metric",
            "value",
            "percentile_rank",
            "year"
        }

        missing = (
            required_columns -
            set(df.columns)
        )

        if missing:

            raise ValueError(
                "Missing columns in "
                "peer_percentiles: "
                + ", ".join(
                    sorted(missing)
                )
            )

        # ----------------------------------------------------
        # Numeric conversion
        # ----------------------------------------------------

        df["value"] = pd.to_numeric(
            df["value"],
            errors="coerce"
        )

        df["percentile_rank"] = pd.to_numeric(
            df["percentile_rank"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Metric name cleanup
        # ----------------------------------------------------

        df["metric"] = (
            df["metric"]
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # Convert percentiles to 0-100
        # ----------------------------------------------------

        df["percentile_rank"] = (
            df["percentile_rank"]
            .clip(0, 100)
        )

        # ----------------------------------------------------
        # Composite score
        #
        # If Day 17 composite_quality_score is not available
        # in peer_percentiles, create a peer-relative
        # composite score from the available metrics.
        # ----------------------------------------------------

        composite_components = [
            "ROE",
            "ROCE",
            "NPM",
            "FCF",
            "PAT CAGR 5Y",
            "Revenue CAGR 5Y",
            "Interest Coverage",
            "Asset Turnover",
            "D/E"
        ]

        component_df = df[
            df["metric"].isin(
                composite_components
            )
        ].copy()

        if not component_df.empty:

            composite = (
                component_df
                .groupby(
                    [
                        "company_id",
                        "peer_group_name"
                    ],
                    dropna=False
                )["percentile_rank"]
                .mean()
                .reset_index()
            )

            composite[
                "metric"
            ] = "Composite Score"

            composite[
                "percentile_rank"
            ] = composite[
                "percentile_rank"
            ].clip(0, 100)

            composite[
                "value"
            ] = composite[
                "percentile_rank"
            ]

            composite[
                "year"
            ] = np.nan

            df = pd.concat(
                [
                    df,
                    composite
                ],
                ignore_index=True
            )

        self.radar_data = df

        print(
            f"Radar records prepared: "
            f"{len(df)}"
        )

    # ========================================================
    # METRIC NAME MAPPING
    # ========================================================

    def get_radar_metrics(self):

        return [
            "ROE",
            "ROCE",
            "NPM",
            "D/E",
            "FCF",
            "PAT CAGR 5Y",
            "Revenue CAGR 5Y",
            "Composite Score"
        ]

    # ========================================================
    # GET COMPANY NAME
    # ========================================================

    def get_company_name(
        self,
        company_id
    ):

        # ----------------------------------------------------
        # companies.csv / DB lookup
        # ----------------------------------------------------

        if self.companies is not None:

            companies = (
                self.companies.copy()
            )

            # Find ID column
            id_column = None

            if "company_id" in companies.columns:

                id_column = "company_id"

            elif "id" in companies.columns:

                id_column = "id"

            if id_column is not None:

                match = companies[
                    companies[id_column]
                    .astype(str)
                    .str.strip()
                    == str(company_id).strip()
                ]

                if not match.empty:

                    possible_name_columns = [
                        "company_name",
                        "name",
                        "Company Name"
                    ]

                    for column in (
                        possible_name_columns
                    ):

                        if column in match.columns:

                            name = (
                                match.iloc[0][
                                    column
                                ]
                            )

                            if pd.notna(name):

                                return str(
                                    name
                                ).strip()

        return str(company_id)

    # ========================================================
    # NORMALIZE COMPANY NAME FOR FILE
    # ========================================================

    @staticmethod
    def safe_filename(text):

        text = str(text)

        invalid_chars = [
            "\\",
            "/",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|"
        ]

        for char in invalid_chars:

            text = text.replace(
                char,
                "_"
            )

        return text.strip()

    # ========================================================
    # GET COMPANY RADAR VALUES
    # ========================================================

    def get_company_values(
        self,
        company_id
    ):

        df = self.radar_data[
            self.radar_data[
                "company_id"
            ].astype(str)
            == str(company_id)
        ].copy()

        metrics = self.get_radar_metrics()

        values = []

        for metric in metrics:

            match = df[
                df["metric"]
                == metric
            ]

            if match.empty:

                values.append(
                    np.nan
                )

            else:

                value = pd.to_numeric(
                    match.iloc[0][
                        "percentile_rank"
                    ],
                    errors="coerce"
                )

                values.append(
                    value
                )

        return np.array(
            values,
            dtype=float
        )

    # ========================================================
    # PEER AVERAGE
    # ========================================================

    def get_peer_average(
        self,
        peer_group_name,
        exclude_company=None
    ):

        df = self.radar_data[
            self.radar_data[
                "peer_group_name"
            ] == peer_group_name
        ].copy()

        if (
            exclude_company
            is not None
        ):

            df = df[
                df["company_id"]
                .astype(str)
                != str(exclude_company)
            ]

        metrics = self.get_radar_metrics()

        averages = []

        for metric in metrics:

            match = df[
                df["metric"]
                == metric
            ]

            if match.empty:

                averages.append(
                    np.nan
                )

            else:

                value = pd.to_numeric(
                    match[
                        "percentile_rank"
                    ],
                    errors="coerce"
                ).mean()

                averages.append(
                    value
                )

        return np.array(
            averages,
            dtype=float
        )

    # ========================================================
    # NIFTY 100 AVERAGE
    # ========================================================

    def get_nifty_average(self):

        metrics = self.get_radar_metrics()

        averages = []

        for metric in metrics:

            match = self.radar_data[
                self.radar_data[
                    "metric"
                ] == metric
            ]

            if match.empty:

                averages.append(
                    50.0
                )

            else:

                value = pd.to_numeric(
                    match[
                        "percentile_rank"
                    ],
                    errors="coerce"
                ).mean()

                if pd.isna(value):

                    value = 50.0

                averages.append(
                    value
                )

        return np.array(
            averages,
            dtype=float
        )

    # ========================================================
    # HANDLE MISSING VALUES
    # ========================================================

    @staticmethod
    def fill_missing(
        values,
        fallback=50.0
    ):

        values = np.asarray(
            values,
            dtype=float
        )

        values[
            ~np.isfinite(values)
        ] = fallback

        return np.clip(
            values,
            0,
            100
        )

    # ========================================================
    # CREATE RADAR CHART
    # ========================================================

    def create_radar_chart(
        self,
        company_id,
        company_values,
        peer_values,
        peer_group_name
    ):

        metrics = self.get_radar_metrics()

        # ----------------------------------------------------
        # Handle missing values
        # ----------------------------------------------------

        company_values = (
            self.fill_missing(
                company_values
            )
        )

        peer_values = (
            self.fill_missing(
                peer_values
            )
        )

        # ----------------------------------------------------
        # Number of axes
        # ----------------------------------------------------

        number_of_axes = len(
            metrics
        )

        angles = np.linspace(
            0,
            2 * np.pi,
            number_of_axes,
            endpoint=False
        ).tolist()

        # Close polygon
        angles += angles[:1]

        company_plot = (
            company_values.tolist()
        )

        company_plot += (
            company_plot[:1]
        )

        peer_plot = (
            peer_values.tolist()
        )

        peer_plot += (
            peer_plot[:1]
        )

        # ----------------------------------------------------
        # Figure
        # ----------------------------------------------------

        fig = plt.figure(
            figsize=(10, 10)
        )

        ax = fig.add_subplot(
            111,
            polar=True
        )

        # ----------------------------------------------------
        # Company polygon
        # ----------------------------------------------------

        ax.plot(
            angles,
            company_plot,
            linewidth=2,
            label="Company"
        )

        ax.fill(
            angles,
            company_plot,
            alpha=0.20
        )

        # ----------------------------------------------------
        # Peer average
        # ----------------------------------------------------

        ax.plot(
            angles,
            peer_plot,
            linestyle="--",
            linewidth=2,
            label="Peer Group Average"
        )

        # ----------------------------------------------------
        # Axis labels
        # ----------------------------------------------------

        ax.set_xticks(
            angles[:-1]
        )

        ax.set_xticklabels(
            metrics,
            fontsize=10
        )

        # ----------------------------------------------------
        # Scale
        # ----------------------------------------------------

        ax.set_ylim(
            0,
            100
        )

        ax.set_yticks(
            [
                20,
                40,
                60,
                80,
                100
            ]
        )

        ax.set_yticklabels(
            [
                "20",
                "40",
                "60",
                "80",
                "100"
            ],
            fontsize=8
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        company_name = (
            self.get_company_name(
                company_id
            )
        )

        title = (
            f"{company_name}\n"
            f"Peer Group: "
            f"{peer_group_name}"
        )

        ax.set_title(
            title,
            fontsize=15,
            fontweight="bold",
            pad=25
        )

        # ----------------------------------------------------
        # Legend
        # ----------------------------------------------------

        ax.legend(
            loc="upper right",
            bbox_to_anchor=(
                1.25,
                1.15
            )
        )

        # ----------------------------------------------------
        # Grid
        # ----------------------------------------------------

        ax.grid(
            True,
            alpha=0.35
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        safe_company = (
            self.safe_filename(
                company_name
            )
        )

        safe_id = (
            self.safe_filename(
                company_id
            )
        )

        filename = (
            f"{safe_id}_radar.png"
        )

        output_path = (
            self.radar_dir /
            filename
        )

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)

        return output_path

    # ========================================================
    # GENERATE ALL RADAR CHARTS
    # ========================================================

    def generate_all_charts(self):

        print()
        print("=" * 70)
        print("GENERATING RADAR CHARTS")
        print("=" * 70)

        # ----------------------------------------------------
        # Get unique companies
        # ----------------------------------------------------

        companies = (
            self.radar_data[
                [
                    "company_id",
                    "peer_group_name"
                ]
            ]
            .drop_duplicates()
        )

        total = len(
            companies
        )

        generated = 0

        failed = 0

        # ----------------------------------------------------
        # Generate chart for every company
        # ----------------------------------------------------

        for _, row in companies.iterrows():

            company_id = (
                row["company_id"]
            )

            peer_group = (
                row["peer_group_name"]
            )

            try:

                company_values = (
                    self.get_company_values(
                        company_id
                    )
                )

                # --------------------------------------------
                # Peer group exists
                # --------------------------------------------

                if pd.notna(
                    peer_group
                ):

                    peer_values = (
                        self.get_peer_average(
                            peer_group,
                            exclude_company=company_id
                        )
                    )

                    reference_name = (
                        str(peer_group)
                    )

                # --------------------------------------------
                # No peer group
                # --------------------------------------------

                else:

                    peer_values = (
                        self.get_nifty_average()
                    )

                    reference_name = (
                        "Nifty 100 Average"
                    )

                output = (
                    self.create_radar_chart(
                        company_id,
                        company_values,
                        peer_values,
                        reference_name
                    )
                )

                generated += 1

                print(
                    f"[{generated}/{total}] "
                    f"✓ {company_id} "
                    f"→ {output.name}"
                )

            except Exception as e:

                failed += 1

                print(
                    f"✗ {company_id} "
                    f"→ {type(e).__name__}: {e}"
                )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("RADAR GENERATION SUMMARY")
        print("=" * 70)

        print(
            f"Total companies: {total}"
        )

        print(
            f"Charts generated: {generated}"
        )

        print(
            f"Failed: {failed}"
        )

        print(
            f"Output directory:\n"
            f"{self.radar_dir}"
        )

        return generated, failed

    # ========================================================
    # VALIDATE OUTPUT
    # ========================================================

    def validate_output(
        self,
        generated,
        failed
    ):

        print()
        print("=" * 70)
        print("DAY 19 VALIDATION")
        print("=" * 70)

        png_files = list(
            self.radar_dir.glob(
                "*_radar.png"
            )
        )

        print(
            f"PNG files found: "
            f"{len(png_files)}"
        )

        if len(png_files) == 0:

            raise RuntimeError(
                "No radar charts were generated."
            )

        print(
            "✓ Radar chart files exist"
        )

        if failed > 0:

            print(
                f"⚠ {failed} charts failed"
            )

        else:

            print(
                "✓ All charts generated "
                "without errors"
            )

        print()
        print(
            "Sample output files:"
        )

        for file in sorted(
            png_files
        )[:10]:

            print(
                f"  ✓ {file.name}"
            )

        print()
        print(
            "✓ DAY 19 VALIDATION COMPLETE"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("SPRINT 3 — DAY 19 RADAR CHART ENGINE")
    print("=" * 70)

    try:

        engine = RadarChartEngine()

        # Load SQLite
        engine.load_database()

        # Prepare data
        engine.prepare_data()

        # Generate charts
        generated, failed = (
            engine.generate_all_charts()
        )

        # Validate
        engine.validate_output(
            generated,
            failed
        )

        print()
        print("=" * 70)
        print("DAY 19 COMPLETED")
        print("=" * 70)

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