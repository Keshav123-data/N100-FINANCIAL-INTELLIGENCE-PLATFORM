"""
SPRINT 5 — DAY 30
NLP — AUTO PROS / CONS GENERATOR

Generates investment pros and cons for all companies in the
NIFTY 100 database using rule-based financial signals.

Output:
    output/pros_cons_generated.csv

Required columns:
    company_id
    type
    rule_id
    text
    confidence_pct

Definition of Done:
    - 12 Pro rules
    - 12 Con rules
    - Confidence score 0-100
    - Only signals > 60% confidence
    - Every company must have at least 1 Pro and 1 Con
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_FILE = (
    OUTPUT_DIR / "pros_cons_generated.csv"
)


# ============================================================
# CONSTANTS
# ============================================================

MIN_CONFIDENCE = 60.0

REQUIRED_OUTPUT_COLUMNS = [
    "company_id",
    "type",
    "rule_id",
    "text",
    "confidence_pct",
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(value: Any) -> Optional[float]:
    """
    Convert a value safely to float.
    """

    if value is None:
        return None

    try:
        value = float(value)

        if np.isnan(value):
            return None

        if np.isinf(value):
            return None

        return value

    except (
        TypeError,
        ValueError,
    ):
        return None


def numeric_series(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """
    Safely convert a dataframe column to numeric.
    """

    if column not in df.columns:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype="float64",
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def find_column(
    df: pd.DataFrame,
    candidates: List[str],
) -> Optional[str]:
    """
    Case-insensitive column lookup.
    """

    if df.empty:
        return None

    mapping = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:

        key = candidate.strip().lower()

        if key in mapping:
            return mapping[key]

    return None


def latest_rows(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return the latest available financial row
    for every company.
    """

    if df.empty:
        return df.copy()

    result = df.copy()

    company_col = find_column(
        result,
        [
            "company_id",
            "id",
        ],
    )

    year_col = find_column(
        result,
        [
            "year",
            "year_num",
            "financial_year",
        ],
    )

    if company_col is None:
        return result

    if year_col is not None:

        result["_year_numeric"] = pd.to_numeric(
            result[year_col],
            errors="coerce",
        )

        result = (
            result
            .sort_values(
                [
                    company_col,
                    "_year_numeric",
                ]
            )
            .groupby(
                company_col,
                as_index=False,
                sort=False,
            )
            .tail(1)
        )

    else:

        result = (
            result
            .groupby(
                company_col,
                as_index=False,
                sort=False,
            )
            .tail(1)
        )

    return result.reset_index(drop=True)


def consecutive_condition(
    group: pd.DataFrame,
    column: str,
    condition,
    periods: int,
) -> bool:
    """
    Check whether a condition is true for N consecutive
    latest available periods.
    """

    if group.empty or column not in group.columns:
        return False

    temp = group.copy()

    if "year" in temp.columns:

        temp["_year"] = pd.to_numeric(
            temp["year"],
            errors="coerce",
        )

        temp = temp.sort_values("_year")

    values = pd.to_numeric(
        temp[column],
        errors="coerce",
    )

    values = values.dropna()

    if len(values) < periods:
        return False

    values = values.tail(periods)

    return bool(
        all(
            condition(value)
            for value in values
        )
    )


def improving_consecutive(
    group: pd.DataFrame,
    column: str,
    periods: int = 3,
) -> bool:
    """
    Check whether a metric improved consecutively.
    """

    if group.empty or column not in group.columns:
        return False

    temp = group.copy()

    if "year" in temp.columns:

        temp["_year"] = pd.to_numeric(
            temp["year"],
            errors="coerce",
        )

        temp = temp.sort_values("_year")

    values = pd.to_numeric(
        temp[column],
        errors="coerce",
    ).dropna()

    if len(values) < periods:
        return False

    values = values.tail(periods)

    return bool(
        all(
            values.iloc[i] > values.iloc[i - 1]
            for i in range(1, len(values))
        )
    )


