def asset_turnover(revenue,total_assets):
    return round(revenue/total_assets,2)


def inventory_turnover(cogs,inventory):
    return round(cogs/inventory,2)


def receivable_turnover(revenue,receivables):
    return round(revenue/receivables,2)

print(asset_turnover(1000000,900000))
print(inventory_turnover(600000,120000))
print(receivable_turnover(1000000,100000))