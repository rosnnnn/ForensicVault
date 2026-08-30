"""ForensicVault - User Management (Admin Only)"""
import streamlit as st
import pandas as pd
from database import fetch_all, execute_query
from utils import has_permission

def render_users():
    if not has_permission(st.session_state.user_role, 'users'):
        st.error("🚫 Access Restricted: Administrators only.")
        return

    st.title("👥 User Management")
    st.caption("Administrator panel to manage user accounts.")
    st.divider()

    users = fetch_all("SELECT id, username, first_name, last_name, email, role, status, created_at, last_login FROM users")
    df = pd.DataFrame([dict(u) for u in users])
    st.dataframe(df, use_container_width=True, hide_index=True)