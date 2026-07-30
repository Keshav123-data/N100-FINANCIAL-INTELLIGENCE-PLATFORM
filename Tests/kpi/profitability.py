def gross_margin(gross_profit,revenue):
    return round((gross_profit/revenue)*100,2)


def operating_margin(operating_income,revenue):
    return round((operating_income/revenue)*100,2)


def net_margin(net_income,revenue):
    return round((net_income/revenue)*100,2)


def roa(net_income,total_assets):
    return round((net_income/total_assets)*100,2)


def roe(net_income,total_equity):
    return round((net_income/total_equity)*100,2)

print(gross_margin(400000,1000000))
print(operating_margin(220000,1000000))
print(net_margin(150000,1000000))
print(roa(150000,900000))
print(roe(150000,500000))

