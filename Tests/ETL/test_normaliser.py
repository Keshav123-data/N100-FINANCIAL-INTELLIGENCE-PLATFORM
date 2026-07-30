import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.ETL.normaliser import normalize_year, normalize_ticker


# -------------------------
# normalize_year Tests
# -------------------------

@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("Dec 2012", 2012),
        ("Mar 2018", 2018),
        ("2019", 2019),
        ("2020 ", 2020),
        (" FY2021 ", 2021),
        ("Dec-2022", 2022),
        ("Mar-2023", 2023),
        ("2024", 2024),
        ("2015", 2015),
        ("2016", 2016),
        ("2017", 2017),
        ("2018", 2018),
        ("2019", 2019),
        ("2020", 2020),
        ("2021", 2021),
        ("2022", 2022),
        ("2023", 2023),
        ("2024", 2024),
        ("Dec 2025", 2025),
        ("Mar 2026", 2026),
    ]
)
def test_normalize_year_valid(input_value, expected):
    assert normalize_year(input_value) == expected


# -------------------------
# normalize_ticker Tests
# -------------------------

@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("abb", "ABB"),
        ("ABB", "ABB"),
        (" tcs ", "TCS"),
        ("Reliance", "RELIANCE"),
        ("infy", "INFY"),
        ("hdfcbank", "HDFCBANK"),
        ("itc", "ITC"),
        ("sbin", "SBIN"),
        ("lt", "LT"),
        ("asianpaint", "ASIANPAINT"),
        ("nestleind", "NESTLEIND"),
        ("tatamotors", "TATAMOTORS"),
        ("ultracemco", "ULTRACEMCO"),
        ("adanient", "ADANIENT"),
        ("wipro", "WIPRO"),
    ]
)
def test_normalize_ticker_valid(input_value, expected):
    assert normalize_ticker(input_value) == expected