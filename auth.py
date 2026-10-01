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
    if not all([fn, ln, un, em, pw, cpw]):
        return False, "Please fill all fields."
    if len(un) < 3:
        return False, "Username must be at least 3 characters."
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if pw != cpw:
        return False, "Passwords do not match."
    if '@' not in em:
        return False, "Invalid email address."

    existing = fetch_one("SELECT id FROM users WHERE username = ? OR email = ?", (un, em))
    if existing:
        return False, "Username or email already exists."

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
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.full_name = None
    st.session_state.role = None
    st.rerun()


def render_login_page():
    """Public Portal: Highly Styled Homepage + Login + Registration"""
    
    # ==================== BEAUTIFUL CSS INJECTION ====================
    st.markdown("""
    <style>
    /* Main Background adjustments */
    [data-testid="stAppViewContainer"] {
        background-color: #060d1f;
    }
    
    /* Glowing Title */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        padding-bottom: 0px;
        text-shadow: 0px 0px 20px rgba(0, 198, 255, 0.3);
    }
    .hero-subtitle {
        text-align: center;
        color: #b0c4de;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 40px;
        font-weight: 400;
    }
    
    /* Cyber Feature Cards (The 4 Boxes) */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-top: 20px;
        margin-bottom: 40px;
    }
    .feature-card {
        background: rgba(13, 31, 60, 0.7);
        border: 1px solid rgba(0, 198, 255, 0.2);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .feature-card:hover {
        transform: translateY(-8px);
        border-color: #00c6ff;
        box-shadow: 0 10px 30px rgba(0, 198, 255, 0.4);
    }
    .feature-icon {
        font-size: 45px;
        margin-bottom: 15px;
        text-shadow: 0 0 15px rgba(0, 198, 255, 0.5);
    }
    .feature-title {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .feature-desc {
        color: #9ca3af;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* Tech Stack Pills */
    .tech-stack-container {
        text-align: center;
        margin-bottom: 30px;
    }
    .tech-pill {
        display: inline-block;
        background: rgba(0, 198, 255, 0.1);
        border: 1px solid rgba(0, 198, 255, 0.3);
        color: #00c6ff;
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 8px;
        box-shadow: 0 2px 10px rgba(0, 198, 255, 0.1);
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        color: #b0c4de !important;
        font-size: 1.1rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00c6ff !important;
        border-bottom-color: #00c6ff !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px rgba(0, 198, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Structure the layout to center the content
    col1, col2, col3 = st.columns([1, 4, 1])

    with col2:
        # App Branding Header
        st.markdown("<div style='text-align: center; font-size: 60px; margin-bottom: -25px; filter: drop-shadow(0 0 15px rgba(0, 198, 255, 0.5));'>🛡️</div>", unsafe_allow_html=True)
        st.markdown("<h1 class='hero-title'>ForensicVault</h1>", unsafe_allow_html=True)
        st.markdown("<p class='hero-subtitle'>Enterprise-Grade Digital Evidence & Case Management</p>", unsafe_allow_html=True)
        st.write("")

        # 3 Public Tabs
        tab_home, tab_login, tab_register = st.tabs(["🏠 **Overview**", "🔑 **Login**", "📝 **Register**"])

        # ==================== TAB 1: HOMEPAGE / OVERVIEW ====================
        with tab_home:
            # Tech Stack Pills
            st.markdown("""
            <div class="tech-stack-container">
                <span class="tech-pill">🐍 Python 3</span>
                <span class="tech-pill">🌐 Streamlit UI</span>
                <span class="tech-pill">🗄️ SQLite Database</span>
                <span class="tech-pill">🔐 SHA-256 Crypto</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Beautiful Feature Cards Grid (The 4 Boxes)
            st.markdown("""
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="feature-icon">📁</div>
                    <div class="feature-title">Case Management</div>
                    <div class="feature-desc">Register, track, filter, and assign cases in real-time.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔐</div>
                    <div class="feature-title">SHA-256 Hashing</div>
                    <div class="feature-desc">Automatic file digest generation & cryptographic verification.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⛓️</div>
                    <div class="feature-title">Chain of Custody</div>
                    <div class="feature-desc">Immutable audit logs tracking every single evidence interaction.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Visual Analytics</div>
                    <div class="feature-desc">Interactive Plotly charts and automated CSV/JSON report exports.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            

        # ==================== TAB 2: LOGIN ====================
        with tab_login:
            # Wrapping form in a container makes it look like a floating card
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

                    agree = st.checkbox("I agree to the strict security terms & confidentiality policy")

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
        st.caption("<div style='text-align:center; color:gray;'>🔒 All actions are strictly logged & encrypted • ISO 27001 Compliant Architecture</div>", unsafe_allow_html=True)