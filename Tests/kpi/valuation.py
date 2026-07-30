def eps(net_income,shares):
    return round(net_income/shares,2)


def pe_ratio(price,eps_value):
    return round(price/eps_value,2)


def book_value(total_equity,shares):
    return round(total_equity/shares,2)


def pb_ratio(price,bvps):
    return round(price/bvps,2)

print(eps(200000,10000))
print(pe_ratio(850,20))
print(book_value(500000,10000))
print(pb_ratio(850,50))

