"""ForensicVault - Chain of Custody Module"""
import streamlit as st
import pandas as pd
from database import fetch_all

def render_custody():
    st.title("⛓️ Chain of Custody")
    st.caption("Immutable audit log tracking all evidence handlings.")
    st.divider()

    logs = fetch_all("""
        SELECT cl.timestamp, cl.evidence_id, cl.action, u.username, u.role, cl.description
        FROM custody_logs cl
        JOIN users u ON cl.performed_by = u.id
        ORDER BY cl.id DESC
    """)

    if logs:
        df = pd.DataFrame([dict(l) for l in logs])
        df.columns = ["Timestamp", "Evidence ID", "Action", "Performed By", "Role", "Details"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No custody records logged yet.")