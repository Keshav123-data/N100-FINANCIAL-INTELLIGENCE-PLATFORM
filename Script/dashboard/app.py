from pathlib import Path
import sys

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PAGE DEFINITIONS
# ============================================================

pages = [
    st.Page(
        "pages/01_home.py",
        title="Home",
        icon="🏠",
        default=True,
    ),
    st.Page(
        "pages/02_profile.py",
        title="Company Profile",
        icon="🏢",
    ),
    st.Page(
        "pages/03_screener.py",
        title="Screener",
        icon="🔎",
    ),
    st.Page(
        "pages/04_peers.py",
        title="Peer Comparison",
        icon="📊",
    ),
    st.Page(
        "pages/05_trends.py",
        title="Trend Analysis",
        icon="📈",
    ),
    st.Page(
        "pages/06_sectors.py",
        title="Sector Analysis",
        icon="🏭",
    ),
    st.Page(
        "pages/07_capital.py",
        title="Capital Allocation",
        icon="💰",
    ),
    st.Page(
        "pages/08_reports.py",
        title="Annual Reports",
        icon="📄",
    ),
]


# ============================================================
# SIDEBAR HEADER
# ============================================================

with st.sidebar:

    st.title("NIFTY 100")

    st.caption(
        "Financial Intelligence Platform"
    )

    st.divider()

    st.caption(
        "Sprint 4 — Dashboard & Valuation"
    )

    st.caption(
        "92 listed companies"
    )


# ============================================================
# NAVIGATION
# ============================================================

navigation = st.navigation(
    pages,
    position="sidebar",
)

navigation.run()