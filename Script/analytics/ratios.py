import math


def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)

    Formula:
        (Net Profit / Sales) * 100

    Returns:
        None if sales <= 0
    """

    if sales is None or sales <= 0:
        return None

    return round((net_profit / sales) * 100, 2)


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)
    """

    if sales is None or sales <= 0:
        return None

    return round((operating_profit / sales) * 100, 2)


def check_opm(calculated_opm, source_opm):
    """
    Returns True if mismatch >1%
    """

    if calculated_opm is None or source_opm is None:
        return False

    return abs(calculated_opm - source_opm) > 1


def return_on_equity(net_profit,
                     equity_capital,
                     reserves):
    """
    ROE
    """

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round((net_profit / equity) * 100, 2)


def return_on_capital_employed(
        operating_profit,
        other_income,
        equity_capital,
        reserves,
        borrowings,
        broad_sector=None):
    """
    ROCE
    """

    capital = equity_capital + reserves + borrowings

    if capital <= 0:
        return None

    ebit = operating_profit + other_income

    roce = (ebit / capital) * 100

    # Bank / Financial carve-out
    if broad_sector == "Financials":
        return round(roce, 2)

    return round(roce, 2)


def return_on_assets(net_profit,
                     total_assets):
    """
    ROA
    """

    if total_assets is None or total_assets <= 0:
        return None

    return round((net_profit / total_assets) * 100, 2)



def debt_to_equity(borrowings, equity_capital, reserves):
    """
    Debt-to-Equity Ratio

    Formula:
        Borrowings / (Equity + Reserves)

    Rules:
    - If borrowings = 0 → return 0
    - If equity <= 0 → return None
    """

    equity = equity_capital + reserves

    if borrowings == 0:
        return 0

    if equity <= 0:
        return None

    return round(borrowings / equity, 2)


def high_leverage_flag(de_ratio, broad_sector):
    """
    High leverage if D/E > 5
    Ignore Financial sector
    """

    if de_ratio is None:
        return False

    if broad_sector == "Financials":
        return False

    return de_ratio > 5


def interest_coverage(
    operating_profit,
    other_income,
    interest
):
    """
    Interest Coverage Ratio

    Formula:
    (Operating Profit + Other Income) / Interest
    """

    if interest == 0:
        return None

    ebit = operating_profit + other_income

    return round(ebit / interest, 2)



def icr_label(icr):
    """
    Debt-free companies
    """

    if icr is None:
        return "Debt Free"

    return ""


def icr_warning(icr):
    """
    Warn if ICR <1.5
    """

    if icr is None:
        return False

    return icr < 1.5


def net_debt(
    borrowings,
    investments
):
    """
    Net Debt

    Borrowings - Investments
    """

    return borrowings - investments


def asset_turnover(
    sales,
    total_assets
):

    if total_assets <= 0:
        return None

    return round(sales / total_assets, 2)


