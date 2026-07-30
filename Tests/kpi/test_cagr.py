import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.cagr import *

def test_normal_cagr():

    value, flag = calculate_cagr(
        100,
        200,
        5
    )

    assert round(value,2) == 14.87

    assert flag == "OK"

def test_turnaround():

    value, flag = calculate_cagr(
        -100,
        200,
        5
    )

    assert value is None

    assert flag == "TURNAROUND"

def test_decline():

    value, flag = calculate_cagr(
        100,
        -50,
        5
    )

    assert value is None

    assert flag == "DECLINE_TO_LOSS"


def test_both_negative():

    value, flag = calculate_cagr(
        -100,
        -50,
        5
    )

    assert value is None

    assert flag == "BOTH_NEGATIVE"

def test_zero_base():

    value, flag = calculate_cagr(
        0,
        100,
        5
    )

    assert value is None

    assert flag == "ZERO_BASE"

def test_insufficient():

    value, flag = calculate_cagr(
        100,
        200,
        0
    )

    assert value is None

    assert flag == "INSUFFICIENT"


def test_revenue():
    value, flag = revenue_cagr(
        500,
        900,
        5
    )

    assert flag == "OK"


def test_pat():
    value, flag = pat_cagr(
        200,
        300,
        5
    )

    assert flag == "OK"


def test_eps():
    value, flag = eps_cagr(
        25,
        50,
        5
    )

    assert flag == "OK"


def test_missing_values():
    value, flag = calculate_cagr(
        None,
        100,
        5
    )

    assert value is None
    assert flag == "INSUFFICIENT"


