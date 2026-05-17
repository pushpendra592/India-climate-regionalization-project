"""
Sidebar controls for the Streamlit dashboard.
"""

import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="
                font-size:1.05rem;font-weight:700;color:#111827;
                padding-bottom:10px;border-bottom:2px solid #C0392B;
                margin-bottom:18px;letter-spacing:0.01em;">
                Climate Cluster Lookup
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="font-size:0.78rem;color:#6b7280;line-height:1.7;margin-bottom:16px;">
            Enter a place name to fetch its NASA POWER weather history and assign
            it to the closest learned climate region.
            </div>
            """,
            unsafe_allow_html=True,
        )

        place_name = st.text_input(
            "Place name",
            value="Delhi",
            placeholder="e.g. Mumbai, Jaipur, Chennai",
        )

        trigger = st.button("Predict Climate Cluster", use_container_width=True)

        st.markdown(
            """
            <div style="
                margin-top:20px;background:#f9fafb;border:1px solid #e5e7eb;
                border-radius:5px;padding:12px 14px;">
                <div style="font-size:0.72rem;font-weight:600;color:#C0392B;
                    text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
                    How to use
                </div>
                <div style="font-size:0.78rem;color:#6b7280;line-height:1.8;">
                    1. Type any Indian city or town<br>
                    2. Click <strong style="color:#111827;">Predict Climate Cluster</strong><br>
                    3. Explore results across all tabs
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {"place_name": place_name, "trigger": trigger}
