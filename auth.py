"""
ForensicVault - Authentication & Public Landing Module
"""
import streamlit as st
from datetime import datetime
from database import fetch_one, execute_query
from hashing import hash_password, verify_password

def init_session():
    defaults = {
        'authenticated': False,
        'user_id': None,
        'username': None,
        'full_name': None,
        'role': None,
        'current_page': 'Dashboard'
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def log_audit(username, action_type, description):
    now = datetime.now().isoformat()
    execute_query(
        "INSERT INTO audit_logs (username, action_type, action_description, timestamp) VALUES (?, ?, ?, ?)",
        (username, action_type, description, now)
    )

def login_user(username, password, role):
    if not username or not password:
        return False, "Please enter username and password."

    user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not user:
        return False, "❌ Invalid username or password."

    if user['status'] != 'active':
        return False, "🚫 Account is deactivated. Contact administrator."

    if not verify_password(password, user['password_hash'], user['salt']):
        log_audit(username, "Failed Login", "Invalid password")
        return False, "❌ Invalid username or password."

    if user['role'] != role:
        return False, f"⚠️ Role mismatch. This account is registered as '{user['role']}'."

    now = datetime.now().isoformat()
    execute_query("UPDATE users SET last_login = ? WHERE id = ?", (now, user['id']))

    st.session_state.authenticated = True
    st.session_state.user_id = user['id']
    st.session_state.username = user['username']
    st.session_state.full_name = f"{user['first_name']} {user['last_name']}"
    st.session_state.role = user['role']

    log_audit(username, "Login", f"Logged in as {role}")
    return True, f"✅ Welcome back, {user['first_name']}!"

def register_user(fn, ln, un, em, pw, cpw, role):
    if not all([fn, ln, un, em, pw, cpw]): return False, "Please fill all fields."
    if len(un) < 3: return False, "Username must be at least 3 characters."
    if len(pw) < 8: return False, "Password must be at least 8 characters."
    if pw != cpw: return False, "Passwords do not match."
    if '@' not in em: return False, "Invalid email address."

    existing = fetch_one("SELECT id FROM users WHERE username = ? OR email = ?", (un, em))
    if existing: return False, "Username or email already exists."

    p_hash, salt = hash_password(pw)
    now = datetime.now().isoformat()

    try:
        execute_query("""
            INSERT INTO users (first_name, last_name, username, email, password_hash, salt, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fn, ln, un, em, p_hash, salt, role, now))
        log_audit(un, "Registration", f"New user registered as {role}")
        return True, "🎉 Account created successfully! Please log in."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def logout():
    if st.session_state.authenticated:
        log_audit(st.session_state.username, "Logout", "User logged out")
    for key in ['authenticated', 'user_id', 'username', 'full_name', 'role']:
        st.session_state[key] = None if key != 'authenticated' else False
    st.rerun()

def render_login_page():
    """Beautiful 3-Tab Homepage and Auth Portal"""
    st.write("")
    
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        # App Branding Header
        st.markdown("<h1 style='text-align: center; font-size: 55px; color: #00c6ff;'>🛡️ ForensicVault</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; font-size: 16px;'>Secure Digital Evidence & Case Management System</p>", unsafe_allow_html=True)
        st.write("")

        # 3 Public Tabs
        tab_home, tab_login, tab_register = st.tabs(["🏠 **Overview**", "🔑 **Login**", "📝 **Register**"])

        # ==================== TAB 1: HOMEPAGE / OVERVIEW ====================
        with tab_home:
            st.markdown("### Welcome to ForensicVault")
            st.markdown("""
            **ForensicVault** is an enterprise-grade digital evidence and case management prototype 
            designed to streamline cybercrime investigations while maintaining strict evidentiary integrity.
            """)
            st.divider()

            st.markdown("#### ✨ Key Features")
            f1, f2 = st.columns(2)
            with f1:
                st.info("**📁 Case Management**\n\nRegister, track, filter, and assign cases.")
                st.info("**🔐 SHA-256 Hashing**\n\nAutomatic file digest generation & verification.")
            with f2:
                st.info("**⛓️ Chain of Custody**\n\nImmutable logs tracking every evidence interaction.")
                st.info("**📊 Visual Analytics**\n\nInteractive Plotly charts and report generation.")

            st.divider()

            st.markdown("#### 🛠️ Technology Stack")
            c1, c2, c3, c4 = st.columns(4)
            c1.success("**Python 3**\n\nCore Logic")
            c2.success("**Streamlit**\n\nUser Interface")
            c3.success("**SQLite 3**\n\nDatabase")
            c4.success("**hashlib**\n\nCryptography")

        # ==================== TAB 2: LOGIN ====================
        with tab_login:
            with st.container(border=True):
                st.markdown("### 🔐 User Authentication")
                st.caption("Enter your credentials to access the secure vault")
                st.write("")

                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("👤 Username / Badge ID", placeholder="e.g., anact")
                    password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
                    role = st.selectbox("🎖️ Select Role", ["Administrator", "Investigator", "Forensic Analyst"])

                    st.write("")
                    submitted = st.form_submit_button("🚀 Authenticate & Login", use_container_width=True, type="primary")

                    if submitted:
                        success, msg = login_user(username, password, role)
                        if success:
                            st.success(msg)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(msg)

            # Demo Credentials Expander
            with st.expander("💡 View Demo Credentials"):
                st.info("""
                **🔑 Administrator**  
                Username: `anact` | Password: `Anact@245`

                **🕵️ Investigator**  
                Username: `anactt` | Password: `Anact@245`

                **🔬 Forensic Analyst**  
                Username: `anacttt` | Password: `Anact@245`
                """)

        # ==================== TAB 3: REGISTER ====================
        with tab_register:
            with st.container(border=True):
                st.markdown("### 🚀 Create New Account")
                st.caption("Register for authorized system access")
                st.write("")
                
                with st.form("register_form", clear_on_submit=True):
                    rc1, rc2 = st.columns(2)
                    fn = rc1.text_input("First Name *", placeholder="John")
                    ln = rc2.text_input("Last Name *", placeholder="Doe")

                    un = st.text_input("Username / Badge ID *", placeholder="Choose unique username")
                    em = st.text_input("Email Address *", placeholder="officer@agency.gov")

                    role_reg = st.selectbox("Select Role *", ["Investigator", "Forensic Analyst", "Administrator"])

                    rc3, rc4 = st.columns(2)
                    pw = rc3.text_input("Password *", type="password", placeholder="Min 8 characters")
                    cpw = rc4.text_input("Confirm Password *", type="password", placeholder="Repeat password")

                    agree = st.checkbox("I agree to the security terms & privacy policy")

                    st.write("")
                    reg_submit = st.form_submit_button("✅ Create Account", use_container_width=True, type="primary")

                    if reg_submit:
                        if not agree:
                            st.error("⚠️ Please accept the security terms to continue.")
                        else:
                            success, msg = register_user(fn, ln, un, em, pw, cpw, role_reg)
                            if success:
                                st.success(msg)
                                st.balloons()
                            else:
                                st.error(msg)

        st.write("")
        st.caption("<div style='text-align:center; color:gray;'>🔒 All actions are logged & encrypted • ISO 27001 Compliant</div>", unsafe_allow_html=True)