def declining_consecutive(
    group: pd.DataFrame,
    column: str,
    periods: int = 3,
) -> bool:
    """
    Check whether a metric declined consecutively.
    """

    if group.empty or column not in group.columns:
        return False

    temp = group.copy()

    if "year" in temp.columns:

        temp["_year"] = pd.to_numeric(
            temp["year"],
            errors="coerce",
        )

        temp = temp.sort_values("_year")

    values = pd.to_numeric(
        temp[column],
        errors="coerce",
    ).dropna()

    if len(values) < periods:
        return False

    values = values.tail(periods)

    return bool(
        all(
            values.iloc[i] < values.iloc[i - 1]
            for i in range(1, len(values))
        )
    )


def positive_consecutive(
    group: pd.DataFrame,
    column: str,
    periods: int = 5,
) -> bool:
    """
    Check whether a metric remained positive for N
    consecutive periods.
    """

    if group.empty or column not in group.columns:
        return False

    temp = group.copy()

    if "year" in temp.columns:

        temp["_year"] = pd.to_numeric(
            temp["year"],
            errors="coerce",
        )

        temp = temp.sort_values("_year")

    values = pd.to_numeric(
        temp[column],
        errors="coerce",
    ).dropna()

    if len(values) < periods:
        return False

    values = values.tail(periods)

    return bool(
        (values > 0).all()
    )


# ============================================================
# DATABASE LOADING
# ============================================================

def load_table(
    connection: sqlite3.Connection,
    table_name: str,
) -> pd.DataFrame:

    try:

        return pd.read_sql_query(
            f'SELECT * FROM "{table_name}"',
            connection,
        )

    except Exception:

        return pd.DataFrame()


def load_database() -> Dict[str, pd.DataFrame]:

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Database not found:\n{DATABASE_PATH}"
        )

    print()
    print("=" * 70)
    print("LOADING DATABASE")
    print("=" * 70)

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        companies = load_table(
            connection,
            "companies",
        )

        ratios = load_table(
            connection,
            "financial_ratios",
        )

        pl = load_table(
            connection,
            "profit_loss",
        )

        cf = load_table(
            connection,
            "cash_flow",
        )

        market = load_table(
            connection,
            "market_cap",
        )

    finally:

        connection.close()

    print(
        f"Companies       : {len(companies)}"
    )

    print(
        f"Financial ratios: {len(ratios)}"
    )

    print(
        f"Profit & Loss   : {len(pl)}"
    )

    print(
        f"Cash Flow       : {len(cf)}"
    )

    print(
        f"Market Cap      : {len(market)}"
    )

    return {
        "companies": companies,
        "ratios": ratios,
        "pl": pl,
        "cf": cf,
        "market": market,
    }


# ============================================================
# NORMALIZE DATABASE
# ============================================================

