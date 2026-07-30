import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.cashflow_kpis import *


def test_fcf():
    assert free_cash_flow(500, -100) == 400


def test_fcf_negative():
    assert free_cash_flow(100, -500) == -400


def test_quality():
    score, label = cfo_quality_score(200, 100)
    assert label == "High Quality"


def test_capex():
    value, label = capex_intensity(-100, 1000)
    assert label == "Capital Intensive"


def test_conversion():
    assert fcf_conversion_rate(200, 100) == 200.0


def test_pattern():
    pattern = capital_allocation_pattern(
        500,
        -200,
        -100,
        1.5
    )

    assert pattern["pattern_label"] == "Shareholder Returns"