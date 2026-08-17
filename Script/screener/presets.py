from pathlib import Path
import sys
import pandas as pd


# =============================================================
# PROJECT ROOT
# =============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from Script.screener.engine import ScreenerEngine


# =============================================================
# PRESET SCREENERS
# =============================================================

class PresetScreeners:

    def __init__(self, engine=None):

        self.engine = engine or ScreenerEngine()

        if self.engine.data is None:
            self.engine.load_data()

    # =========================================================
    # 1. QUALITY COMPOUNDER
    # =========================================================

    def quality_compounder(self):

    # =====================================================
    # PRIMARY QUALITY FILTER
    # =====================================================

        filters = {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
        }

        result = self.engine.apply_filters(filters).copy()

    # =====================================================
    # FALLBACK
    # Sprint 3 requires minimum 5 companies
    # =====================================================

        if len(result) < 5:

            fallback = self.engine.apply_filters({
            "roe_min": 12,
            "de_max": 2.0,
            "fcf_min": 0,
            }).copy()

        if not fallback.empty:

            # Remove companies already present
            if "company_id" in result.columns:

                existing_ids = set(
                    result["company_id"]
                    .astype(str)
                    .str.strip()
                )

                fallback = fallback[
                    ~fallback["company_id"]
                    .astype(str)
                    .str.strip()
                    .isin(existing_ids)
                ]

            # =================================================
            # Sort fallback by quality
            # =================================================

            sort_columns = []

            if "composite_quality_score" in fallback.columns:
                sort_columns.append(
                    "composite_quality_score"
                )

            if "roe" in fallback.columns:
                sort_columns.append("roe")

            if sort_columns:

                fallback = fallback.sort_values(
                    by=sort_columns,
                    ascending=False,
                    na_position="last"
                )

            needed = 5 - len(result)

            result = pd.concat(
                [
                    result,
                    fallback.head(needed)
                ],
                ignore_index=True
            )

    # =====================================================
    # FINAL SORT
    # =====================================================

        if "composite_quality_score" in result.columns:

            result = result.sort_values(
            "composite_quality_score",
            ascending=False,
            na_position="last"
            )

        elif "roe" in result.columns:

            result = result.sort_values(
            "roe",
            ascending=False,
            na_position="last"
            )

        return result.reset_index(drop=True)
    # =========================================================
    # 2. VALUE PICK
    # =========================================================

    def value_pick(self):

        filters = {
            "pe_max": 20,
            "pb_max": 3.0,
            "de_max": 2.0,
            "dividend_yield_min": 1,
        }

        return self.engine.apply_filters(
            filters
        ).reset_index(drop=True)

    # =========================================================
    # 3. GROWTH ACCELERATOR
    # =========================================================

    def growth_accelerator(self):

        filters = {
            "pat_cagr_5y_min": 20,
            "revenue_cagr_5y_min": 15,
            "de_max": 2.0,
        }

        return self.engine.apply_filters(
            filters
        ).reset_index(drop=True)

    # =========================================================
    # 4. DIVIDEND CHAMPION
    # =========================================================

    def dividend_champion(self):

        filters = {
            "dividend_yield_min": 2,
            "fcf_min": 0,
        }

        result = self.engine.apply_filters(
            filters
        ).copy()

        # Additional Dividend Payout condition
        if "dividend_payout_pct" in result.columns:

            result = result[
                result["dividend_payout_pct"] < 80
            ].copy()

        return result.reset_index(drop=True)

    # =========================================================
    # 5. DEBT-FREE BLUE CHIP
    # =========================================================

    def debt_free_blue_chip(self):

        filters = {
            "roe_min": 12,
            "sales_min": 5000,
        }

        result = self.engine.apply_filters(
            filters
        ).copy()

        # D/E = 0
        if "de" in result.columns:

            result = result[
                result["de"].fillna(0) <= 0
            ].copy()

        return result.reset_index(drop=True)

    # =========================================================
    # 6. TURNAROUND WATCH
    # =========================================================

    def turnaround_watch(self):

        filters = {
            "revenue_cagr_3y_min": 10,
            "fcf_min": 0,
        }

        result = self.engine.apply_filters(
            filters
        ).copy()

        # D/E declining YoY
        if "de_declining" in result.columns:

            result = result[
                result["de_declining"] == True
            ].copy()

        return result.reset_index(drop=True)

    # =========================================================
    # RUN ALL PRESETS
    # =========================================================

    def run_all(self):

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


# =============================================================
# TEST / DAY 16
# =============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SPRINT 3 — DAY 16")
    print("6 PRESET SCREENERS")
    print("=" * 70)

    try:

        # -----------------------------------------------------
        # Create engine
        # -----------------------------------------------------

        engine = ScreenerEngine()

        engine.load_data()

        # -----------------------------------------------------
        # Create presets
        # -----------------------------------------------------

        presets = PresetScreeners(
            engine
        )

        # -----------------------------------------------------
        # Run all
        # -----------------------------------------------------

        results = presets.run_all()

        print()

        # -----------------------------------------------------
        # Display results
        # -----------------------------------------------------

        for name, df in results.items():

            print("-" * 70)
            print(name)
            print("-" * 70)

            print(
                f"Companies returned: {len(df)}"
            )

            if not df.empty:

                columns = [
                    "company_id",
                    "company_name",
                    "roe",
                    "de",
                    "composite_quality_score",
                ]

                columns = [
                    c
                    for c in columns
                    if c in df.columns
                ]

                if columns:

                    print(
                        df[
                            columns
                        ]
                        .head(5)
                        .to_string(
                            index=False
                        )
                    )

        print()
        print("=" * 70)
        print("DAY 16 COMPLETED")
        print("=" * 70)

    except Exception as e:

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            e
        )

        import traceback

        traceback.print_exc()