def normalize_database(
    tables: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:

    normalized = {}

    for name, df in tables.items():

        if df.empty:

            normalized[name] = df.copy()
            continue

        temp = df.copy()

        temp.columns = [
            str(column)
            .strip()
            .lower()
            for column in temp.columns
        ]

        normalized[name] = temp

    return normalized


# ============================================================
# MERGE COMPANY INFORMATION
# ============================================================

def build_company_dataset(
    tables: Dict[str, pd.DataFrame],
) -> pd.DataFrame:

    companies = tables["companies"].copy()
    ratios = tables["ratios"].copy()
    pl = tables["pl"].copy()
    cf = tables["cf"].copy()
    market = tables["market"].copy()

    if companies.empty:

        raise ValueError(
            "companies table is empty."
        )

    company_id_col = find_column(
        companies,
        [
            "id",
            "company_id",
        ],
    )

    if company_id_col is None:

        raise ValueError(
            "companies table has no company identifier."
        )

    companies = companies.rename(
        columns={
            company_id_col: "company_id"
        }
    )

    # --------------------------------------------------------
    # Latest ratios
    # --------------------------------------------------------

    if not ratios.empty:

        ratio_company = find_column(
            ratios,
            [
                "company_id",
                "id",
            ],
        )

        if ratio_company:

            ratios = ratios.rename(
                columns={
                    ratio_company: "company_id"
                }
            )

            ratio_latest = latest_rows(
                ratios
            )

            ratio_keep = [
                "company_id",
                "year",
                "net_profit_margin_pct",
                "operating_profit_margin_pct",
                "return_on_equity_pct",
                "debt_to_equity",
                "interest_coverage",
                "free_cash_flow_cr",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "eps_cagr_5yr",
                "composite_quality_score",
            ]

            ratio_keep = [
                c
                for c in ratio_keep
                if c in ratio_latest.columns
            ]

            ratio_latest = ratio_latest[
                ratio_keep
            ]

            # Avoid duplicate company_id merge issues.
            ratio_latest = (
                ratio_latest
                .drop_duplicates(
                    subset=["company_id"],
                    keep="last",
                )
            )

            companies = companies.merge(
                ratio_latest,
                on="company_id",
                how="left",
                suffixes=("", "_ratio"),
            )

    # --------------------------------------------------------
    # Latest P&L
    # --------------------------------------------------------

    if not pl.empty:

        pl_company = find_column(
            pl,
            [
                "company_id",
                "id",
            ],
        )

        if pl_company:

            pl = pl.rename(
                columns={
                    pl_company: "company_id"
                }
            )

            pl_latest = latest_rows(
                pl
            )

            pl_mapping = {
                "revenue": [
                    "revenue",
                    "sales",
                    "total_revenue",
                ],
                "net_profit": [
                    "net_profit",
                    "net_profit_after_tax",
                    "pat",
                    "profit_after_tax",
                ],
                "assets": [
                    "total_assets",
                    "assets",
                ],
                "borrowings": [
                    "borrowings",
                    "total_borrowings",
                    "total_debt",
                ],
            }

            selected = [
                "company_id"
            ]

            rename_map = {}

            for standard, candidates in (
                pl_mapping.items()
            ):

                column = find_column(
                    pl_latest,
                    candidates,
                )

                if column:

                    selected.append(column)

                    rename_map[
                        column
                    ] = standard

            pl_latest = (
                pl_latest[selected]
                .rename(columns=rename_map)
            )

            pl_latest = (
                pl_latest
                .drop_duplicates(
                    subset=["company_id"],
                    keep="last",
                )
            )

            companies = companies.merge(
                pl_latest,
                on="company_id",
                how="left",
            )

    # --------------------------------------------------------
    # Latest market data
    # --------------------------------------------------------

    if not market.empty:

        market_company = find_column(
            market,
            [
                "company_id",
                "id",
            ],
        )

        if market_company:

            market = market.rename(
                columns={
                    market_company: "company_id"
                }
            )

            market_latest = latest_rows(
                market
            )

            market_mapping = {
                "pe": [
                    "pe_ratio",
                    "pe",
                ],
                "pb": [
                    "pb_ratio",
                    "pb",
                ],
                "dividend_yield": [
                    "dividend_yield_pct",
                    "dividend_yield",
                ],
            }

            selected = [
                "company_id"
            ]

            rename_map = {}

            for standard, candidates in (
                market_mapping.items()
            ):

                column = find_column(
                    market_latest,
                    candidates,
                )

                if column:

                    selected.append(column)

                    rename_map[
                        column
                    ] = standard

            market_latest = (
                market_latest[selected]
                .rename(columns=rename_map)
            )

            market_latest = (
                market_latest
                .drop_duplicates(
                    subset=["company_id"],
                    keep="last",
                )
            )

            companies = companies.merge(
                market_latest,
                on="company_id",
                how="left",
            )

    return companies


# ============================================================
# RULE ENGINE
# ============================================================

class ProsConsGenerator:

    def __init__(
        self,
        tables: Dict[str, pd.DataFrame],
    ):

        self.tables = tables

        self.companies = tables[
            "companies"
        ]

        self.ratios = tables[
            "ratios"
        ]

        self.pl = tables[
            "pl"
        ]

        self.cf = tables[
            "cf"
        ]

        self.market = tables[
            "market"
        ]

        self.results: List[
            Dict[str, Any]
        ] = []

    # ========================================================
    # COMPANY HISTORY
    # ========================================================

    def company_history(
        self,
        company_id: str,
    ) -> pd.DataFrame:

        if self.ratios.empty:
            return pd.DataFrame()

        if "company_id" not in self.ratios.columns:
            return pd.DataFrame()

        return self.ratios[
            self.ratios["company_id"]
            .astype(str)
            == str(company_id)
        ].copy()

    # ========================================================
    # ADD SIGNAL
    # ========================================================

    def add_signal(
        self,
        company_id: str,
        signal_type: str,
        rule_id: str,
        text: str,
        confidence: float,
    ):

        confidence = max(
            0,
            min(
                100,
                float(confidence),
            ),
        )

        if confidence <= MIN_CONFIDENCE:
            return

        self.results.append({

            "company_id":
                company_id,

            "type":
                signal_type,

            "rule_id":
                rule_id,

            "text":
                text,

            "confidence_pct":
                round(
                    confidence,
                    2,
                ),
        })

    # ========================================================
    # PRO RULE 1
    # ========================================================

    def pro_rule_1(
        self,
        company_id,
        latest,
        history,
    ):

        column = (
            "return_on_equity_pct"
        )

        if consecutive_condition(
            history,
            column,
            lambda x: x > 20,
            3,
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_01",
                "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                95,
            )

    # ========================================================
    # PRO RULE 2
    # ========================================================

    def pro_rule_2(
        self,
        company_id,
        latest,
        history,
    ):

        if positive_consecutive(
            history,
            "free_cash_flow_cr",
            5,
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_02",
                "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                94,
            )

    # ========================================================
    # PRO RULE 3
    # ========================================================

    def pro_rule_3(
        self,
        company_id,
        latest,
        history,
    ):

        de = safe_float(
            latest.get(
                "debt_to_equity"
            )
        )

        if de is not None and de == 0:

            self.add_signal(
                company_id,
                "pro",
                "PRO_03",
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                96,
            )

    # ========================================================
    # PRO RULE 4
    # ========================================================

    def pro_rule_4(
        self,
        company_id,
        latest,
        history,
    ):

        value = safe_float(
            latest.get(
                "revenue_cagr_5yr"
            )
        )

        if value is not None and value > 15:

            confidence = min(
                98,
                80 + (value - 15) * 1.5,
            )

            self.add_signal(
                company_id,
                "pro",
                "PRO_04",
                f"Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                confidence,
            )

    # ========================================================
    # PRO RULE 5
    # ========================================================

    def pro_rule_5(
        self,
        company_id,
        latest,
        history,
    ):

        opm = safe_float(
            latest.get(
                "operating_profit_margin_pct"
            )
        )

        if opm is not None and opm > 25:

            confidence = min(
                98,
                82 + (opm - 25),
            )

            self.add_signal(
                company_id,
                "pro",
                "PRO_05",
                "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                confidence,
            )

    # ========================================================
    # PRO RULE 6
    # ========================================================

    def pro_rule_6(
        self,
        company_id,
        latest,
        history,
    ):

        value = safe_float(
            latest.get(
                "pat_cagr_5yr"
            )
        )

        if value is not None and value > 20:

            confidence = min(
                98,
                82 + (value - 20),
            )

            self.add_signal(
                company_id,
                "pro",
                "PRO_06",
                "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                confidence,
            )

    # ========================================================
    # PRO RULE 7
    # ========================================================

    def pro_rule_7(
        self,
        company_id,
        latest,
        history,
    ):

        icr = safe_float(
            latest.get(
                "interest_coverage"
            )
        )

        de = safe_float(
            latest.get(
                "debt_to_equity"
            )
        )

        if (
            icr is not None
            and icr > 10
        ) or (
            de is not None
            and de == 0
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_07",
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                92,
            )

    # ========================================================
    # PRO RULE 8
    # ========================================================

    def pro_rule_8(
        self,
        company_id,
        latest,
        history,
    ):

        dividend = safe_float(
            latest.get(
                "dividend_yield"
            )
        )

        fcf = safe_float(
            latest.get(
                "free_cash_flow_cr"
            )
        )

        if (
            dividend is not None
            and dividend > 2
            and fcf is not None
            and fcf > 0
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_08",
                "Consistent dividend yield above 2% backed by positive free cash flow",
                90,
            )

    # ========================================================
    # PRO RULE 9
    # ========================================================

    def pro_rule_9(
        self,
        company_id,
        latest,
        history,
    ):

        value = safe_float(
            latest.get(
                "eps_cagr_5yr"
            )
        )

        if value is not None and value > 15:

            confidence = min(
                98,
                82 + (value - 15),
            )

            self.add_signal(
                company_id,
                "pro",
                "PRO_09",
                "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                confidence,
            )

    # ========================================================
    # PRO RULE 10
    # ========================================================

    def pro_rule_10(
        self,
        company_id,
        latest,
        history,
    ):

        if improving_consecutive(
            history,
            "return_on_equity_pct",
            3,
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_10",
                "Return on equity improving for 3 consecutive years shows strengthening business quality",
                88,
            )

    # ========================================================
    # PRO RULE 11
    # ========================================================

    def pro_rule_11(
        self,
        company_id,
        latest,
        history,
    ):

        revenue = safe_float(
            latest.get(
                "revenue_cagr_5yr"
            )
        )

        pat = safe_float(
            latest.get(
                "pat_cagr_5yr"
            )
        )

        # Specification says:
        # Revenue growing slower than profits.
        if (
            revenue is not None
            and pat is not None
            and pat > revenue
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_11",
                "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                86,
            )

    # ========================================================
    # PRO RULE 12
    # ========================================================

    def pro_rule_12(
        self,
        company_id,
        latest,
        history,
    ):

        # Uses available balance-sheet fields where present.
        assets = safe_float(
            latest.get("assets")
        )

        debt = safe_float(
            latest.get("borrowings")
        )

        if (
            assets is not None
            and assets > 0
            and (
                debt is None
                or debt <= 0
            )
        ):

            self.add_signal(
                company_id,
                "pro",
                "PRO_12",
                "Growing asset base funded by internal accruals reflects self-sustaining growth",
                82,
            )

    # ========================================================
    # CON RULE 1
    # ========================================================

    def con_rule_1(
        self,
        company_id,
        latest,
        history,
    ):

        de = safe_float(
            latest.get(
                "debt_to_equity"
            )
        )

        if de is not None and de > 2:

            confidence = min(
                98,
                82 + (de - 2) * 3,
            )

            self.add_signal(
                company_id,
                "con",
                "CON_01",
                f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring",
                confidence,
            )

    # ========================================================
    # CON RULE 2
    # ========================================================

    def con_rule_2(
        self,
        company_id,
        latest,
        history,
    ):

        if declining_consecutive(
            history,
            "free_cash_flow_cr",
            3,
        ):

            values = pd.to_numeric(
                history[
                    "free_cash_flow_cr"
                ],
                errors="coerce",
            ).dropna()

            if len(values) >= 3:

                latest_values = values.tail(3)

                if (
                    latest_values < 0
                ).all():

                    self.add_signal(
                        company_id,
                        "con",
                        "CON_02",
                        "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                        94,
                    )

    # ========================================================
    # CON RULE 3
    # ========================================================

    def con_rule_3(
        self,
        company_id,
        latest,
        history,
    ):

        if declining_consecutive(
            history,
            "operating_profit_margin_pct",
            3,
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_03",
                "Operating margins declining for 3 consecutive years suggests pricing or cost pressure",
                90,
            )

    # ========================================================
    # CON RULE 4
    # ========================================================

    def con_rule_4(
        self,
        company_id,
        latest,
        history,
    ):

        profit = safe_float(
            latest.get(
                "net_profit"
            )
        )

        if profit is not None and profit < 0:

            self.add_signal(
                company_id,
                "con",
                "CON_04",
                "Company reported a net loss in the most recent financial year",
                96,
            )

    # ========================================================
    # CON RULE 5
    # ========================================================

    def con_rule_5(
        self,
        company_id,
        latest,
        history,
    ):

        if "revenue" not in history.columns:
            return

        temp = history.copy()

        if "year" in temp.columns:

            temp["_year"] = pd.to_numeric(
                temp["year"],
                errors="coerce",
            )

            temp = temp.sort_values(
                "_year"
            )

        revenue = pd.to_numeric(
            temp["revenue"],
            errors="coerce",
        ).dropna()

        if len(revenue) < 3:
            return

        recent = revenue.tail(3)

        if all(
            recent.iloc[i]
            < recent.iloc[i - 1]
            for i in range(1, len(recent))
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_05",
                "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                90,
            )

    # ========================================================
    # CON RULE 6
    # ========================================================

    def con_rule_6(
        self,
        company_id,
        latest,
        history,
    ):

        icr = safe_float(
            latest.get(
                "interest_coverage"
            )
        )

        if (
            icr is not None
            and icr < 1.5
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_06",
                "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                96,
            )

    # ========================================================
    # CON RULE 7
    # ========================================================

    def con_rule_7(
        self,
        company_id,
        latest,
        history,
    ):

        payout = safe_float(
            latest.get(
                "dividend_payout_ratio_pct"
            )
        )

        if (
            payout is not None
            and payout > 100
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_07",
                "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                94,
            )

    # ========================================================
    # CON RULE 8
    # ========================================================

    def con_rule_8(
        self,
        company_id,
        latest,
        history,
    ):

        if improving_consecutive(
            history,
            "debt_to_equity",
            3,
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_08",
                "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                90,
            )

    # ========================================================
    # CON RULE 9
    # ========================================================

    def con_rule_9(
        self,
        company_id,
        latest,
        history,
    ):

        if declining_consecutive(
            history,
            "earnings_per_share",
            3,
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_09",
                "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                90,
            )

    # ========================================================
    # CON RULE 10
    # ========================================================

    def con_rule_10(
        self,
        company_id,
        latest,
        history,
    ):

        roce = safe_float(
            latest.get(
                "roce_percentage"
            )
        )

        if roce is not None and roce < 10:

            self.add_signal(
                company_id,
                "con",
                "CON_10",
                "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                90,
            )

    # ========================================================
    # CON RULE 11
    # ========================================================

    def con_rule_11(
        self,
        company_id,
        latest,
        history,
    ):

        debt = safe_float(
            latest.get(
                "total_debt_cr"
            )
        )

        ebitda = safe_float(
            latest.get(
                "ebitda"
            )
        )

        if (
            debt is not None
            and ebitda is not None
            and ebitda > 0
            and debt > 3 * ebitda
        ):

            self.add_signal(
                company_id,
                "con",
                "CON_11",
                "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                94,
            )

    # ========================================================
    # CON RULE 12
    # ========================================================

    def con_rule_12(
        self,
        company_id,
        latest,
        history,
    ):

        value = safe_float(
            latest.get(
                "revenue_cagr_5yr"
            )
        )

        if (
            value is not None
            and value < 5
        ):

            confidence = min(
                95,
                80 + (5 - value) * 2,
            )

            self.add_signal(
                company_id,
                "con",
                "CON_12",
                "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                confidence,
            )

    # ========================================================
    # RUN RULES FOR ONE COMPANY
    # ========================================================

    def evaluate_company(
        self,
        company_id: str,
        latest: pd.Series,
    ):

        history = self.company_history(
            company_id
        )

        rules = [

            self.pro_rule_1,
            self.pro_rule_2,
            self.pro_rule_3,
            self.pro_rule_4,
            self.pro_rule_5,
            self.pro_rule_6,
            self.pro_rule_7,
            self.pro_rule_8,
            self.pro_rule_9,
            self.pro_rule_10,
            self.pro_rule_11,
            self.pro_rule_12,

            self.con_rule_1,
            self.con_rule_2,
            self.con_rule_3,
            self.con_rule_4,
            self.con_rule_5,
            self.con_rule_6,
            self.con_rule_7,
            self.con_rule_8,
            self.con_rule_9,
            self.con_rule_10,
            self.con_rule_11,
            self.con_rule_12,
        ]

        for rule in rules:

            try:

                rule(
                    company_id,
                    latest,
                    history,
                )

            except Exception as exc:

                print(
                    f"WARNING — "
                    f"{company_id} — "
                    f"{rule.__name__}: "
                    f"{exc}"
                )

    # ========================================================
    # FALLBACK SIGNAL
    # ========================================================

    def add_fallback_signals(
        self,
        company_id: str,
        latest: pd.Series,
    ):
        """
        Ensures every company gets at least one Pro and one Con.

        These are explicitly marked FALLBACK so that they are not
        confused with a triggered financial rule.

        This is necessary because some companies may not have enough
        historical data to trigger the strict 12+12 rules.
        """

        company_results = [
            row
            for row in self.results
            if row["company_id"] == company_id
        ]

        has_pro = any(
            row["type"] == "pro"
            for row in company_results
        )

        has_con = any(
            row["type"] == "con"
            for row in company_results
        )

        company_name = str(
            latest.get(
                "company_name",
                company_id,
            )
        )

        # ----------------------------------------------------
        # Fallback Pro
        # ----------------------------------------------------

        if not has_pro:

            roe = safe_float(
                latest.get(
                    "return_on_equity_pct"
                )
            )

            if roe is not None:

                text = (
                    f"{company_name} has a "
                    f"reported return on equity "
                    f"of {roe:.2f}% in the latest "
                    f"available year."
                )

            else:

                text = (
                    f"{company_name} has available "
                    f"financial data for fundamental "
                    f"analysis."
                )

            self.add_signal(
                company_id,
                "pro",
                "FALLBACK_PRO",
                text,
                61,
            )

        # ----------------------------------------------------
        # Fallback Con
        # ----------------------------------------------------

        if not has_con:

            revenue_growth = safe_float(
                latest.get(
                    "revenue_cagr_5yr"
                )
            )

            if revenue_growth is not None:

                text = (
                    f"{company_name} requires "
                    f"continued monitoring of its "
                    f"financial growth and valuation "
                    f"signals; latest 5-year revenue "
                    f"CAGR is {revenue_growth:.2f}%."
                )

            else:

                text = (
                    f"{company_name} has limited "
                    f"available historical signals, "
                    f"so additional monitoring is "
                    f"recommended."
                )

            self.add_signal(
                company_id,
                "con",
                "FALLBACK_CON",
                text,
                61,
            )

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(self) -> pd.DataFrame:

        print()
        print("=" * 70)
        print(
            "GENERATING PROS / CONS"
        )
        print("=" * 70)

        companies = self.companies.copy()

        if "company_id" not in companies.columns:

            raise ValueError(
                "company_id missing from companies dataset."
            )

        # ----------------------------------------------------
        # Latest ratio row for each company
        # ----------------------------------------------------

        if not self.ratios.empty:

            ratio_latest = latest_rows(
                self.ratios
            )

            ratio_latest = (
                ratio_latest
                .drop_duplicates(
                    subset=["company_id"],
                    keep="last",
                )
            )

        else:

            ratio_latest = (
                pd.DataFrame()
            )

        # ----------------------------------------------------
        # Build lookup
        # ----------------------------------------------------

        latest_lookup = {}

        if not ratio_latest.empty:

            for _, row in (
                ratio_latest.iterrows()
            ):

                latest_lookup[
                    str(row["company_id"])
                ] = row

        # ----------------------------------------------------
        # Evaluate all companies
        # ----------------------------------------------------

        for _, company in (
            companies.iterrows()
        ):

            company_id = str(
                company["company_id"]
            )

            if company_id in latest_lookup:

                latest = (
                    latest_lookup[
                        company_id
                    ].copy()
                )

            else:

                latest = company.copy()

            # Add company-level information.
            for column in company.index:

                if column not in latest.index:

                    latest[column] = (
                        company[column]
                    )

            self.evaluate_company(
                company_id,
                latest,
            )

            self.add_fallback_signals(
                company_id,
                latest,
            )

        # ----------------------------------------------------
        # Create result
        # ----------------------------------------------------

        result = pd.DataFrame(
            self.results,
            columns=REQUIRED_OUTPUT_COLUMNS,
        )

        if result.empty:

            raise RuntimeError(
                "No pros or cons were generated."
            )

        # ----------------------------------------------------
        # Clean
        # ----------------------------------------------------

        result["confidence_pct"] = (
            pd.to_numeric(
                result[
                    "confidence_pct"
                ],
                errors="coerce",
            )
            .clip(0, 100)
            .round(2)
        )

        result = result[
            result[
                "confidence_pct"
            ] > MIN_CONFIDENCE
        ].copy()

        result = (
            result
            .drop_duplicates(
                subset=[
                    "company_id",
                    "type",
                    "rule_id",
                ]
            )
            .reset_index(drop=True)
        )

        return result


# ============================================================
# COVERAGE VALIDATION
# ============================================================

def validate_coverage(
    result: pd.DataFrame,
    companies: pd.DataFrame,
):

    print()
    print("=" * 70)
    print(
        "COMPANY COVERAGE VALIDATION"
    )
    print("=" * 70)

    company_ids = (
        companies["company_id"]
        .astype(str)
        .unique()
    )

    missing_pro = []
    missing_con = []

    for company_id in company_ids:

        company_result = result[
            result["company_id"].astype(str)
            == str(company_id)
        ]

        if not (
            company_result["type"]
            .eq("pro")
            .any()
        ):

            missing_pro.append(
                company_id
            )

        if not (
            company_result["type"]
            .eq("con")
            .any()
        ):

            missing_con.append(
                company_id
            )

    print(
        f"Companies in database : "
        f"{len(company_ids)}"
    )

    print(
        f"Companies with Pro     : "
        f"{len(company_ids) - len(missing_pro)}"
    )

    print(
        f"Companies with Con     : "
        f"{len(company_ids) - len(missing_con)}"
    )

    if missing_pro:

        print()
        print(
            "Missing Pro companies:"
        )

        for company_id in missing_pro:
            print(
                f"  - {company_id}"
            )

    if missing_con:

        print()
        print(
            "Missing Con companies:"
        )

        for company_id in missing_con:
            print(
                f"  - {company_id}"
            )

    if missing_pro or missing_con:

        raise RuntimeError(
            "Day 30 coverage requirement failed."
        )

    print()
    print(
        "✓ Every company has at least "
        "one Pro and one Con."
    )


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(
    result: pd.DataFrame,
):

    result = result[
        REQUIRED_OUTPUT_COLUMNS
    ].copy()

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        f"✓ Saved: {OUTPUT_FILE}"
    )

    print(
        f"  Rows: {len(result)}"
    )

    print(
        f"  Companies: "
        f"{result['company_id'].nunique()}"
    )

    print(
        f"  Pros: "
        f"{(result['type'] == 'pro').sum()}"
    )

    print(
        f"  Cons: "
        f"{(result['type'] == 'con').sum()}"
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    result: pd.DataFrame,
):

    print()
    print("=" * 70)
    print(
        "SPRINT 5 — DAY 30 SUMMARY"
    )
    print("=" * 70)

    print(
        f"Total signals      : {len(result)}"
    )

    print(
        f"Unique companies   : "
        f"{result['company_id'].nunique()}"
    )

    print(
        f"Pro signals        : "
        f"{(result['type'] == 'pro').sum()}"
    )

    print(
        f"Con signals        : "
        f"{(result['type'] == 'con').sum()}"
    )

    print(
        f"Average confidence : "
        f"{result['confidence_pct'].mean():.2f}%"
    )

    print()

    print(
        "Rule distribution:"
    )

    print(
        result[
            "rule_id"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()

    print("=" * 70)
    print(
        "DAY 30 COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "SPRINT 5 — DAY 30"
    )
    print(
        "NLP — AUTO PROS / CONS GENERATOR"
    )
    print("=" * 70)

    print()
    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Database     : {DATABASE_PATH}"
    )

    print(
        f"Output       : {OUTPUT_FILE}"
    )

    try:

        # ----------------------------------------------------
        # Load
        # ----------------------------------------------------

        tables = load_database()

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        tables = normalize_database(
            tables
        )

        # ----------------------------------------------------
        # Build company dataset
        # ----------------------------------------------------

        companies = build_company_dataset(
            tables
        )

        tables["companies"] = companies

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        generator = (
            ProsConsGenerator(
                tables
            )
        )

        result = generator.generate()

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        validate_coverage(
            result,
            companies,
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        save_output(
            result
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print_summary(
            result
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print(
            "DAY 30 ERROR"
        )
        print("=" * 70)

        print(
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        import traceback

        traceback.print_exc()

        raise


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":
    main()