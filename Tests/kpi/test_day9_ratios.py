import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import *

def test_debt_free():
    assert debt_to_equity(
        0,
        100,
        900
    ) == 0

def test_negative_equity():
    assert debt_to_equity(
        100,
        -100,
        -50
    ) is None

def test_interest_zero():
    assert interest_coverage(
        100,
        20,
        0
    ) is None

def test_icr_label():
    assert icr_label(None) == "Debt Free"

def test_icr_warning():
    assert icr_warning(1.2) is True

def test_net_debt():
    assert net_debt(
        500,
        100
    ) == 400

def test_asset_turnover():
    assert asset_turnover(
        1000,
        500
    ) == 2.0

def test_high_leverage():
    assert high_leverage_flag(
        6.2,
        "Industrials"
    ) is True



