import streamlit as st

from Script.dashboard.utils.db import (
    get_companies,
)


st.title("🏢 Company Profile")

companies = get_companies()

if companies.empty:

    st.warning(
        "No company data is currently available."
    )

    st.stop()


# ------------------------------------------------------------
# Search
# ------------------------------------------------------------

search = st.text_input(
    "Search company or ticker",
    placeholder="Example: TCS or Tata Consultancy Services",
)


if search:

    search_upper = search.strip().upper()

    matches = companies.copy()

    name_match = (
        matches["company_name"]
        .astype(str)
        .str.upper()
        .str.contains(
            search_upper,
            na=False,
        )
        if "company_name" in matches.columns
        else False
    )

    ticker_match = False

    if "ticker" in matches.columns:

        ticker_match |= (
            matches["ticker"]
            .astype(str)
            .str.upper()
            .str.contains(
                search_upper,
                na=False,
            )
        )

    if "nse_ticker" in matches.columns:

        ticker_match |= (
            matches["nse_ticker"]
            .astype(str)
            .str.upper()
            .str.contains(
                search_upper,
                na=False,
            )
        )

    filtered = matches[
        name_match | ticker_match
    ]

else:

    filtered = companies


if filtered.empty:

    st.error(
        "Ticker not found — please try another."
    )

    st.stop()


options = filtered.index.tolist()

selected_index = st.selectbox(
    "Select company",
    options,
    format_func=lambda idx: (
        f"{filtered.loc[idx, 'company_name']} "
        f"({filtered.loc[idx, 'ticker']})"
        if "ticker" in filtered.columns
        else str(filtered.loc[idx, "company_name"])
    ),
)

company = filtered.loc[selected_index]

st.divider()

st.subheader(
    company.get(
        "company_name",
        "Company",
    )
)

st.info(
    "Full company profile will be implemented on Day 23."
)