import streamlit as st

from Script.dashboard.utils.db import get_database_tables


st.title("📊 Peer Comparison")

st.info(
    "Peer comparison radar chart and benchmark "
    "table will be implemented on Day 24."
)

st.write(
    "Available database tables:"
)

st.write(
    get_database_tables()
)