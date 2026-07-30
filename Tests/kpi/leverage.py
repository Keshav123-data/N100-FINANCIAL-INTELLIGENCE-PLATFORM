def debt_to_equity(total_debt, total_equity):
    return round(total_debt / total_equity,2)


def debt_ratio(total_debt,total_assets):
    return round(total_debt/total_assets,2)


def equity_ratio(total_equity,total_assets):
    return round(total_equity/total_assets,2)

print(debt_to_equity(300000,500000))
print(debt_ratio(300000,900000))
print(equity_ratio(500000,900000))

