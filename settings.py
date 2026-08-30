"""ForensicVault - User Settings Module"""
import streamlit as st
from database import fetch_one, execute_query
from hashing import hash_password, verify_password

def render_settings():
    st.title("⚙️ Account Settings")
    st.caption("Manage your profile and security credentials.")
    st.divider()

    st.subheader("Profile Information")
    st.write(f"**Name:** {st.session_state.full_name}")
    st.write(f"**Username:** `{st.session_state.username}`")
    st.write(f"**Role:** {st.session_state.user_role}")

    st.divider()
    st.subheader("🔑 Change Password")
    with st.form("change_pw_form"):
        old_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submit = st.form_submit_button("Update Password")

        if submit:
            user = fetch_one("SELECT * FROM users WHERE id = ?", (st.session_state.user_id,))
            if not verify_password(old_pw, user["password_hash"], user["salt"]):
                st.error("Incorrect current password")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match")
            elif len(new_pw) < 8:
                st.error("Password must be at least 8 characters")
            else:
                pw_hash, salt = hash_password(new_pw)
                execute_query("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pw_hash, salt, st.session_state.user_id))
                st.success("Password updated successfully!")