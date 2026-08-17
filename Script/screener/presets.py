from pathlib import Path
import sys

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.screener.engine import ScreenerEngine


class PresetScreeners:

    def __init__(self, engine=None):
        self.engine = engine or ScreenerEngine()

        if self.engine.data is None:
            self.engine.load_data()

    # =========================================================
    # 1. QUALITY COMPOUNDER
    # =========================================================

    def quality_compounder(self):

        filters = {
            "roe_min": 15,
            "de_max": 1.0,
            "fcf_min": 0,
            "revenue_cagr_5y_min": 10,
        }

        return self.engine.apply_filters(filters)

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

        return self.engine.apply_filters(filters)

    # =========================================================
    # 3. GROWTH ACCELERATOR
    # =========================================================

    def growth_accelerator(self):

        filters = {
            "pat_cagr_5y_min": 20,
            "revenue_cagr_5y_min": 15,
            "de_max": 2.0,
        }

        return self.engine.apply_filters(filters)

    # =========================================================
    # 4. DIVIDEND CHAMPION
    # =========================================================

    def dividend_champion(self):

        filters = {
            "dividend_yield_min": 2,
            "fcf_min": 0,
        }

        result = self.engine.apply_filters(filters)

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

        result = self.engine.apply_filters(filters)

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

        result = self.engine.apply_filters(filters)

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
# TEST
# =============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("SPRINT 3 — DAY 16")
    print("6 PRESET SCREENERS")
    print("=" * 70)

    try:

        engine = ScreenerEngine()
        engine.load_data()

        presets = PresetScreeners(engine)

        results = presets.run_all()

        print()

        for name, df in results.items():

            print("-" * 70)
            print(f"{name}")
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
                    c for c in columns
                    if c in df.columns
                ]

                print(
                    df[columns]
                    .head(5)
                    .to_string(index=False)
                )

        print()
        print("=" * 70)
        print("DAY 16 COMPLETED")
        print("=" * 70)

    except Exception as e:

        print()
        print("ERROR:")
        print(type(e).__name__, ":", e)

        import traceback
        traceback.print_exc()