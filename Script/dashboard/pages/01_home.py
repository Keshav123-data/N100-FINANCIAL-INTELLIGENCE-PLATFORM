import streamlit as st

from Script.dashboard.utils.db import (
    get_companies,
    get_database_tables,
)


st.title("🏠 Nifty 100 Analytics")

st.subheader(
    "Financial Intelligence Dashboard"
)

st.info(
    "Home dashboard will be implemented on Day 23."
)

companies = get_companies()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Companies",
        len(companies),
    )

with col2:
    st.metric(
        "Database Tables",
        len(get_database_tables()),
    )

with col3:
    st.metric(
        "Dashboard Status",
        "Online",
    )

st.divider()

st.subheader("Sprint 4")

st.write(
    """
    The Nifty 100 Analytics dashboard provides
    company-level financial analysis, screening,
    peer comparison, trend analysis, sector analysis,
    capital allocation analysis and annual reports.
    """
)