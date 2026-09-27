"""
ForensicVault - Auth + Beautiful Homepage
"""

import streamlit as st
from datetime import datetime
from database import fetch_one, execute_query
from hashing import hash_password, verify_password


def init_session():
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "full_name": None,
        "role": None,
        "current_page": "Dashboard",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def log_audit(username, action_type, description):
    execute_query(
        "INSERT INTO audit_logs (username, action_type, action_description, timestamp) VALUES (?, ?, ?, ?)",
        (username, action_type, description, datetime.now().isoformat()),
    )


def login_user(username, password, role):
    if not username or not password:
        return False, "Please enter username and password."

    user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not user:
        return False, "❌ Invalid username or password."

    if user["status"] != "active":
        return False, "🚫 Account deactivated."

    if not verify_password(password, user["password_hash"], user["salt"]):
        log_audit(username, "Failed Login", "Invalid password")
        return False, "❌ Invalid username or password."

    if user["role"] != role:
        return False, f"⚠️ Role mismatch. Account role is '{user['role']}'."

    execute_query("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user["id"]))

    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.username = user["username"]
    st.session_state.full_name = f"{user['first_name']} {user['last_name']}"
    st.session_state.role = user["role"]

    log_audit(username, "Login", f"Logged in as {role}")
    return True, f"✅ Welcome back, {user['first_name']}!"


def register_user(fn, ln, un, em, pw, cpw, role):
    if not all([fn, ln, un, em, pw, cpw]):
        return False, "Please fill all fields."
    if len(un) < 3:
        return False, "Username must be at least 3 characters."
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if pw != cpw:
        return False, "Passwords do not match."
    if "@" not in em:
        return False, "Invalid email address."

    exists = fetch_one("SELECT id FROM users WHERE username = ? OR email = ?", (un, em))
    if exists:
        return False, "Username or email already exists."

    p_hash, salt = hash_password(pw)
    execute_query(
        """
        INSERT INTO users (first_name, last_name, username, email, password_hash, salt, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (fn, ln, un, em, p_hash, salt, role, datetime.now().isoformat()),
    )
    log_audit(un, "Registration", f"Registered as {role}")
    return True, "🎉 Account created successfully! Please login."


def logout():
    if st.session_state.authenticated:
        log_audit(st.session_state.username, "Logout", "User logged out")
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.full_name = None
    st.session_state.role = None
    st.rerun()


def render_login_page():
    left, center, right = st.columns([1, 4, 1])
    with center:
        st.markdown(
            """
            <div class="hero-wrap">
                <div class="hero-badge">SECURE FORENSIC PLATFORM</div>
                <h1 class="hero-title">🛡️ ForensicVault</h1>
                <p class="hero-subtitle">Digital Evidence & Case Management System</p>
                <div>
                    <span class="tech-pill">🐍 Python</span>
                    <span class="tech-pill">⚡ Streamlit</span>
                    <span class="tech-pill">🗄️ SQLite</span>
                    <span class="tech-pill">🔐 SHA-256</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_home, tab_login, tab_register = st.tabs(["🏠 Overview", "🔑 Login", "📝 Register"])

        with tab_home:
            st.markdown(
                """
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="feature-icon">📁</div>
                        <div class="feature-title">Case Management</div>
                        <div class="feature-desc">Create, track, filter and update investigation cases.</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🗂️</div>
                        <div class="feature-title">Evidence Vault</div>
                        <div class="feature-desc">Upload digital evidence and store secure metadata.</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🔐</div>
                        <div class="feature-title">SHA-256 Integrity</div>
                        <div class="feature-desc">Detect tampering with cryptographic file fingerprints.</div>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">⛓️</div>
                        <div class="feature-title">Chain of Custody</div>
                        <div class="feature-desc">Immutable timeline of every evidence action.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info("Use **Login** tab to access the system.")

        with tab_login:
            with st.container(border=True):
                st.subheader("User Authentication")
                with st.form("login_form"):
                    username = st.text_input("Username / Badge ID", placeholder="e.g. anact")
                    password = st.text_input("Password", type="password")
                    role = st.selectbox("Role", ["Administrator", "Investigator", "Forensic Analyst"])
                    submitted = st.form_submit_button("🚀 Login Securely", use_container_width=True, type="primary")
                    if submitted:
                        ok, msg = login_user(username, password, role)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with st.expander("Demo Credentials"):
                st.write("Admin: `anact` / `Anact@245`")
                st.write("Investigator: `anactt` / `Anact@245`")
                st.write("Analyst: `anacttt` / `Anact@245`")

        with tab_register:
            with st.container(border=True):
                st.subheader("Create Account")
                with st.form("register_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    fn = c1.text_input("First Name *")
                    ln = c2.text_input("Last Name *")
                    un = st.text_input("Username *")
                    em = st.text_input("Email *")
                    role = st.selectbox("Role *", ["Investigator", "Forensic Analyst", "Administrator"])
                    p1, p2 = st.columns(2)
                    pw = p1.text_input("Password *", type="password")
                    cpw = p2.text_input("Confirm Password *", type="password")
                    agree = st.checkbox("I agree to security terms")
                    reg = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                    if reg:
                        if not agree:
                            st.error("Please accept terms.")
                        else:
                            ok, msg = register_user(fn, ln, un, em, pw, cpw, role)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)

        st.markdown('<div class="footer-note">All actions are logged • SHA-256 integrity • Role-based access</div>', unsafe_allow_html=True)