"""ForensicVault - Plotly Analytics Module"""
import streamlit as st
import pandas as pd
import plotly.express as px
from database import fetch_all

def render_analytics():
    st.title("📊 Analytical Insights")
    st.caption("Real-time visual metrics powered by Plotly.")
    st.divider()

    cases = fetch_all("SELECT crime_type, priority, status, assigned_officer FROM cases")
    evidence = fetch_all("SELECT evidence_type, verification_status FROM evidence")

    if cases:
        df_cases = pd.DataFrame([dict(c) for c in cases])
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cases by Crime Type")
            fig1 = px.pie(df_cases, names="crime_type", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Cases by Priority")
            fig2 = px.bar(df_cases, x="priority", color="priority", color_discrete_map={"Critical":"red","High":"orange","Medium":"yellow","Low":"green"})
            st.plotly_chart(fig2, use_container_width=True)

    if evidence:
        df_ev = pd.DataFrame([dict(e) for e in evidence])
        st.subheader("Evidence Verification Status")
        fig3 = px.pie(df_ev, names="verification_status")
        st.plotly_chart(fig3, use_container_width=True)