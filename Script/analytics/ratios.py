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