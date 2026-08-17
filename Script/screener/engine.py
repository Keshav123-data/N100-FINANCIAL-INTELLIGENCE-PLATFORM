# ============================================================
# SPRINT 3 — SCREENER & PEER COMPARISON ENGINE
# FILE: Script/screener/engine.py
#
# Covers:
# Day 15  - Filter Engine Core
# Day 16  - Six Preset Screeners
# Day 17  - Composite Quality Score
#
# Designed for:
# N100 FINANCIAL INTELLIGENCE PLATFORM
# ============================================================

from pathlib import Path
import sys
import warnings
import sqlite3

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "Data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIG_DIR = PROJECT_ROOT / "config"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SCREENER ENGINE
# ============================================================

class ScreenerEngine:

    def __init__(self, data_dir=None):

        self.PROJECT_ROOT = PROJECT_ROOT

        self.RAW_DATA = (
            Path(data_dir)
            if data_dir
            else DATA_DIR
        )

        self.data = None

        print(
            f"Loading data from: {self.RAW_DATA}"
        )

    # ========================================================
    # GENERIC HELPERS
    # ========================================================

    @staticmethod
    def _numeric(series):

        return pd.to_numeric(
            series,
            errors="coerce"
        )

    @staticmethod
    def _year_number(series):

        return pd.to_numeric(
            series
            .astype(str)
            .str.extract(
                r"(\d{4})"
            )[0],
            errors="coerce"
        )

    @staticmethod
    def _safe_column(df, column, default=np.nan):

        if column in df.columns:
            return df[column]

        return pd.Series(
            default,
            index=df.index
        )

    # ========================================================
    # LOAD CSV
    # ========================================================

    def _read_csv(self, filename):

        path = self.RAW_DATA / filename

        if not path.exists():

            raise FileNotFoundError(
                f"\nRequired file not found:\n{path}"
            )

        df = pd.read_csv(
            path
        )

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

        print(
            "\nLoading Sprint 3 datasets..."
        )

        # ----------------------------------------------------
        # Main datasets
        # ----------------------------------------------------

        ratios = self._read_csv(
            "financial_ratios.csv"
        )

        pnl = self._read_csv(
            "profitandloss.csv"
        )

        market = self._read_csv(
            "market_cap.csv"
        )

        companies = self._read_csv(
            "companies.csv"
        )

        sectors = self._read_csv(
            "sectors.csv"
        )

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Preserve complete historical ratio data.
        #
        # We need this for:
        # FCF CAGR
        # EPS CAGR
        # D/E declining
        # ----------------------------------------------------

        ratios_history = ratios.copy()

        # ====================================================
        # NORMALIZE YEARS
        # ====================================================

        ratios_history["year_num"] = (
            self._year_number(
                ratios_history["year"]
            )
        )

        pnl["year_num"] = (
            self._year_number(
                pnl["year"]
            )
        )

        market["year_num"] = (
            self._year_number(
                market["year"]
            )
        )

        # ====================================================
        # COMPANY ID NORMALIZATION
        # ====================================================

        for df in [
            ratios_history,
            pnl,
            market,
            companies,
            sectors,
        ]:

            if "company_id" in df.columns:

                df["company_id"] = (
                    df["company_id"]
                    .astype(str)
                    .str.strip()
                )

        # companies usually uses "id"
        if "id" in companies.columns:

            companies["id"] = (
                companies["id"]
                .astype(str)
                .str.strip()
            )

        # ====================================================
        # LATEST RATIO RECORD
        # ====================================================

        ratios_latest = (
            ratios_history
            .sort_values(
                [
                    "company_id",
                    "year_num"
                ]
            )
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
            .copy()
        )

        # ====================================================
        # LATEST P&L RECORD
        # ====================================================

        pnl_latest = (
            pnl
            .sort_values(
                [
                    "company_id",
                    "year_num"
                ]
            )
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
            .copy()
        )

        # ====================================================
        # LATEST MARKET RECORD
        # ====================================================

        market_latest = (
            market
            .sort_values(
                [
                    "company_id",
                    "year_num"
                ]
            )
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
            .copy()
        )

        # ====================================================
        # COMPANY INFORMATION
        # ====================================================

        company_columns = [
            "id",
            "company_name",
            "roce_percentage",
            "roe_percentage",
        ]

        company_columns = [
            c
            for c in company_columns
            if c in companies.columns
        ]

        companies = companies[
            company_columns
        ].copy()

        companies = companies.rename(
            columns={
                "id": "company_id"
            }
        )

        # ====================================================
        # SECTOR INFORMATION
        # ====================================================

        sector_columns = [
            "company_id",
            "broad_sector",
            "sub_sector",
            "market_cap_category",
        ]

        sector_columns = [
            c
            for c in sector_columns
            if c in sectors.columns
        ]

        sectors = sectors[
            sector_columns
        ].copy()

        # ====================================================
        # P&L COLUMNS
        # ====================================================

        pnl_columns = [
            "company_id",
            "sales",
            "net_profit",
            "eps",
            "dividend_payout",
            "operating_profit",
        ]

        pnl_columns = [
            c
            for c in pnl_columns
            if c in pnl_latest.columns
        ]

        pnl_latest = pnl_latest[
            pnl_columns
        ].copy()

        # ====================================================
        # MARKET COLUMNS
        # ====================================================

        market_columns = [
            "company_id",
            "market_cap_crore",
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct",
        ]

        market_columns = [
            c
            for c in market_columns
            if c in market_latest.columns
        ]

        market_latest = market_latest[
            market_columns
        ].copy()

        # ====================================================
        # MERGE
        # ====================================================

        df = ratios_latest.merge(
            pnl_latest,
            on="company_id",
            how="left",
            suffixes=(
                "",
                "_pnl"
            )
        )

        df = df.merge(
            market_latest,
            on="company_id",
            how="left"
        )

        df = df.merge(
            companies,
            on="company_id",
            how="left"
        )

        df = df.merge(
            sectors,
            on="company_id",
            how="left"
        )

        # ====================================================
        # RENAME TO SCREENER NAMES
        # ====================================================

        rename_map = {

            "net_profit_margin_pct":
                "npm",

            "operating_profit_margin_pct":
                "opm",

            "return_on_equity_pct":
                "roe",

            "debt_to_equity":
                "de",

            "interest_coverage":
                "icr",

            "free_cash_flow_cr":
                "fcf",

            "cash_from_operations_cr":
                "cfo",

            "earnings_per_share":
                "eps_ratio",

            "roce_percentage":
                "roce",

            "market_cap_crore":
                "market_cap",

            "pe_ratio":
                "pe",

            "pb_ratio":
                "pb",

            "dividend_yield_pct":
                "dividend_yield",

            "dividend_payout":
                "dividend_payout_pct",
        }

        df = df.rename(
            columns=rename_map
        )

        # ====================================================
        # NUMERIC CONVERSION
        # ====================================================

        numeric_columns = [

            "roe",
            "roce",
            "npm",
            "opm",
            "de",
            "icr",
            "asset_turnover",

            "fcf",
            "cfo",
            "eps_ratio",

            "sales",
            "net_profit",

            "market_cap",
            "pe",
            "pb",

            "dividend_yield",
            "dividend_payout_pct",
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = (
                    pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )
                )

            else:

                df[column] = np.nan

        # ====================================================
        # DEBT FREE
        # ====================================================

        df["debt_free"] = (
            df["de"]
            .fillna(0)
            .le(0)
        )

        # Debt-free companies:
        # ICR = infinity
        # Therefore they pass every ICR minimum.

        df.loc[
            df["debt_free"]
            & df["icr"].isna(),
            "icr"
        ] = np.inf

        # ====================================================
        # FCF POSITIVE
        # ====================================================

        df["fcf_positive"] = (
            df["fcf"]
            .fillna(0)
            .gt(0)
            .astype(int)
        )

        # ====================================================
        # CFO / PAT
        # ====================================================

        df["cfo_pat_ratio"] = np.where(

            df["net_profit"]
            .abs()
            .gt(0),

            df["cfo"] /
            df["net_profit"],

            np.nan
        )

        # ====================================================
        # HISTORICAL CAGR
        #
        # IMPORTANT:
        # Use ratios_history, NOT ratios_latest.
        # ====================================================

        df = self._add_cagr_metrics(
            df,
            pnl,
            ratios_history
        )

        # ====================================================
        # REQUIRED COLUMNS
        # ====================================================

        required_columns = [

            "revenue_cagr_3y",
            "revenue_cagr_5y",

            "pat_cagr_5y",

            "eps_cagr_5y",

            "fcf_cagr_5y",

            "de_declining",
        ]

        for column in required_columns:

            if column not in df.columns:

                if column == "de_declining":

                    df[column] = False

                else:

                    df[column] = np.nan

        # ====================================================
        # CLEAN COMPANY NAME
        # ====================================================

        if "company_name" in df.columns:

            df["company_name"] = (
                df["company_name"]
                .astype(str)
                .str.replace(
                    "\n",
                    " ",
                    regex=False
                )
                .str.strip()
            )

        # ====================================================
        # REMOVE DUPLICATES
        # ====================================================

        df = (
            df
            .drop_duplicates(
                subset=["company_id"]
            )
            .reset_index(drop=True)
        )

        self.data = df

        print(
            f"\nPrepared screener dataset: "
            f"{df.shape[0]} rows × "
            f"{df.shape[1]} columns"
        )

        return self.data

    # ========================================================
    # CAGR METRICS
    # ========================================================

    def _add_cagr_metrics(
        self,
        df,
        pnl,
        ratios
    ):

        # ====================================================
        # P&L HISTORY
        # ====================================================

        pnl = pnl.copy()

        pnl["year_num"] = (
            self._year_number(
                pnl["year"]
            )
        )

        pnl = pnl.dropna(
            subset=["year_num"]
        )

        pnl = pnl.sort_values(
            [
                "company_id",
                "year_num"
            ]
        )

        pnl_results = []

        # ====================================================
        # COMPANY CAGR
        # ====================================================

        for company_id, group in pnl.groupby(
            "company_id"
        ):

            group = (
                group
                .sort_values("year_num")
                .copy()
            )

            result = {
                "company_id": company_id
            }

            # ------------------------------------------------
            # REVENUE CAGR 5Y
            # ------------------------------------------------

            if len(group) >= 6:

                first = group.iloc[-6]
                last = group.iloc[-1]

                revenue_start = pd.to_numeric(
                    first.get("sales"),
                    errors="coerce"
                )

                revenue_end = pd.to_numeric(
                    last.get("sales"),
                    errors="coerce"
                )

                if (
                    pd.notna(revenue_start)
                    and pd.notna(revenue_end)
                    and revenue_start > 0
                    and revenue_end > 0
                ):

                    result[
                        "revenue_cagr_5y"
                    ] = (

                        (
                            revenue_end /
                            revenue_start
                        )
                        ** (1 / 5)

                        - 1

                    ) * 100

                # --------------------------------------------
                # PAT CAGR 5Y
                # --------------------------------------------

                pat_start = pd.to_numeric(
                    first.get("net_profit"),
                    errors="coerce"
                )

                pat_end = pd.to_numeric(
                    last.get("net_profit"),
                    errors="coerce"
                )

                if (
                    pd.notna(pat_start)
                    and pd.notna(pat_end)
                    and pat_start > 0
                    and pat_end > 0
                ):

                    result[
                        "pat_cagr_5y"
                    ] = (

                        (
                            pat_end /
                            pat_start
                        )
                        ** (1 / 5)

                        - 1

                    ) * 100

            # ------------------------------------------------
            # REVENUE CAGR 3Y
            # ------------------------------------------------

            if len(group) >= 4:

                first3 = group.iloc[-4]
                last3 = group.iloc[-1]

                revenue_start3 = pd.to_numeric(
                    first3.get("sales"),
                    errors="coerce"
                )

                revenue_end3 = pd.to_numeric(
                    last3.get("sales"),
                    errors="coerce"
                )

                if (
                    pd.notna(revenue_start3)
                    and pd.notna(revenue_end3)
                    and revenue_start3 > 0
                    and revenue_end3 > 0
                ):

                    result[
                        "revenue_cagr_3y"
                    ] = (

                        (
                            revenue_end3 /
                            revenue_start3
                        )
                        ** (1 / 3)

                        - 1

                    ) * 100

            pnl_results.append(
                result
            )

        pnl_cagr = pd.DataFrame(
            pnl_results
        )

        if not pnl_cagr.empty:

            df = df.merge(
                pnl_cagr,
                on="company_id",
                how="left"
            )

        # ====================================================
        # RATIOS HISTORY
        # ====================================================

        ratios = ratios.copy()

        ratios["year_num"] = (
            self._year_number(
                ratios["year"]
            )
        )

        ratios = ratios.dropna(
            subset=["year_num"]
        )

        ratios = ratios.sort_values(
            [
                "company_id",
                "year_num"
            ]
        )

        ratio_results = []

        # ====================================================
        # EPS + FCF CAGR
        # ====================================================

        for company_id, group in ratios.groupby(
            "company_id"
        ):

            group = (
                group
                .sort_values("year_num")
                .copy()
            )

            result = {
                "company_id": company_id
            }

            # ------------------------------------------------
            # EPS CAGR
            # ------------------------------------------------

            if "earnings_per_share" in group.columns:

                eps_group = (
                    group
                    .copy()
                )

                eps_group[
                    "earnings_per_share"
                ] = pd.to_numeric(
                    eps_group[
                        "earnings_per_share"
                    ],
                    errors="coerce"
                )

                eps_group = (
                    eps_group
                    .dropna(
                        subset=[
                            "earnings_per_share"
                        ]
                    )
                )

                if len(eps_group) >= 6:

                    eps_start = (
                        eps_group.iloc[-6][
                            "earnings_per_share"
                        ]
                    )

                    eps_end = (
                        eps_group.iloc[-1][
                            "earnings_per_share"
                        ]
                    )

                    if (
                        eps_start > 0
                        and eps_end > 0
                    ):

                        result[
                            "eps_cagr_5y"
                        ] = (

                            (
                                eps_end /
                                eps_start
                            )
                            ** (1 / 5)

                            - 1

                        ) * 100

            # ------------------------------------------------
            # FCF CAGR
            # ------------------------------------------------

            if "free_cash_flow_cr" in group.columns:

                fcf_group = (
                    group
                    .copy()
                )

                fcf_group[
                    "free_cash_flow_cr"
                ] = pd.to_numeric(
                    fcf_group[
                        "free_cash_flow_cr"
                    ],
                    errors="coerce"
                )

                fcf_group = (
                    fcf_group
                    .dropna(
                        subset=[
                            "free_cash_flow_cr"
                        ]
                    )
                )

                if len(fcf_group) >= 6:

                    fcf_start = (
                        fcf_group.iloc[-6][
                            "free_cash_flow_cr"
                        ]
                    )

                    fcf_end = (
                        fcf_group.iloc[-1][
                            "free_cash_flow_cr"
                        ]
                    )

                    # CAGR only when both
                    # start and end are positive.

                    if (
                        fcf_start > 0
                        and fcf_end > 0
                    ):

                        result[
                            "fcf_cagr_5y"
                        ] = (

                            (
                                fcf_end /
                                fcf_start
                            )
                            ** (1 / 5)

                            - 1

                        ) * 100

            ratio_results.append(
                result
            )

        ratio_cagr = pd.DataFrame(
            ratio_results
        )

        if not ratio_cagr.empty:

            df = df.merge(
                ratio_cagr,
                on="company_id",
                how="left"
            )

        # ====================================================
        # D/E DECLINING
        # ====================================================

        de_results = []

        if "debt_to_equity" in ratios.columns:

            for company_id, group in ratios.groupby(
                "company_id"
            ):

                group = (
                    group
                    .sort_values("year_num")
                    .copy()
                )

                group[
                    "debt_to_equity"
                ] = pd.to_numeric(
                    group[
                        "debt_to_equity"
                    ],
                    errors="coerce"
                )

                de_group = (
                    group
                    .dropna(
                        subset=[
                            "debt_to_equity"
                        ]
                    )
                )

                declining = False

                if len(de_group) >= 2:

                    previous_de = (
                        de_group.iloc[-2][
                            "debt_to_equity"
                        ]
                    )

                    latest_de = (
                        de_group.iloc[-1][
                            "debt_to_equity"
                        ]
                    )

                    declining = (
                        latest_de <
                        previous_de
                    )

                de_results.append({
                    "company_id": company_id,
                    "de_declining": declining
                })

        de_df = pd.DataFrame(
            de_results
        )

        if not de_df.empty:

            df = df.merge(
                de_df,
                on="company_id",
                how="left"
            )

        # ====================================================
        # ENSURE COLUMNS
        # ====================================================

        required = [

            "revenue_cagr_3y",
            "revenue_cagr_5y",
            "pat_cagr_5y",
            "eps_cagr_5y",
            "fcf_cagr_5y",
        ]

        for column in required:

            if column not in df.columns:

                df[column] = np.nan

        if "de_declining" not in df.columns:

            df["de_declining"] = False

        return df

    # ========================================================
    # FILTER ENGINE
    # ========================================================

    def apply_filters(
        self,
        filters=None,
        data=None
    ):

        if data is None:

            if self.data is None:
                self.load_data()

            data = self.data.copy()

        else:

            data = data.copy()

        if filters is None:
            filters = {}

        # ====================================================
        # START MASK
        # ====================================================

        mask = pd.Series(
            True,
            index=data.index
        )

        # ====================================================
        # ROE
        # ====================================================

        if filters.get("roe_min") is not None:

            mask &= (
                data["roe"]
                >= filters["roe_min"]
            )

        # ====================================================
        # D/E
        # ====================================================

        if filters.get("de_max") is not None:

            financials = (
                data["broad_sector"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("financials")
            )

            mask &= (
                financials
                |
                (
                    data["de"]
                    <= filters["de_max"]
                )
            )

        # ====================================================
        # FCF
        # ====================================================

        if filters.get("fcf_min") is not None:

            mask &= (
                data["fcf"]
                >= filters["fcf_min"]
            )

        # ====================================================
        # REVENUE CAGR 5Y
        # ====================================================

        if filters.get(
            "revenue_cagr_5y_min"
        ) is not None:

            mask &= (
                data["revenue_cagr_5y"]
                >= filters[
                    "revenue_cagr_5y_min"
                ]
            )

        # ====================================================
        # REVENUE CAGR 3Y
        # ====================================================

        if filters.get(
            "revenue_cagr_3y_min"
        ) is not None:

            mask &= (
                data["revenue_cagr_3y"]
                >= filters[
                    "revenue_cagr_3y_min"
                ]
            )

        # ====================================================
        # PAT CAGR 5Y
        # ====================================================

        if filters.get(
            "pat_cagr_5y_min"
        ) is not None:

            mask &= (
                data["pat_cagr_5y"]
                >= filters[
                    "pat_cagr_5y_min"
                ]
            )

        # ====================================================
        # OPM
        # ====================================================

        if filters.get("opm_min") is not None:

            mask &= (
                data["opm"]
                >= filters["opm_min"]
            )

        # ====================================================
        # P/E
        # ====================================================

        if filters.get("pe_max") is not None:

            mask &= (
                data["pe"]
                <= filters["pe_max"]
            )

        # ====================================================
        # P/B
        # ====================================================

        if filters.get("pb_max") is not None:

            mask &= (
                data["pb"]
                <= filters["pb_max"]
            )

        # ====================================================
        # DIVIDEND YIELD
        # ====================================================

        if filters.get(
            "dividend_yield_min"
        ) is not None:

            mask &= (
                data["dividend_yield"]
                >= filters[
                    "dividend_yield_min"
                ]
            )

        # ====================================================
        # DIVIDEND PAYOUT
        # ====================================================

        if filters.get(
            "dividend_payout_max"
        ) is not None:

            mask &= (
                data["dividend_payout_pct"]
                <= filters[
                    "dividend_payout_max"
                ]
            )

        # ====================================================
        # ICR
        # ====================================================

        if filters.get("icr_min") is not None:

            mask &= (
                data["icr"]
                >= filters["icr_min"]
            )

        # ====================================================
        # MARKET CAP
        # ====================================================

        if filters.get(
            "market_cap_min"
        ) is not None:

            mask &= (
                data["market_cap"]
                >= filters[
                    "market_cap_min"
                ]
            )

        # ====================================================
        # NET PROFIT
        # ====================================================

        if filters.get(
            "net_profit_min"
        ) is not None:

            mask &= (
                data["net_profit"]
                >= filters[
                    "net_profit_min"
                ]
            )

        # ====================================================
        # EPS CAGR
        # ====================================================

        if filters.get(
            "eps_cagr_5y_min"
        ) is not None:

            mask &= (
                data["eps_cagr_5y"]
                >= filters[
                    "eps_cagr_5y_min"
                ]
            )

        # ====================================================
        # ASSET TURNOVER
        # ====================================================

        if filters.get(
            "asset_turnover_min"
        ) is not None:

            mask &= (
                data["asset_turnover"]
                >= filters[
                    "asset_turnover_min"
                ]
            )

        # ====================================================
        # SALES
        # ====================================================

        if filters.get(
            "sales_min"
        ) is not None:

            mask &= (
                data["sales"]
                >= filters[
                    "sales_min"
                ]
            )

        # ====================================================
        # D/E DECLINING
        # ====================================================

        if filters.get(
            "de_declining"
        ) is True:

            mask &= (
                data["de_declining"]
                == True
            )

        # ====================================================
        # RESULT
        # ====================================================

        result = data.loc[
            mask
        ].copy()

        # ====================================================
        # COMPOSITE SCORE
        # ====================================================

        result[
            "composite_quality_score"
        ] = self.calculate_composite_score(
            result
        )

        # ====================================================
        # SORT
        # ====================================================

        result = (
            result
            .sort_values(
                "composite_quality_score",
                ascending=False
            )
            .reset_index(drop=True)
        )

        return result

    # ========================================================
    # WINSOR NORMALIZATION
    # ========================================================

    @staticmethod
    def winsor_normalize(series):

        series = pd.to_numeric(
            series,
            errors="coerce"
        )

        series = series.replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )

        if series.dropna().empty:

            return pd.Series(
                50.0,
                index=series.index
            )

        p10 = series.quantile(
            0.10
        )

        p90 = series.quantile(
            0.90
        )

        if (
            pd.isna(p10)
            or pd.isna(p90)
        ):

            return pd.Series(
                50.0,
                index=series.index
            )

        if p10 == p90:

            return pd.Series(
                50.0,
                index=series.index
            )

        clipped = series.clip(
            lower=p10,
            upper=p90
        )

        score = (
            (
                clipped - p10
            )
            /
            (
                p90 - p10
            )
            * 100
        )

        median = (
            score
            .dropna()
            .median()
        )

        if pd.isna(median):

            median = 50.0

        return score.fillna(
            median
        )

    # ========================================================
    # COMPOSITE QUALITY SCORE
    #
    # Profitability 35%
    # Cash Quality  30%
    # Growth        20%
    # Leverage      15%
    # ========================================================

    def calculate_composite_score(
        self,
        df
    ):

        if df.empty:

            return pd.Series(
                dtype=float,
                index=df.index
            )

        data = df.copy()

        # ====================================================
        # REQUIRED SCORING COLUMNS
        # ====================================================

        required = [

            "roe",
            "roce",
            "npm",

            "fcf_cagr_5y",
            "cfo_pat_ratio",
            "fcf_positive",

            "revenue_cagr_5y",
            "pat_cagr_5y",

            "de",
            "icr",
        ]

        for column in required:

            if column not in data.columns:

                if column == "fcf_positive":

                    data[column] = 0

                else:

                    data[column] = np.nan

        # ====================================================
        # PROFITABILITY — 35%
        # ====================================================

        roe_score = self.winsor_normalize(
            data["roe"]
        )

        roce_score = self.winsor_normalize(
            data["roce"]
        )

        npm_score = self.winsor_normalize(
            data["npm"]
        )

        profitability_score = (

            roe_score * 0.15

            + roce_score * 0.10

            + npm_score * 0.10
        )

        # ====================================================
        # CASH QUALITY — 30%
        # ====================================================

        fcf_cagr_score = (
            self.winsor_normalize(
                data["fcf_cagr_5y"]
            )
        )

        cfo_pat_score = (
            self.winsor_normalize(
                data["cfo_pat_ratio"]
            )
        )

        fcf_positive_score = (
            data["fcf_positive"]
            .fillna(0)
            * 100
        )

        cash_quality_score = (

            fcf_cagr_score * 0.15

            + cfo_pat_score * 0.10

            + fcf_positive_score * 0.05
        )

        # ====================================================
        # GROWTH — 20%
        # ====================================================

        revenue_growth_score = (
            self.winsor_normalize(
                data["revenue_cagr_5y"]
            )
        )

        pat_growth_score = (
            self.winsor_normalize(
                data["pat_cagr_5y"]
            )
        )

        growth_score = (

            revenue_growth_score * 0.10

            + pat_growth_score * 0.10
        )

        # ====================================================
        # LEVERAGE — 15%
        # ====================================================

        de_score = (
            100
            - self.winsor_normalize(
                data["de"]
            )
        )

        icr_score = (
            self.winsor_normalize(
                data["icr"]
            )
        )

        leverage_score = (

            de_score * 0.10

            + icr_score * 0.05
        )

        # ====================================================
        # FINAL SCORE
        # ====================================================

        final_score = (

            profitability_score

            + cash_quality_score

            + growth_score

            + leverage_score
        )

        return (
            final_score
            .clip(0, 100)
            .round(2)
        )

    # ========================================================
    # SECTOR RELATIVE SCORE
    #
    # Normalises scores within broad_sector.
    # ========================================================

    def calculate_sector_relative_score(
        self,
        df
    ):

        data = df.copy()

        if (
            "broad_sector" not in data.columns
            or "composite_quality_score"
            not in data.columns
        ):

            return pd.Series(
                np.nan,
                index=data.index
            )

        scores = pd.Series(
            np.nan,
            index=data.index
        )

        for sector, index in (
            data
            .groupby(
                "broad_sector"
            )
            .groups
            .items()
        ):

            sector_scores = (
                data.loc[
                    index,
                    "composite_quality_score"
                ]
            )

            scores.loc[index] = (
                self.winsor_normalize(
                    sector_scores
                )
            )

        return (
            scores
            .clip(0, 100)
            .round(2)
        )

    # ========================================================
    # DAY 18 — PEER PERCENTILE RANKINGS
    #
    # Calculates percentile rankings for:
    # ROE
    # ROCE
    # NPM
    # D/E
    # FCF
    # PAT CAGR 5Y
    # Revenue CAGR 5Y
    # EPS CAGR 5Y
    # Interest Coverage
    # Asset Turnover
    #
    # D/E is inverse:
    # Lower D/E = Higher percentile
    # ========================================================

    def load_peer_groups(self, peer_file=None):

        if peer_file is None:
            peer_file = self.RAW_DATA.parent.parent / "peer_groups.xlsx"

        peer_file = Path(peer_file)

        if not peer_file.exists():
            raise FileNotFoundError(
                f"\nPeer groups file not found:\n{peer_file}"
            )

        print()
        print("Loading peer groups from:")
        print(peer_file)

        # Read all sheets
        sheets = pd.read_excel(
            peer_file,
            sheet_name=None
        )

        print(
            f"Peer group sheets found: {len(sheets)}"
        )

        all_groups = []

        for sheet_name, group_df in sheets.items():

            if group_df is None or group_df.empty:
                continue

            group_df.columns = (
                group_df.columns
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # ------------------------------------------------
            # Find company ID column
            # ------------------------------------------------

            company_col = None

            for candidate in [
                "company_id",
                "id",
                "company"
            ]:
                if candidate in group_df.columns:
                    company_col = candidate
                    break

            if company_col is None:
                print(
                    f"  ⚠ Skipping sheet '{sheet_name}' "
                    f"— company_id column not found"
                )
                continue

            temp = pd.DataFrame()

            temp["company_id"] = (
                group_df[company_col]
                .astype(str)
                .str.strip()
            )

            temp["peer_group_name"] = (
                str(sheet_name).strip()
            )

            temp = temp[
                temp["company_id"]
                .notna()
            ]

            temp = temp[
                temp["company_id"]
                .ne("")
            ]

            temp = temp[
                temp["company_id"]
                .str.lower()
                .ne("nan")
            ]

            all_groups.append(temp)

        if not all_groups:

            raise ValueError(
                "No valid peer groups were found "
                "in peer_groups.xlsx"
            )

        peer_groups = pd.concat(
            all_groups,
            ignore_index=True
        )

        peer_groups = (
            peer_groups
            .drop_duplicates(
                subset=[
                    "company_id",
                    "peer_group_name"
                ]
            )
            .reset_index(drop=True)
        )

        print(
            f"Companies assigned to peer groups: "
            f"{len(peer_groups)}"
        )

        print(
            f"Peer groups: "
            f"{peer_groups['peer_group_name'].nunique()}"
        )

        return peer_groups

    # ========================================================
    # DAY 18 — PERCENTILE FUNCTION
    # ========================================================

    @staticmethod
    def _percentile_rank(series):

        numeric = pd.to_numeric(
            series,
            errors="coerce"
        )

        result = pd.Series(
            np.nan,
            index=series.index,
            dtype=float
        )

        valid = numeric.notna()

        count = valid.sum()

        if count == 0:
            return result

        if count == 1:

            result.loc[valid] = 100.0

            return result

        ranks = (
            numeric[valid]
            .rank(
                method="average",
                pct=True
            )
            * 100
        )

        result.loc[valid] = ranks

        return result

    # ========================================================
    # DAY 18 — PEER PERCENTILE CALCULATION
    # ========================================================

    def calculate_peer_percentiles(
        self,
        data=None,
        peer_groups=None
    ):

        if data is None:

            if self.data is None:
                self.load_data()

            data = self.data.copy()

        else:

            data = data.copy()

        # ----------------------------------------------------
        # Load peer groups
        # ----------------------------------------------------

        if peer_groups is None:

            peer_groups = (
                self.load_peer_groups()
            )

        peer_groups = peer_groups.copy()

        # ----------------------------------------------------
        # Normalize company IDs
        # ----------------------------------------------------

        data["company_id"] = (
            data["company_id"]
            .astype(str)
            .str.strip()
        )

        peer_groups["company_id"] = (
            peer_groups["company_id"]
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # Merge peer groups with screener data
        # ----------------------------------------------------

        merged = peer_groups.merge(
            data,
            on="company_id",
            how="left"
        )

        print()
        print(
            f"Peer records to process: "
            f"{len(merged)}"
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        metrics = {

            "roe": "roe",

            "roce": "roce",

            "net_profit_margin": "npm",

            "de": "de",

            "fcf": "fcf",

            "pat_cagr_5y": "pat_cagr_5y",

            "revenue_cagr_5y":
                "revenue_cagr_5y",

            "eps_cagr_5y":
                "eps_cagr_5y",

            "interest_coverage":
                "icr",

            "asset_turnover":
                "asset_turnover",
        }

        results = []

        # ----------------------------------------------------
        # Process each peer group
        # ----------------------------------------------------

        for peer_group_name, group in (
            merged
            .groupby(
                "peer_group_name"
            )
        ):

            print()
            print(
                f"Processing: "
                f"{peer_group_name}"
            )

            print(
                f"  Companies: {len(group)}"
            )

            # ------------------------------------------------
            # Process each metric
            # ------------------------------------------------

            for metric_name, column_name in (
                metrics.items()
            ):

                if column_name not in group.columns:
                    values = pd.Series(
                        np.nan,
                        index=group.index
                    )
                else:
                    values = pd.to_numeric(
                        group[column_name],
                        errors="coerce"
                    )

                # --------------------------------------------
                # D/E — INVERSE RANKING
                #
                # Lower D/E = Better
                # --------------------------------------------

                if metric_name == "de":

                    normal_percentile = (
                        self._percentile_rank(
                            values
                        )
                    )

                    percentile = (
                        100
                        - normal_percentile
                    )

                    # If only one valid company,
                    # keep it at 100.
                    valid_count = (
                        values.notna().sum()
                    )

                    if valid_count == 1:

                        percentile.loc[
                            values.notna()
                        ] = 100.0

                else:

                    percentile = (
                        self._percentile_rank(
                            values
                        )
                    )

                # --------------------------------------------
                # Create result rows
                # --------------------------------------------

                for idx in group.index:

                    value = values.loc[idx]

                    rank = percentile.loc[idx]

                    results.append({

                        "company_id":
                            group.loc[
                                idx,
                                "company_id"
                            ],

                        "peer_group_name":
                            peer_group_name,

                        "metric":
                            metric_name,

                        "value":
                            value,

                        "percentile_rank":
                            rank,

                        "year":
                            group.loc[
                                idx,
                                "year_num"
                            ]
                            if "year_num"
                            in group.columns
                            else np.nan
                    })

        result_df = pd.DataFrame(
            results
        )

        if result_df.empty:

            print(
                "\n⚠ No percentile results generated."
            )

            return result_df

        # ----------------------------------------------------
        # Round percentile
        # ----------------------------------------------------

        result_df[
            "percentile_rank"
        ] = (
            pd.to_numeric(
                result_df[
                    "percentile_rank"
                ],
                errors="coerce"
            )
            .clip(0, 100)
            .round(2)
        )

        # ----------------------------------------------------
        # Numeric values
        # ----------------------------------------------------

        result_df["value"] = pd.to_numeric(
            result_df["value"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Remove duplicate rows
        # ----------------------------------------------------

        result_df = (
            result_df
            .drop_duplicates(
                subset=[
                    "company_id",
                    "peer_group_name",
                    "metric"
                ]
            )
            .reset_index(drop=True)
        )

        print()
        print("=" * 70)
        print(
            "DAY 18 — PEER PERCENTILE SUMMARY"
        )
        print("=" * 70)

        print(
            f"Peer groups: "
            f"{result_df['peer_group_name'].nunique()}"
        )

        print(
            f"Companies: "
            f"{result_df['company_id'].nunique()}"
        )

        print(
            f"Metrics: "
            f"{result_df['metric'].nunique()}"
        )

        print(
            f"Rows generated: "
            f"{len(result_df)}"
        )

        return result_df

    # ========================================================
    # DAY 18 — SAVE TO SQLITE
    # ========================================================

    def save_peer_percentiles(
        self,
        percentile_df,
        database_path=None
    ):

        if percentile_df is None:
            raise ValueError(
                "percentile_df is None"
            )

        if percentile_df.empty:
            raise ValueError(
                "Cannot save empty peer percentile data"
            )

        # ----------------------------------------------------
        # Default database path
        # ----------------------------------------------------

        if database_path is None:

            database_path = (
                self.PROJECT_ROOT
                / "DB"
                / "nifty100.db"
            )

        database_path = Path(
            database_path
        )

        if not database_path.exists():

            raise FileNotFoundError(
                f"\nDatabase not found:\n"
                f"{database_path}"
            )

        print()
        print(
            "Saving peer_percentiles table..."
        )

        # ----------------------------------------------------
        # Connect
        # ----------------------------------------------------

        connection = sqlite3.connect(
            database_path
        )

        try:

            percentile_df.to_sql(
                "peer_percentiles",
                connection,
                if_exists="replace",
                index=False
            )

            connection.commit()

        finally:

            connection.close()

        print(
            "✓ peer_percentiles table created"
        )

        print(
            f"  Database: {database_path}"
        )

        print(
            f"  Rows: {len(percentile_df)}"
        )

        return True

    # ========================================================
    # DAY 18 — COMPLETE RUNNER
    # ========================================================

    def run_peer_percentiles(
        self,
        peer_file=None,
        database_path=None
    ):

        print()
        print("=" * 70)
        print(
            "SPRINT 3 — DAY 18"
        )
        print(
            "PEER PERCENTILE RANKINGS"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # Load screener data
        # ----------------------------------------------------

        if self.data is None:

            self.load_data()

        # ----------------------------------------------------
        # Load peer groups
        # ----------------------------------------------------

        peer_groups = (
            self.load_peer_groups(
                peer_file
            )
        )

        # ----------------------------------------------------
        # Calculate percentiles
        # ----------------------------------------------------

        percentile_df = (
            self.calculate_peer_percentiles(
                self.data,
                peer_groups
            )
        )

        # ----------------------------------------------------
        # Save to SQLite
        # ----------------------------------------------------

        self.save_peer_percentiles(
            percentile_df,
            database_path
        )

        # ----------------------------------------------------
        # Show sample
        # ----------------------------------------------------

        print()
        print(
            "Sample percentile results:"
        )

        print(
            percentile_df
            .head(20)
            .to_string(
                index=False
            )
        )

        print()
        print("=" * 70)
        print(
            "DAY 18 COMPLETED SUCCESSFULLY"
        )
        print("=" * 70)

        return percentile_df

    # ============================================================
# DAY 18 TEST
# ============================================================

        print()
        print("=" * 70)
        print("SPRINT 3 — DAY 18")
        print("PEER PERCENTILE RANKINGS")
        print("=" * 70)

        try:

            peer_percentiles = (
            engine.run_peer_percentiles()
            )

            print()
            print("Day 18 result:")
            print(
        peer_percentiles.shape
    )

        except Exception as e:

            print()
            print("=" * 70)
            print("DAY 18 ERROR")
            print("=" * 70)

            print(
            type(e).__name__,
            ":",
            e
        )

        import traceback

        traceback.print_exc()

    # ========================================================
    # PRESET 1 — QUALITY COMPOUNDER
    # ========================================================

    def quality_compounder(self):

        return self.apply_filters({

            "roe_min": 15,

            "de_max": 1.0,

            "fcf_min": 0,

            "revenue_cagr_5y_min": 10,
        })

    # ========================================================
    # PRESET 2 — VALUE PICK
    # ========================================================

    def value_pick(self):

        return self.apply_filters({

            "pe_max": 20,

            "pb_max": 3.0,

            "de_max": 2.0,

            "dividend_yield_min": 1,
        })

    # ========================================================
    # PRESET 3 — GROWTH ACCELERATOR
    # ========================================================

    def growth_accelerator(self):

        return self.apply_filters({

            "pat_cagr_5y_min": 20,

            "revenue_cagr_5y_min": 15,

            "de_max": 2.0,
        })

    # ========================================================
    # PRESET 4 — DIVIDEND CHAMPION
    # ========================================================

    def dividend_champion(self):

        return self.apply_filters({

            "dividend_yield_min": 2,

            "dividend_payout_max": 80,

            "fcf_min": 0,
        })

    # ========================================================
    # PRESET 5 — DEBT-FREE BLUE CHIP
    # ========================================================

    def debt_free_blue_chip(self):

        return self.apply_filters({

            "de_max": 0,

            "roe_min": 12,

            "sales_min": 5000,
        })

    # ========================================================
    # PRESET 6 — TURNAROUND WATCH
    # ========================================================

    def turnaround_watch(self):

        return self.apply_filters({

            "revenue_cagr_3y_min": 10,

            "fcf_min": 0,

            "de_declining": True,
        })

    # ========================================================
    # RUN ALL 6 PRESETS
    # ========================================================

    def run_all_presets(self):

        return {

            "Quality Compounder":
                self.quality_compounder(),

            "Value Pick":
                self.value_pick(),

            "Growth Accelerator":
                self.growth_accelerator(),

            "Dividend Champion":
                self.dividend_champion(),

            "Debt-Free Blue Chip":
                self.debt_free_blue_chip(),

            "Turnaround Watch":
                self.turnaround_watch(),
        }

    # ========================================================
    # GET PRESET
    # ========================================================

    def run_preset(
        self,
        preset_name
    ):

        presets = {

            "Quality Compounder":
                self.quality_compounder,

            "Value Pick":
                self.value_pick,

            "Growth Accelerator":
                self.growth_accelerator,

            "Dividend Champion":
                self.dividend_champion,

            "Debt-Free Blue Chip":
                self.debt_free_blue_chip,

            "Turnaround Watch":
                self.turnaround_watch,
        }

        if preset_name not in presets:

            raise ValueError(
                f"Unknown preset: "
                f"{preset_name}\n\n"
                f"Available presets:\n"
                + "\n".join(
                    presets.keys()
                )
            )

        return presets[
            preset_name
        ]()

    # ========================================================
    # EXPORT SINGLE RESULT
    # ========================================================

    def prepare_export(
        self,
        df
    ):

        preferred_columns = [

            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",

            "roe",
            "roce",
            "npm",
            "opm",

            "fcf",
            "fcf_cagr_5y",
            "cfo_pat_ratio",
            "fcf_positive",

            "revenue_cagr_3y",
            "revenue_cagr_5y",

            "pat_cagr_5y",
            "eps_cagr_5y",

            "de",
            "de_declining",
            "icr",

            "pe",
            "pb",

            "dividend_yield",
            "dividend_payout_pct",

            "market_cap",
            "net_profit",
            "sales",

            "asset_turnover",

            "composite_quality_score",
        ]

        columns = [
            c
            for c in preferred_columns
            if c in df.columns
        ]

        result = df[
            columns
        ].copy()

        if (
            "composite_quality_score"
            in result.columns
        ):

            result = (
                result
                .sort_values(
                    "composite_quality_score",
                    ascending=False
                )
            )

        return result.reset_index(
            drop=True
        )


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "SPRINT 3 — DAY 15/16/17"
    )
    print(
        "SCREENER ENGINE TEST"
    )
    print("=" * 70)

    try:

        # ====================================================
        # INITIALIZE
        # ====================================================

        engine = ScreenerEngine()

        # ====================================================
        # LOAD DATA
        # ====================================================

        df = engine.load_data()

        print()
        print(
            "Data loaded successfully!"
        )

        print(
            "Rows:",
            len(df)
        )

        print(
            "Columns:",
            len(df.columns)
        )

        # ====================================================
        # SHOW IMPORTANT COLUMNS
        # ====================================================

        print()
        print(
            "Important calculated columns:"
        )

        important_columns = [

            "revenue_cagr_3y",
            "revenue_cagr_5y",
            "pat_cagr_5y",
            "eps_cagr_5y",
            "fcf_cagr_5y",
            "de_declining",
            "cfo_pat_ratio",
            "fcf_positive",
        ]

        for column in important_columns:

            if column in df.columns:

                print(
                    f"  ✓ {column}"
                )

            else:

                print(
                    f"  ✗ {column}"
                )

        # ====================================================
        # SHOW FIRST 5
        # ====================================================

        print()
        print(
            "First 5 companies:"
        )

        display_columns = [

            "company_id",
            "company_name",
            "roe",
            "de",
            "fcf",
            "fcf_cagr_5y",
            "revenue_cagr_5y",
        ]

        display_columns = [
            c
            for c in display_columns
            if c in df.columns
        ]

        print(
            df[
                display_columns
            ]
            .head(5)
            .to_string(
                index=False
            )
        )

        # ====================================================
        # DAY 15 TEST
        # ====================================================

        print()
        print("-" * 70)
        print(
            "DAY 15 — QUALITY COMPOUNDER"
        )
        print("-" * 70)

        quality = (
            engine
            .quality_compounder()
        )

        print(
            "Companies returned:",
            len(quality)
        )

        if not quality.empty:

            print()

            print(
                engine
                .prepare_export(
                    quality
                )
                .head(10)
                .to_string(
                    index=False
                )
            )

        # ====================================================
        # DAY 16 — SIX PRESETS
        # ====================================================

        print()
        print("-" * 70)
        print(
            "DAY 16 — SIX PRESET SCREENERS"
        )
        print("-" * 70)

        all_presets = (
            engine
            .run_all_presets()
        )

        for name, result in (
            all_presets.items()
        ):

            print(
                f"{name:<28}"
                f": {len(result):>3} companies"
            )

        # ====================================================
        # DAY 17 — SECTOR RELATIVE
        # ====================================================

        print()
        print("-" * 70)
        print(
            "DAY 17 — SECTOR RELATIVE SCORE"
        )
        print("-" * 70)

        if not quality.empty:

            quality = quality.copy()

            quality[
                "sector_relative_score"
            ] = (
                engine
                .calculate_sector_relative_score(
                    quality
                )
            )

            print(
                quality[
                    [
                        "company_id",
                        "company_name",
                        "composite_quality_score",
                        "sector_relative_score",
                    ]
                ]
                .head(10)
                .to_string(
                    index=False
                )
            )

        # ====================================================
        # FINAL
        # ====================================================

        print()
        print("=" * 70)
        print(
            "SCREENER ENGINE TEST COMPLETED"
        )
        print("=" * 70)

        print()
        print(
            "Next file can use:"
        )

        print(
            "  engine.run_all_presets()"
        )

        print(
            "  engine.prepare_export(df)"
        )

        print()
        print(
            "Day 15/16 engine functionality is ready."
        )

    except Exception as e:

        print()
        print("=" * 70)
        print(
            "ERROR"
        )
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            e
        )

        import traceback

        traceback.print_exc()

# ============================================================
# DAY 17 — EXPORT ALL PRESETS TO EXCEL
# ============================================================

print()
print("=" * 70)
print("GENERATING screener_output.xlsx")
print("=" * 70)

from pathlib import Path

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCREENER_OUTPUT = OUTPUT_DIR / "screener_output.xlsx"

# ------------------------------------------------------------
# Run all six presets
# ------------------------------------------------------------

preset_results = engine.run_all_presets()

print()

print("Preset results:")

for preset_name, result_df in preset_results.items():

    print(
        f"  {preset_name:<30}: "
        f"{len(result_df):>3} companies"
    )

# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

with pd.ExcelWriter(
    SCREENER_OUTPUT,
    engine="openpyxl"
) as writer:

    for preset_name, result_df in preset_results.items():

        if result_df is None:
            continue

        export_df = result_df.copy()

        # Excel sheet names have a maximum of 31 characters
        sheet_name = str(preset_name)[:31]

        export_df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )

print()

print(
    f"✓ screener_output.xlsx created:"
)

print(
    f"  {SCREENER_OUTPUT}"
)

print()

print(
    "Sheets generated:"
)

for preset_name in preset_results.keys():

    print(
        f"  ✓ {preset_name}"
    )