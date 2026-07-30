import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import *


def test_net_profit_margin():
    assert net_profit_margin(100, 1000) == 10.0


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


def test_operating_profit_margin():
    assert operating_profit_margin(150, 1000) == 15.0


def test_opm_crosscheck():
    calc = operating_profit_margin(150, 1000)

    assert check_opm(calc, 12) is True


def test_roe():
    assert return_on_equity(
        200,
        100,
        900
    ) == 20.0


def test_negative_equity():
    assert return_on_equity(
        100,
        -100,
        -50
    ) is None


def test_roce():
    assert return_on_capital_employed(
        150,
        20,
        100,
        900,
        200
    ) == 14.17


def test_roa():
    assert return_on_assets(
        100,
        1000
    ) == 10.0