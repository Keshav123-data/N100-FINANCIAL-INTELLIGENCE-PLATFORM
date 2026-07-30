def free_cash_flow(operating_activity, investing_activity):
    """
    FCF = CFO + CFI

    Investing activity is usually negative.
    Negative FCF is allowed.
    """

    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity

def cfo_quality_score(cfo, pat):
    """
    CFO / PAT
    """

    if pat is None or pat == 0:
        return None, "N/A"

    score = cfo / pat

    if score > 1:
        label = "High Quality"

    elif score >= 0.5:
        label = "Moderate"

    else:
        label = "Accrual Risk"

    return round(score, 2), label

def capex_intensity(investing_activity, sales):
    """
    abs(CFI) / Sales ×100
    """

    if sales is None or sales == 0:
        return None, "N/A"

    intensity = abs(investing_activity) / sales * 100

    if intensity < 3:
        label = "Asset Light"

    elif intensity <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return round(intensity, 2), label

def fcf_conversion_rate(fcf, operating_profit):
    """
    FCF / Operating Profit ×100
    """

    if operating_profit is None or operating_profit == 0:
        return None

    return round((fcf / operating_profit) * 100, 2)

def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    """
    8-pattern classifier
    """

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    signs = (cfo_sign, cfi_sign, cff_sign)

    if signs == ("+", "-", "-"):

        if cfo_pat_ratio and cfo_pat_ratio > 1:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"

    elif signs == ("+", "+", "-"):
        label = "Liquidating Assets"

    elif signs == ("-", "+", "+"):
        label = "Distress Signal"

    elif signs == ("-", "-", "+"):
        label = "Growth Funded by Debt"

    elif signs == ("+", "+", "+"):
        label = "Cash Accumulator"

    elif signs == ("-", "-", "-"):
        label = "Pre-Revenue"

    elif signs == ("+", "-", "+"):
        label = "Mixed"

    else:
        label = "Other"

    return {
        "cfo_sign": cfo_sign,
        "cfi_sign": cfi_sign,
        "cff_sign": cff_sign,
        "pattern_label": label
    }

