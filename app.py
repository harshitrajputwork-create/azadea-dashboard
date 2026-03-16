import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_loader import (
    load_chiller_freezer_data,
    load_hygiene_data,
    load_manager_checklists,
)
from dashboards.chiller_freezer import render_chiller_freezer
from dashboards.hygiene_receiving import render_hygiene_receiving
from dashboards.manager_checklists import render_manager_checklists

st.set_page_config(
    page_title="Azadea Analytics Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Enterprise CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }

/* ── Main content area ── */
.stApp { background-color: #f0f2f6 !important; color: #1a1a2e !important; }

/* ── Sidebar: force white bg + dark text ── */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #dde1ea !important;
    min-width: 240px !important;
}
section[data-testid="stSidebar"] * { color: #1a1a2e !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 4px 0 !important;
}

/* ── All headings ── */
h1, h2, h3, h4, h5, h6 { color: #1a1a2e !important; font-weight: 700 !important; }

/* ── KPI Metric Cards with color-coded left borders ── */
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 5px solid #3b82f6 !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] {
    color: #1a1a2e !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Plotly charts get white card wrapper ── */
.stPlotlyChart {
    background: #ffffff !important;
    border-radius: 10px !important;
    padding: 8px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
}

/* ── Tabs ── */
button[data-baseweb="tab"] { color: #374151 !important; font-weight: 600 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #1a1a2e !important; border-bottom-color: #3b82f6 !important; }

/* ── Alerts & expanders ── */
.stAlert { border-radius: 8px !important; }
details summary { font-weight: 600 !important; color: #374151 !important; }

/* ── Dataframe / table ── */
.stDataFrame { border-radius: 8px !important; overflow: hidden !important; }

/* ── Hide branding ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str, icon: str):
    """Dark navy enterprise-style header banner."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
                color: white; padding: 22px 28px; border-radius: 12px;
                margin-bottom: 24px; display: flex; align-items: center; gap: 16px;
                box-shadow: 0 4px 16px rgba(15,52,96,0.25);">
        <span style="font-size: 2.2rem; line-height:1;">{icon}</span>
        <div>
            <div style="font-size: 0.68rem; font-weight: 700; opacity: 0.6;
                        letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 4px;">
                AZADEA OPERATIONS DASHBOARD
            </div>
            <div style="font-size: 1.55rem; font-weight: 800; line-height: 1.2;">{title}</div>
            <div style="font-size: 0.82rem; opacity: 0.7; margin-top: 4px;">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_all_data(chiller_file, hygiene_file, m_open, m_mid, m_close, _version=4):
    """Load and process datasets. Increment _version to bust stale cache."""
    chiller_df   = load_chiller_freezer_data(chiller_file)
    hygiene_df   = load_hygiene_data(hygiene_file)
    manager_df   = load_manager_checklists(m_open, m_mid, m_close)
    return chiller_df, hygiene_df, manager_df


def main():
    # ── Sidebar brand header ─────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="padding: 18px 12px 8px 12px;">
        <div style="font-size: 0.65rem; font-weight: 700; color: #94a3b8;
                    letter-spacing: 0.14em; text-transform: uppercase;">
            Powered by Taqtics
        </div>
        <div style="font-size: 1.25rem; font-weight: 800; color: #1a1a2e; margin-top: 3px;">
            Azadea Analytics
        </div>
    </div>
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 6px 0 14px 0;">
    """, unsafe_allow_html=True)

    # ── Navigation ───────────────────────────────────────────────────────
    st.sidebar.markdown('<div style="font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">📊 Dashboards</div>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "nav",
        ["🧊  Chiller & Freezer Log", "🧼  Chef Hygiene Checklists", "📋  Manager Checklists"],
        label_visibility="collapsed"
    )

    # ── Upload CSV section ───────────────────────────────────────────────
    st.sidebar.markdown('<hr style="border:none; border-top:1px solid #e2e8f0; margin:14px 0;">', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">📁 Upload CSV Data</div>', unsafe_allow_html=True)
    with st.sidebar.expander("Replace default files", expanded=False):
        st.caption("Upload to override default source data.")
        up_chiller = st.file_uploader("Chiller & Freezer CSV", type=["csv"], key="uc")
        up_hygiene = st.file_uploader("Hygiene Checklist CSV", type=["csv"], key="uh")

    # ── File paths (defaults) ────────────────────────────────────────────
    chiller_path   = up_chiller if up_chiller else r"c:\Users\Harshit Rajput\Downloads\Herfy V\Chiller & Freez_01February2026_31March2026.csv"
    hygiene_path   = up_hygiene if up_hygiene else r"c:\Users\Harshit Rajput\Downloads\Personal Hygiene Checklist.csv"
    op_path  = r"c:\Users\Harshit Rajput\Downloads\MANAGER OPENING CHECK - KITCHEN (Before The Biefing) (7).csv"
    mid_path = r"c:\Users\Harshit Rajput\Downloads\MANAGER MID-SHIFT CHECK - KITCHEN (during employee changeover).csv"
    cl_path  = r"c:\Users\Harshit Rajput\Downloads\MANAGER CLOSING CHECK - KITCHEN.csv"

    # ── Load data ────────────────────────────────────────────────────────
    with st.spinner("Loading data..."):
        try:
            chiller_df, hygiene_df, manager_df = load_all_data(
                chiller_path, hygiene_path, op_path, mid_path, cl_path
            )
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

    # ── Date filter ──────────────────────────────────────────────────────
    st.sidebar.markdown('<hr style="border:none; border-top:1px solid #e2e8f0; margin:14px 0;">', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">🗓️ Date Range</div>', unsafe_allow_html=True)
    start_date = pd.to_datetime("2026-02-01").date()
    end_date   = pd.to_datetime("2026-03-31").date()
    date_range = st.sidebar.date_input(
        "date_range", value=(start_date, end_date),
        min_value=pd.to_datetime("2026-01-01").date(),
        max_value=pd.to_datetime("2026-12-31").date(),
        label_visibility="collapsed"
    )
    if len(date_range) != 2:
        st.warning("Please select a complete date range.")
        st.stop()

    global_start_date, global_end_date = date_range
    global_start_datetime = pd.to_datetime(global_start_date)
    global_end_datetime   = pd.to_datetime(global_end_date) + pd.Timedelta(days=1, microseconds=-1)

    st.sidebar.markdown("""
    <hr style="border:none; border-top:1px solid #e2e8f0; margin:14px 0;">
    <div style="font-size:0.72rem; color:#94a3b8; padding:0 4px; line-height:1.5;">
        Data from Taqtics Checklist Submissions<br>Feb – Mar 2026
    </div>
    """, unsafe_allow_html=True)

    # ── Route to selected dashboard ──────────────────────────────────────
    if "Chiller" in page:
        render_page_header(
            "Chiller & Freezer Temperature Log",
            "Track temperature readings across all chiller and freezer units",
            "🧊"
        )
        render_chiller_freezer(chiller_df, global_start_datetime, global_end_datetime)

    elif "Hygiene" in page:
        render_page_header(
            "Chef Hygiene Checklists",
            "Personal hygiene checks and compliance tracking by staff member",
            "🧼"
        )
        render_hygiene_receiving(hygiene_df, global_start_datetime, global_end_datetime)

    elif "Manager" in page:
        render_page_header(
            "Manager Checklists — Opening, Mid & Closing",
            "Submission tracking and compliance across all shift types",
            "📋"
        )
        render_manager_checklists(manager_df, global_start_datetime, global_end_datetime)


if __name__ == "__main__":
    main()
