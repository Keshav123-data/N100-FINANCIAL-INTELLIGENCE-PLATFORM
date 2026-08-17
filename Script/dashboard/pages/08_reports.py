import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from Script.dashboard.utils.db import (
    get_companies,
    get_pl,
)


# ============================================================
# PAGE
# ============================================================

st.title("📄 Annual Reports")

st.caption(
    "Company information, financial statements and "
    "official annual-report resources."
)


# ============================================================
# LOAD COMPANIES
# ============================================================

companies = get_companies()


if companies.empty:

    st.error(
        "Company database could not be loaded."
    )

    st.stop()


# ============================================================
# SIDEBAR SEARCH
# ============================================================

st.sidebar.header("Company Search")

search = st.sidebar.text_input(
    "Company name or company ID",
    placeholder="Example: Reliance",
)


# ============================================================
# FILTER COMPANIES
# ============================================================

if search:

    search_value = search.strip().lower()

    mask = pd.Series(
        False,
        index=companies.index,
    )

    for column in [
        "company_name",
        "company_id",
    ]:

        if column in companies.columns:

            mask |= (
                companies[column]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False,
                )
            )

    matches = companies[mask]

else:

    matches = companies.copy()


if matches.empty:

    st.warning(
        "No company found. Try another company name or ID."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

def company_label(index):

    row = matches.loc[index]

    name = row.get(
        "company_name",
        "Unknown Company",
    )

    company_id = row.get(
        "company_id",
        "",
    )

    return f"{name} ({company_id})"


selected_index = st.selectbox(
    "Select Company",
    matches.index.tolist(),
    format_func=company_label,
)


company = matches.loc[selected_index]


company_id = str(
    company.get(
        "company_id",
        "",
    )
)


company_name = str(
    company.get(
        "company_name",
        "Company",
    )
)


# ============================================================
# COMPANY HEADER
# ============================================================

st.divider()

st.header(company_name)

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Company ID",
        company_id,
    )


with c2:

    st.metric(
        "Sector",
        company.get(
            "sector",
            "N/A",
        ),
    )


with c3:

    st.metric(
        "Sub-Sector",
        company.get(
            "sub_sector",
            "N/A",
        ),
    )


with c4:

    st.metric(
        "Market Cap Category",
        company.get(
            "market_cap_category",
            "N/A",
        ),
    )


# ============================================================
# COMPANY INFORMATION
# ============================================================

st.divider()

st.subheader("Company Information")


about = company.get(
    "about_company",
    None,
)


if about and not pd.isna(about):

    st.write(
        str(about)
    )

else:

    st.info(
        "Company description is not available."
    )


# ============================================================
# OFFICIAL LINKS
# ============================================================

st.subheader(
    "Official Resources"
)


website = company.get(
    "website",
    None,
)

nse_profile = company.get(
    "nse_profile",
    None,
)

bse_profile = company.get(
    "bse_profile",
    None,
)


link_col1, link_col2, link_col3 = st.columns(3)


with link_col1:

    if website and not pd.isna(website):

        website = str(website).strip()

        if website:

            if not website.startswith(
                ("http://", "https://")
            ):

                website = (
                    "https://"
                    + website
                )

            st.link_button(
                "🌐 Company Website",
                website,
                width="stretch",
            )

    else:

        st.info(
            "Website unavailable."
        )


with link_col2:

    if nse_profile and not pd.isna(nse_profile):

        nse_profile = str(
            nse_profile
        ).strip()

        if nse_profile:

            if not nse_profile.startswith(
                ("http://", "https://")
            ):

                nse_profile = (
                    "https://"
                    + nse_profile
                )

            st.link_button(
                "📈 NSE Profile",
                nse_profile,
                width="stretch",
            )

    else:

        st.info(
            "NSE profile unavailable."
        )


with link_col3:

    if bse_profile and not pd.isna(bse_profile):

        bse_profile = str(
            bse_profile
        ).strip()

        if bse_profile:

            if not bse_profile.startswith(
                ("http://", "https://")
            ):

                bse_profile = (
                    "https://"
                    + bse_profile
                )

            st.link_button(
                "📊 BSE Profile",
                bse_profile,
                width="stretch",
            )

    else:

        st.info(
            "BSE profile unavailable."
        )


# ============================================================
# FINANCIAL STATEMENTS
# ============================================================

st.divider()

st.subheader(
    "Financial Statements"
)


pl = get_pl(
    company_id
)


if pl.empty:

    st.info(
        "Profit & Loss data is not available "
        f"for {company_name}."
    )

else:

    st.success(
        f"Financial data available for "
        f"{company_name}."
    )

    st.dataframe(
        pl,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# FINANCIAL YEARS
# ============================================================

if not pl.empty and "year" in pl.columns:

    st.divider()

    st.subheader(
        "Available Financial Years"
    )

    years = (
        pd.to_numeric(
            pl["year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
    )

    years = sorted(
        years,
        reverse=True,
    )


    if years:

        selected_financial_year = st.selectbox(
            "Select Financial Year",
            years,
        )

        year_data = pl[
            pd.to_numeric(
                pl["year"],
                errors="coerce",
            )
            == selected_financial_year
        ].copy()


        st.write(
            f"Financial data for "
            f"**{selected_financial_year}**"
        )


        st.dataframe(
            year_data,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# REPORT SEARCH
# ============================================================

st.divider()

st.subheader(
    "Annual Report Search"
)

st.write(
    "Use the official company, NSE or BSE resource "
    "above to locate the latest annual report."
)


report_query = st.text_input(
    "Report search query",
    value=f"{company_name} annual report",
)


if report_query:

    search_url = (
        "https://www.google.com/search?q="
        + report_query.replace(
            " ",
            "+",
        )
    )

    st.link_button(
        "🔎 Search Annual Report",
        search_url,
        width="stretch",
    )


# ============================================================
# REPORT CHECKLIST
# ============================================================

st.divider()

st.subheader(
    "Annual Report Checklist"
)


checklist = [
    "Revenue and sales growth",
    "Profit after tax",
    "Cash flow from operations",
    "Capital expenditure",
    "Total debt",
    "Management discussion",
    "Risk factors",
    "Related-party transactions",
    "Shareholding pattern",
    "Auditor's report",
]


for item in checklist:

    st.checkbox(
        item,
        key=f"{company_id}_{item}",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Company: {company_name} | "
    f"Company ID: {company_id} | "
    f"Database: nifty100.db"
)