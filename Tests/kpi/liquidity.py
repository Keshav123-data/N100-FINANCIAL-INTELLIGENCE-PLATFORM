import pandas as pd

def current_ratio(current_assets, current_liabilities):
    return round(current_assets / current_liabilities, 2)


def quick_ratio(current_assets, inventory, current_liabilities):
    return round((current_assets - inventory) / current_liabilities, 2)


def cash_ratio(cash, current_liabilities):
    return round(cash / current_liabilities, 2)

print(current_ratio(500000, 250000))
print(quick_ratio(500000, 100000, 250000))
print(cash_ratio(150000,250000))

