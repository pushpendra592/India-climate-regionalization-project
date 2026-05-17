"""Global CSS injection for the dashboard — white/red theme, no emojis."""
import streamlit as st


def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #111827;
    }
    .main { background: #ffffff; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }

    /* ---- Buttons ---- */
    .stButton > button {
        background: #C0392B !important; color: #fff !important;
        border: none !important; border-radius: 4px !important;
        font-weight: 500 !important; font-size: 0.875rem !important;
        padding: 0.45rem 1.1rem !important;
        transition: background 0.15s !important;
    }
    .stButton > button:hover { background: #A93226 !important; }
    .stButton > button:focus { box-shadow: 0 0 0 3px rgba(192,57,43,0.25) !important; }

    /* ---- Tab styling ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0; border-bottom: 2px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.83rem; font-weight: 500; color: #6b7280;
        padding: 0.55rem 1.1rem; border-radius: 0;
        border-bottom: 2px solid transparent; margin-bottom: -2px;
    }
    .stTabs [aria-selected="true"] {
        color: #C0392B !important; border-bottom-color: #C0392B !important;
        background: transparent !important;
    }

    /* ---- KPI tile ---- */
    .kpi-tile {
        background: #fff; border: 1px solid #e5e7eb;
        border-top: 3px solid #C0392B; border-radius: 6px; padding: 16px 18px;
        margin-bottom: 24px;
    }
    .kpi-label {
        font-size: 0.7rem; color: #9ca3af; text-transform: uppercase;
        letter-spacing: 0.07em; margin-bottom: 6px;
    }
    .kpi-value { font-size: 1.9rem; font-weight: 700; color: #C0392B; line-height: 1.1; }
    .kpi-sub { font-size: 0.72rem; color: #9ca3af; margin-top: 5px; }

    /* ---- Section heading ---- */
    .sec-head {
        display: flex; align-items: center; gap: 12px;
        margin: 40px 0 16px;
    }
    .sec-bar { width: 4px; height: 26px; background: #C0392B; border-radius: 2px; flex-shrink: 0; }
    .sec-title { font-size: 1.45rem; font-weight: 700; color: #111827; margin: 0; letter-spacing: -0.02em; }
    .sec-caption { font-size: 0.78rem; color: #6b7280; margin: -8px 0 14px 12px; }

    /* ---- Page header ---- */
    .page-header { border-bottom: 1px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 32px; }
    .page-header h1 { font-size: 1.35rem; font-weight: 700; color: #111827; margin: 0 0 4px; }
    .page-header p { font-size: 0.84rem; color: #6b7280; margin: 0; line-height: 1.6; }

    /* ---- Pipeline stage ---- */
    .pip-row { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
    .pip-row:last-child { border-bottom: none; }
    .pip-num {
        font-size: 0.68rem; font-weight: 700; color: #C0392B;
        background: #fdf3f2; border-radius: 3px; padding: 2px 7px;
        white-space: nowrap; margin-top: 2px; height: fit-content;
    }
    .pip-title { font-size: 0.9rem; font-weight: 600; color: #111827; margin-bottom: 2px; }
    .pip-desc { font-size: 0.81rem; color: #6b7280; line-height: 1.55; }

    /* ---- Feature card (inside expander) ---- */
    .feat-card {
        background: #f9fafb; border: 1px solid #e5e7eb;
        border-left: 3px solid #C0392B; border-radius: 0 6px 6px 0;
        padding: 12px 14px; margin-bottom: 8px;
    }
    .feat-name { font-family: 'Courier New', monospace; font-size: 0.83rem; font-weight: 700; color: #111827; }
    .feat-label { font-size: 0.75rem; color: #C0392B; font-weight: 500; margin: 2px 0 5px; }
    .feat-desc { font-size: 0.8rem; color: #6b7280; line-height: 1.55; margin-bottom: 6px; }
    .feat-formula {
        font-family: 'Courier New', monospace; font-size: 0.77rem;
        background: #fff; border: 1px solid #e5e7eb;
        border-radius: 3px; padding: 3px 8px; color: #374151; display: inline-block;
    }
    .feat-formula-label { font-size: 0.7rem; color: #9ca3af; margin-bottom: 2px; }

    /* ---- Journey box ---- */
    .journey-box {
        background: #fff; border: 1px solid #e5e7eb;
        border-top: 3px solid #C0392B; border-radius: 6px; padding: 16px 18px;
        margin-bottom: 24px;
    }
    .journey-box h4 { font-size: 0.88rem; font-weight: 600; color: #111827; margin: 0 0 10px; }
    .journey-box li { font-size: 0.81rem; color: #6b7280; line-height: 1.8; }

    /* ---- Info card ---- */
    .info-card {
        background: #f9fafb; border: 1px solid #e5e7eb;
        border-radius: 6px; padding: 12px 16px;
        font-size: 0.81rem; color: #6b7280; line-height: 1.6;
        margin-bottom: 24px;
    }

    /* ---- Prediction result card ---- */
    .pred-card {
        background: #fdf3f2; border-left: 3px solid #C0392B;
        border-radius: 0 6px 6px 0; padding: 14px 18px; margin-bottom: 14px;
    }
    .pred-label { font-size: 0.72rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }
    .pred-value { font-size: 1.05rem; font-weight: 600; color: #111827; }

    /* ---- Metrics ---- */
    [data-testid="metric-container"] {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px 16px;
        margin-bottom: 16px;
    }
    [data-testid="metric-container"] label { font-size: 0.72rem !important; color: #9ca3af !important; }
    [data-testid="metric-container"] [data-testid="metric-value"] { color: #C0392B !important; }

    /* ---- Dataframe ---- */
    .dataframe thead tr th {
        background: #f9fafb !important; color: #374151 !important;
        font-size: 0.78rem !important; font-weight: 600 !important;
        border-bottom: 2px solid #e5e7eb !important;
    }
    .dataframe tbody tr td { font-size: 0.8rem !important; color: #374151 !important; }

    /* ---- Divider ---- */
    hr { border: none; border-top: 1px solid #e5e7eb; margin: 32px 0; }

    /* ---- Expander ---- */
    .streamlit-expanderHeader {
        font-size: 0.88rem !important; font-weight: 600 !important; color: #111827 !important;
        background: #f9fafb !important; border-radius: 5px !important;
        margin-top: 8px !important;
    }
    .streamlit-expanderHeader:hover { background: #fdf3f2 !important; color: #C0392B !important; }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] { background: #f9fafb; border-right: 1px solid #e5e7eb; }
    [data-testid="stSidebar"] .stTextInput input {
        border: 1px solid #e5e7eb; border-radius: 4px; font-size: 0.88rem;
    }
    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #C0392B; box-shadow: 0 0 0 2px rgba(192,57,43,0.15);
    }
    </style>
    """, unsafe_allow_html=True)


def section_heading(title: str, caption: str = ""):
    st.markdown(
        f"""<div class="sec-head">
                <div class="sec-bar"></div>
                <p class="sec-title">{title}</p>
            </div>""",
        unsafe_allow_html=True,
    )
    if caption:
        st.markdown(f'<p class="sec-caption">{caption}</p>', unsafe_allow_html=True)


def kpi_tile(col, value: str, label: str, sub: str = ""):
    with col:
        st.markdown(
            f"""<div class="kpi-tile">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>""",
            unsafe_allow_html=True,
        )
