"""
ForensicVault - Theme Loader
Loads style.css into Streamlit app.
"""

from pathlib import Path
import streamlit as st


def apply_theme():
    """Load global CSS for all pages."""
    css_path = Path("style.css")

    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        # fallback mini theme if css missing
        st.markdown(
            """
            <style>
            .stApp { background:#060d1f; color:#fff; }
            div[data-testid="stMetric"] {
                background:#0d1f3c; border:1px solid rgba(0,198,255,.25);
                border-radius:14px; padding:14px;
            }
            .stButton>button {
                background:linear-gradient(135deg,#00c6ff,#0072ff);
                color:white; border:none; border-radius:10px; font-weight:700;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )