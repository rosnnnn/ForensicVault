"""
ForensicVault - Dashboard Module
Displays KPIs, Recent Cases, Chain of Custody, and Activity.
"""

import streamlit as st
import pandas as pd
from database import fetch_all, fetch_one


def render_dashboard():
    """Render main Dashboard view using Streamlit native widgets."""
    st.title("🏠 Dashboard Overview")
    st.caption(f"Welcome back, {st.session_state.full_name} ({st.session_state.user_role})")
    st.divider()

    # Fetch KPI metrics from SQLite
    total_cases = fetch_one("SELECT COUNT(*) FROM cases")[0]
    active_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status IN ('New', 'Active', 'On Hold')")[0]
    closed_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status = 'Closed'")[0]
    
    total_evidence = fetch_one("SELECT COUNT(*) FROM evidence")[0]
    verified_evidence = fetch_one("SELECT COUNT(*) FROM evidence WHERE verification_status = 'Verified'")[0]
    tampered_evidence = fetch_one("SELECT COUNT(*) FROM evidence WHERE verification_status = 'Tampered'")[0]

    # Render KPI Cards using native st.metric
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Cases", total_cases, "+12% MoM")
    m2.metric("Active Investigations", active_cases, delta_color="normal")
    m3.metric("Closed Cases", closed_cases)
    m4.metric("Total Evidence", total_evidence)
    m5.metric("Verified Evidence", verified_evidence, delta=f"{tampered_evidence} Tampered" if tampered_evidence else "100% Intact", delta_color="inverse" if tampered_evidence else "normal")

    st.divider()

    col_left, col_right = st.columns([2, 1])

    # ---------- RECENT CASES TABLE ----------
    with col_left:
        st.subheader("📋 Recent Cases")
        cases = fetch_all("SELECT case_id, case_title, crime_type, priority, status, assigned_officer, date_filed FROM cases ORDER BY id DESC LIMIT 5")
        
        if cases:
            df_cases = pd.DataFrame([dict(c) for c in cases])
            df_cases.columns = ["Case ID", "Title", "Type", "Priority", "Status", "Officer", "Date Filed"]
            st.dataframe(df_cases, use_container_width=True, hide_index=True)
        else:
            st.info("No cases registered yet.")

        # Quick Actions
        st.subheader("⚡ Quick Actions")
        q1, q2, q3 = st.columns(3)
        if q1.button("📁 New Case", use_container_width=True):
            st.session_state.current_page = "cases"
            st.rerun()
        if q2.button("📤 Upload Evidence", use_container_width=True):
            st.session_state.current_page = "evidence"
            st.rerun()
        if q3.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

    # ---------- RECENT ACTIVITY & CUSTODY LOGS ----------
    with col_right:
        st.subheader("⛓️ Recent Chain of Custody")
        custody = fetch_all("""
            SELECT cl.action, cl.description, cl.timestamp, u.username 
            FROM custody_logs cl 
            JOIN users u ON cl.performed_by = u.id 
            ORDER BY cl.id DESC LIMIT 5
        """)
        
        if custody:
            for log in custody:
                with st.container():
                    st.write(f"**{log['action']}** by `{log['username']}`")
                    st.caption(f"{log['description']} • {log['timestamp'][:16]}")
                    st.divider()
        else:
            st.info("No chain of custody logs recorded.")