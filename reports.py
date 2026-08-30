"""ForensicVault - Reports Module with CSV Export"""
import streamlit as st
import pandas as pd
from database import fetch_all

def render_reports():
    st.title("📄 Report Generation")
    st.caption("Generate & export investigation reports.")
    st.divider()

    report_type = st.selectbox("Select Report Type", ["Case Summary Report", "Evidence Inventory Report", "Chain of Custody Audit Report"])

    if report_type == "Case Summary Report":
        data = fetch_all("SELECT case_id, case_title, crime_type, priority, status, assigned_officer, date_filed FROM cases")
    elif report_type == "Evidence Inventory Report":
        data = fetch_all("SELECT evidence_id, case_id, evidence_type, original_filename, sha256_hash, verification_status FROM evidence")
    else:
        data = fetch_all("SELECT timestamp, evidence_id, action, description FROM custody_logs")

    if data:
        df = pd.DataFrame([dict(d) for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Report as CSV", csv, f"{report_type.replace(' ', '_').lower()}.csv", "text/csv", use_container_width=True)
    else:
        st.info("No data available for this report.")