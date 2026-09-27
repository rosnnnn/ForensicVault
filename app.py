"""
ForensicVault - Main Application
Pure Python + Streamlit Web App
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
import uuid

# Custom Modules
from database import init_db, seed_demo_data, fetch_all, fetch_one, execute_query
from auth import init_session, render_login_page, logout, log_audit
from hashing import generate_bytes_hash, generate_file_hash

# ==================== CONFIG ====================
st.set_page_config(
    page_title="ForensicVault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database & Session
init_db()
seed_demo_data()
init_session()

STORAGE_DIR = Path("evidence_storage")
STORAGE_DIR.mkdir(exist_ok=True)


# ==================== HELPERS ====================
def get_role_permissions(role):
    permissions = {
        'Administrator': ['Dashboard', 'Cases', 'Evidence', 'Chain of Custody',
                          'Reports', 'Analytics', 'User Management', 'Audit Logs', 'Settings'],
        'Investigator': ['Dashboard', 'Cases', 'Evidence', 'Chain of Custody',
                         'Reports', 'Analytics', 'Settings'],
        'Forensic Analyst': ['Dashboard', 'Evidence', 'Chain of Custody',
                             'Reports', 'Settings']
    }
    return permissions.get(role, [])


def format_file_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def generate_case_id():
    year = datetime.now().year
    unique = str(uuid.uuid4().int)[:4]
    return f"CR-{year}-{unique}"


def generate_evidence_id():
    return f"EV-{str(uuid.uuid4().int)[:8]}"


# ==================== PAGE: DASHBOARD ====================
def render_dashboard():
    st.markdown("# 🏠 Dashboard Overview")
    st.caption(f"Welcome back, **{st.session_state.full_name}** • Role: **{st.session_state.role}**")
    st.divider()

    # 1. QUICK ACTIONS AT THE TOP
    with st.container(border=True):
        st.markdown("### ⚡ Quick Actions")
        q1, q2, q3, q4 = st.columns(4)
        if q1.button("📁 New Case", use_container_width=True, type="primary"):
            st.session_state.current_page = "Cases"
            st.rerun()
        if q2.button("📤 Upload Evidence", use_container_width=True):
            st.session_state.current_page = "Evidence"
            st.rerun()
        if q3.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
        if q4.button("📄 Generate Report", use_container_width=True):
            st.session_state.current_page = "Reports"
            st.rerun()

    st.write("")

    # 2. KPI METRICS
    total_cases = fetch_one("SELECT COUNT(*) FROM cases")[0]
    active_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status IN ('New', 'Active')")[0]
    closed_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status = 'Closed'")[0]
    total_evidence = fetch_one("SELECT COUNT(*) FROM evidence")[0]
    verified_evidence = fetch_one("SELECT COUNT(*) FROM evidence WHERE verification_status = 'Verified'")[0]
    tampered_evidence = fetch_one("SELECT COUNT(*) FROM evidence WHERE verification_status = 'Tampered'")[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("📁 Total Cases", total_cases, delta="Active investigations")
    with c2:
        with st.container(border=True):
            st.metric("🔍 Active Cases", active_cases, delta=f"{closed_cases} closed")
    with c3:
        with st.container(border=True):
            st.metric("🗂️ Total Evidence", total_evidence, delta="Files stored")
    with c4:
        with st.container(border=True):
            delta_txt = f"⚠️ {tampered_evidence} tampered" if tampered_evidence else "✅ All verified"
            st.metric("✅ Verified", verified_evidence, delta=delta_txt,
                      delta_color="inverse" if tampered_evidence else "normal")

    st.write("")

    # 3. RECENT CASES & RECENT ACTIVITY
    col_left, col_right = st.columns([2, 1])

    with col_left:
        with st.container(border=True):
            st.markdown("### 📋 Recent Cases")
            cases = fetch_all(
                "SELECT case_id, case_title, crime_type, priority, status, assigned_officer FROM cases ORDER BY id DESC LIMIT 5"
            )
            if cases:
                df = pd.DataFrame([dict(c) for c in cases])
                df.columns = ["Case ID", "Title", "Type", "Priority", "Status", "Officer"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No cases registered yet.")

    with col_right:
        with st.container(border=True):
            st.markdown("### ⛓️ Recent Activity")
            logs = fetch_all("""
                SELECT c.action, u.username, c.timestamp 
                FROM custody_logs c 
                JOIN users u ON c.performed_by = u.id 
                ORDER BY c.id DESC LIMIT 5
            """)
            if logs:
                for log in logs:
                    st.markdown(f"**{log['action']}**")
                    st.caption(f"👤 {log['username']} • 🕒 {log['timestamp'][:16]}")
                    st.divider()
            else:
                st.info("No activity logged yet.")


# ==================== PAGE: CASES ====================
def render_cases():
    st.markdown("# 📁 Case Management")
    st.caption("Register and manage forensic investigation cases")
    st.divider()

    tab1, tab2 = st.tabs(["📋 **View All Cases**", "➕ **Create New Case**"])

    with tab1:
        with st.container(border=True):
            st.markdown("### 🔍 Filter Cases")
            col1, col2, col3 = st.columns(3)
            search = col1.text_input("Search", placeholder="Case ID, title, officer...")
            status_filter = col2.selectbox("Status", ["All", "New", "Active", "On Hold", "Closed", "Archived"])
            priority_filter = col3.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])

        query = "SELECT * FROM cases WHERE 1=1"
        params = []
        if search:
            query += " AND (case_id LIKE ? OR case_title LIKE ? OR assigned_officer LIKE ? OR victim LIKE ?)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp, sp])
        if status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        if priority_filter != "All":
            query += " AND priority = ?"
            params.append(priority_filter)
        query += " ORDER BY id DESC"

        cases = fetch_all(query, tuple(params))

        if cases:
            df = pd.DataFrame([dict(c) for c in cases])
            display_df = df[["case_id", "case_title", "crime_type", "priority", "status",
                             "assigned_officer", "victim", "date_filed"]].copy()
            display_df.columns = ["Case ID", "Title", "Type", "Priority", "Status",
                                  "Officer", "Victim", "Filed Date"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            with st.container(border=True):
                st.markdown("### 🔍 Case Inspector")
                selected = st.selectbox("Select case to view/edit",
                                        [c['case_id'] for c in cases],
                                        format_func=lambda x: f"{x} - {next(c['case_title'] for c in cases if c['case_id'] == x)}")

                if selected:
                    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (selected,))

                    ci1, ci2, ci3 = st.columns(3)
                    ci1.markdown(f"**Case ID:** `{case['case_id']}`")
                    ci1.markdown(f"**Crime Type:** {case['crime_type']}")
                    ci2.markdown(f"**Priority:** {case['priority']}")
                    ci2.markdown(f"**Status:** {case['status']}")
                    ci3.markdown(f"**Officer:** {case['assigned_officer']}")
                    ci3.markdown(f"**Victim:** {case['victim']}")

                    st.markdown(f"**Description:** {case['description']}")

                    with st.form(f"update_{selected}"):
                        st.markdown("#### ✏️ Update Case")
                        u1, u2, u3 = st.columns(3)
                        status_opts = ["New", "Active", "On Hold", "Closed", "Archived"]
                        pri_opts = ["Critical", "High", "Medium", "Low"]

                        new_status = u1.selectbox("Status", status_opts, 
                                                  index=status_opts.index(case['status']) if case['status'] in status_opts else 0)
                        new_priority = u2.selectbox("Priority", pri_opts, 
                                                    index=pri_opts.index(case['priority']) if case['priority'] in pri_opts else 0)
                        new_officer = u3.text_input("Officer", value=case['assigned_officer'])

                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            execute_query("""
                                UPDATE cases SET status = ?, priority = ?, assigned_officer = ? WHERE case_id = ?
                            """, (new_status, new_priority, new_officer, selected))
                            log_audit(st.session_state.username, "Case Updated", f"Updated {selected}: status={new_status}")
                            st.success(f"✅ Case {selected} updated!")
                            st.rerun()
        else:
            st.info("No cases match your filters.")

    with tab2:
        with st.form("create_case", clear_on_submit=True):
            st.markdown("### 📝 Register New Case")

            c1, c2 = st.columns(2)
            title = c1.text_input("Case Title *", placeholder="e.g., Corporate Data Breach")
            crime_type = c2.selectbox("Crime Type *",
                                      ["Ransomware", "Financial Fraud", "Identity Theft",
                                       "Data Breach", "Phishing", "Insider Threat", "Other"])

            c3, c4 = st.columns(2)
            victim = c3.text_input("Victim / Organization *", placeholder="Person or company name")
            officer = c4.text_input("Assigned Officer *", value=st.session_state.full_name)

            c5, c6 = st.columns(2)
            priority = c5.selectbox("Priority *", ["Critical", "High", "Medium", "Low"], index=2)
            status = c6.selectbox("Initial Status", ["New", "Active"])

            description = st.text_area("Case Description", placeholder="Detailed description...", height=100)

            if st.form_submit_button("🚀 Create Case", type="primary", use_container_width=True):
                if not all([title, victim, officer]):
                    st.error("⚠️ Please fill all required fields marked with *")
                else:
                    new_id = generate_case_id()
                    date_str = datetime.now().strftime('%b %d, %Y')
                    execute_query("""
                        INSERT INTO cases (case_id, case_title, crime_type, description, victim,
                                           assigned_officer, priority, status, date_filed, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_id, title, crime_type, description, victim, officer,
                          priority, status, date_str, st.session_state.user_id))
                    log_audit(st.session_state.username, "Case Created", f"Created {new_id}: {title}")
                    st.success(f"✅ Case **{new_id}** created successfully!")


# ==================== PAGE: EVIDENCE ====================
def render_evidence():
    st.markdown("# 🗂️ Evidence Management")
    st.caption("Upload, verify, and manage digital evidence with SHA-256 integrity")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📦 **Registry**", "📤 **Upload**", "🔐 **Verify Hash**"])

    with tab1:
        search = st.text_input("🔍 Search evidence", placeholder="ID, filename, description...")

        query = """
            SELECT e.evidence_id, e.case_id, e.evidence_type, e.original_filename, 
                   e.file_size, e.sha256_hash, e.verification_status, u.username, e.uploaded_at 
            FROM evidence e 
            JOIN users u ON e.uploaded_by = u.id 
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (e.evidence_id LIKE ? OR e.original_filename LIKE ? OR e.description LIKE ?)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])
        query += " ORDER BY e.id DESC"

        evidence = fetch_all(query, tuple(params))

        if evidence:
            df = pd.DataFrame([dict(e) for e in evidence])
            df['file_size'] = df['file_size'].apply(format_file_size)
            df['sha256_short'] = df['sha256_hash'].apply(lambda x: x[:16] + "...")
            display_df = df[["evidence_id", "case_id", "evidence_type", "original_filename",
                             "file_size", "sha256_short", "verification_status", "username", "uploaded_at"]].copy()
            display_df.columns = ["Evidence ID", "Case ID", "Type", "Filename",
                                  "Size", "SHA-256", "Status", "Uploader", "Uploaded"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No evidence uploaded yet.")

    with tab2:
        cases = fetch_all("SELECT case_id, case_title FROM cases ORDER BY id DESC")
        if not cases:
            st.warning("⚠️ Create a case first before uploading evidence.")
        else:
            with st.form("upload_evidence", clear_on_submit=True):
                st.markdown("### 📤 Upload New Evidence")

                case_options = {f"{c['case_id']} - {c['case_title']}": c['case_id'] for c in cases}
                selected = st.selectbox("Link to Case *", list(case_options.keys()))

                uploaded = st.file_uploader("Select Evidence File *", help="File will be hashed with SHA-256")

                ev_type = st.selectbox("Evidence Type", ["Image", "Video", "Document", "Audio", "Archive", "Other"])
                description = st.text_area("Description", placeholder="Describe the evidence...")

                if st.form_submit_button("🚀 Upload & Generate SHA-256", type="primary", use_container_width=True):
                    if not uploaded:
                        st.error("⚠️ Please select a file.")
                    else:
                        with st.spinner("🔐 Computing SHA-256 hash..."):
                            case_id = case_options[selected]
                            ev_id = generate_evidence_id()
                            file_bytes = uploaded.read()

                            sha256 = generate_bytes_hash(file_bytes)

                            ext = Path(uploaded.name).suffix
                            stored_name = f"{ev_id}{ext}"
                            stored_path = STORAGE_DIR / stored_name

                            with open(stored_path, "wb") as f:
                                f.write(file_bytes)

                            now = datetime.now().isoformat()
                            execute_query("""
                                INSERT INTO evidence (evidence_id, case_id, evidence_type, description,
                                                      original_filename, stored_filename, file_size,
                                                      sha256_hash, verification_status, uploaded_by, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Verified', ?, ?)
                            """, (ev_id, case_id, ev_type, description, uploaded.name,
                                  stored_name, len(file_bytes), sha256, st.session_state.user_id, now))

                            execute_query("""
                                INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp)
                                VALUES (?, 'Evidence Uploaded', ?, ?, ?)
                            """, (ev_id, st.session_state.user_id,
                                  f"Uploaded {uploaded.name} ({format_file_size(len(file_bytes))})", now))

                            log_audit(st.session_state.username, "Evidence Uploaded", f"Uploaded {ev_id} to {case_id}")

                        st.success(f"✅ Evidence **{ev_id}** uploaded successfully!")
                        st.code(sha256, language="text")

    with tab3:
        st.markdown("### 🔐 SHA-256 Integrity Verification")
        all_evidence = fetch_all("SELECT evidence_id, original_filename, sha256_hash, stored_filename FROM evidence ORDER BY id DESC")

        if not all_evidence:
            st.info("No evidence to verify.")
        else:
            ev_options = {f"{e['evidence_id']} - {e['original_filename']}": e for e in all_evidence}
            selected = st.selectbox("Select Evidence", list(ev_options.keys()))

            if selected:
                item = ev_options[selected]

                with st.container(border=True):
                    st.markdown("#### 📋 Evidence Details")
                    st.markdown(f"**Evidence ID:** `{item['evidence_id']}`")
                    st.markdown(f"**Original File:** {item['original_filename']}")
                    st.markdown("**Original SHA-256:**")
                    st.code(item['sha256_hash'], language="text")

                if st.button("🔍 Verify Integrity", type="primary", use_container_width=True):
                    with st.spinner("Computing current SHA-256..."):
                        file_path = STORAGE_DIR / item['stored_filename']

                        if not file_path.exists():
                            st.warning("⚠️ Demo file missing from disk. Upload a real file to test verification.")
                        else:
                            current_hash = generate_file_hash(file_path)

                            with st.container(border=True):
                                st.markdown("#### 🔬 Verification Result")
                                st.markdown("**Current SHA-256:**")
                                st.code(current_hash, language="text")

                                if current_hash == item['sha256_hash']:
                                    st.success("### ✅ INTEGRITY VERIFIED\nFile has NOT been modified.")
                                    execute_query("UPDATE evidence SET verification_status = 'Verified' WHERE evidence_id = ?", (item['evidence_id'],))
                                else:
                                    st.error("### ⚠️ TAMPERING DETECTED!\nHash mismatch - file has been modified.")
                                    execute_query("UPDATE evidence SET verification_status = 'Tampered' WHERE evidence_id = ?", (item['evidence_id'],))
                                
                                execute_query("""
                                    INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp)
                                    VALUES (?, 'Hash Verification', ?, ?, ?)
                                """, (item['evidence_id'], st.session_state.user_id, f"Result: {'Verified' if current_hash == item['sha256_hash'] else 'Tampered'}", datetime.now().isoformat()))


# ==================== PAGE: CHAIN OF CUSTODY ====================
def render_custody():
    st.markdown("# ⛓️ Chain of Custody")
    st.caption("Immutable log of all evidence handling actions")
    st.divider()

    logs = fetch_all("""
        SELECT c.timestamp, c.evidence_id, c.action, u.username, c.description
        FROM custody_logs c
        JOIN users u ON c.performed_by = u.id
        ORDER BY c.id DESC
    """)

    if logs:
        df = pd.DataFrame([dict(l) for l in logs])
        df.columns = ["Timestamp", "Evidence ID", "Action", "User", "Description"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No custody records logged yet.")


# ==================== PAGE: REPORTS ====================
def render_reports():
    st.markdown("# 📄 Report Generation")
    st.caption("Generate and export investigation reports")
    st.divider()

    report_type = st.selectbox("📊 Select Report Type", [
        "Case Summary Report",
        "Evidence Inventory Report",
        "Chain of Custody Audit"
    ])

    if report_type == "Case Summary Report":
        data = fetch_all("SELECT case_id, case_title, crime_type, priority, status, assigned_officer, victim, date_filed FROM cases")
    elif report_type == "Evidence Inventory Report":
        data = fetch_all("SELECT evidence_id, case_id, evidence_type, original_filename, file_size, sha256_hash, verification_status FROM evidence")
    else:
        data = fetch_all("SELECT c.timestamp, c.evidence_id, c.action, u.username, c.description FROM custody_logs c JOIN users u ON c.performed_by = u.id")

    if data:
        df = pd.DataFrame([dict(d) for d in data])
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download as CSV",
            data=csv,
            file_name=f"{report_type.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No data available for this report.")


# ==================== PAGE: ANALYTICS ====================
def render_analytics():
    st.markdown("# 📊 Analytics Dashboard")
    st.caption("Visual metrics powered by Plotly and SQLite.")
    st.divider()

    cases = fetch_all("SELECT crime_type, priority, status FROM cases")
    
    if not cases:
        st.info("Not enough data for analytics.")
        return

    df_cases = pd.DataFrame([dict(c) for c in cases])
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🍩 Cases by Crime Type")
            crime_counts = df_cases['crime_type'].value_counts().reset_index()
            crime_counts.columns = ['Crime Type', 'Count']
            fig1 = px.pie(crime_counts, values='Count', names='Crime Type', hole=0.5)
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("### 📊 Cases by Priority")
            pri_counts = df_cases['priority'].value_counts().reset_index()
            pri_counts.columns = ['Priority', 'Count']
            fig2 = px.bar(pri_counts, x='Priority', y='Count', color='Priority')
            st.plotly_chart(fig2, use_container_width=True)


# ==================== PAGE: USERS ====================
def render_users():
    st.markdown("# 👥 User Management")
    st.caption("Administrator panel to manage user accounts.")
    st.divider()

    users_list = fetch_all("SELECT id, first_name, last_name, username, email, role, status, created_at FROM users")
    if users_list:
        df_u = pd.DataFrame([dict(u) for u in users_list])
        st.dataframe(df_u, use_container_width=True, hide_index=True)


# ==================== PAGE: AUDIT LOGS ====================
def render_audit_logs():
    st.markdown("# 🛡️ System Audit Logs")
    st.caption("Security and access tracking.")
    st.divider()

    audits = fetch_all("SELECT username, action_type, action_description, timestamp FROM audit_logs ORDER BY id DESC LIMIT 500")
    if audits:
        df_au = pd.DataFrame([dict(a) for a in audits])
        df_au.columns = ["Username", "Action", "Description", "Timestamp"]
        st.dataframe(df_au, use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs yet.")


# ==================== PAGE: SETTINGS (FULL 5-TAB) ====================
def render_settings():
    st.markdown("# ⚙️ Account Settings")
    st.caption("Manage your profile, security, and preferences")
    st.divider()

    user = fetch_one("SELECT * FROM users WHERE id = ?", (st.session_state.user_id,))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 **Profile**", 
        "✏️ **Edit Profile**", 
        "🔐 **Security**", 
        "📊 **My Activity**",
        "ℹ️ **System Info**"
    ])

    # ---------- TAB 1: PROFILE VIEW ----------
    with tab1:
        with st.container(border=True):
            st.markdown("### 👤 Profile Information")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"<div style='text-align:center; font-size:80px;'>👤</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;'><b>{user['role']}</b></div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**Full Name:** {user['first_name']} {user['last_name']}")
                st.markdown(f"**Username:** `{user['username']}`")
                st.markdown(f"**Email:** {user['email']}")
                st.markdown(f"**Role:** {user['role']}")
                st.markdown(f"**Status:** ✅ {user['status'].title()}")
                st.markdown(f"**Member Since:** {user['created_at'][:10]}")
                if user['last_login']:
                    st.markdown(f"**Last Login:** {user['last_login'][:16]}")

    # ---------- TAB 2: EDIT PROFILE ----------
    with tab2:
        with st.container(border=True):
            st.markdown("### ✏️ Edit Profile Information")
            
            with st.form("edit_profile"):
                c1, c2 = st.columns(2)
                new_first = c1.text_input("First Name *", value=user['first_name'])
                new_last = c2.text_input("Last Name *", value=user['last_name'])
                
                new_username = st.text_input("Username *", value=user['username'])
                new_email = st.text_input("Email Address *", value=user['email'])
                
                st.info("⚠️ Note: If you change username, you will need to login again.")
                
                if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                    if not all([new_first, new_last, new_username, new_email]):
                        st.error("⚠️ Please fill all fields.")
                    else:
                        execute_query("""
                            UPDATE users 
                            SET first_name = ?, last_name = ?, username = ?, email = ?
                            WHERE id = ?
                        """, (new_first, new_last, new_username, new_email, user['id']))
                        
                        log_audit(st.session_state.username, "Profile Updated", "Profile details changed")
                        st.session_state.full_name = f"{new_first} {new_last}"
                        
                        if new_username != user['username']:
                            st.success("✅ Profile updated! Please logout and login again with new username.")
                        else:
                            st.session_state.username = new_username
                            st.success("✅ Profile updated successfully!")
                            st.rerun()

    # ---------- TAB 3: SECURITY ----------
    with tab3:
        with st.container(border=True):
            st.markdown("### 🔐 Change Password")
            
            with st.form("change_pw"):
                from hashing import verify_password, hash_password
                
                old = st.text_input("🔒 Current Password", type="password")
                new = st.text_input("🆕 New Password", type="password", placeholder="Min 8 characters")
                confirm = st.text_input("✅ Confirm New Password", type="password")

                if st.form_submit_button("🔒 Update Password", type="primary", use_container_width=True):
                    if not old or not new or not confirm:
                        st.error("⚠️ Please fill all fields.")
                    elif not verify_password(old, user['password_hash'], user['salt']):
                        st.error("❌ Current password is incorrect.")
                    elif new != confirm:
                        st.error("❌ New passwords do not match.")
                    elif len(new) < 8:
                        st.error("❌ Password must be at least 8 characters.")
                    else:
                        p_hash, salt = hash_password(new)
                        execute_query("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                                      (p_hash, salt, user['id']))
                        log_audit(user['username'], "Password Changed", "User changed password")
                        st.success("✅ Password updated successfully!")

    # ---------- TAB 4: MY ACTIVITY ----------
    with tab4:
        with st.container(border=True):
            st.markdown("### 📊 My Recent Activity")
            my_logs = fetch_all("SELECT action_type, action_description, timestamp FROM audit_logs WHERE username = ? ORDER BY id DESC LIMIT 10", (user['username'],))
            if my_logs:
                for log in my_logs:
                    st.markdown(f"**{log['action_type']}**")
                    st.caption(f"📝 {log['action_description']} • 🕒 {log['timestamp'][:16]}")
                    st.divider()
            else:
                st.info("No activity recorded.")

    # ---------- TAB 5: SYSTEM INFO ----------
    with tab5:
        with st.container(border=True):
            st.markdown("### ℹ️ System Information")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Application:** ForensicVault v1.0")
                st.markdown("**Framework:** Streamlit (Python)")
                st.markdown("**Database:** SQLite 3")
                st.markdown("**Encryption:** SHA-256")
            with col2:
                st.markdown("**Compliance:** ISO 27001, NIST")
                st.markdown("**Environment:** Production")
                st.markdown("**Server:** Localhost")
                st.markdown("**Status:** 🟢 Online")


# ==================== MAIN ROUTER ====================
def main():
    if not st.session_state.authenticated:
        render_login_page()
    else:
        with st.sidebar:
            st.markdown("# 🛡️ ForensicVault")
            st.caption(f"👤 {st.session_state.full_name}")
            st.caption(f"🎖️ {st.session_state.role}")
            st.divider()

            allowed = get_role_permissions(st.session_state.role)
            
            page_icons = {
                'Dashboard': '🏠', 'Cases': '📁', 'Evidence': '🗂️',
                'Chain of Custody': '⛓️', 'Reports': '📄', 'Analytics': '📊',
                'User Management': '👥', 'Audit Logs': '🛡️', 'Settings': '⚙️'
            }

            for page in allowed:
                icon = page_icons.get(page, '📄')
                if st.button(f"{icon} {page}", use_container_width=True, key=f"nav_{page}",
                             type="primary" if st.session_state.current_page == page else "secondary"):
                    st.session_state.current_page = page
                    st.rerun()

            st.write("")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                logout()

        page = st.session_state.current_page

        if page == 'Dashboard': render_dashboard()
        elif page == 'Cases': render_cases()
        elif page == 'Evidence': render_evidence()
        elif page == 'Chain of Custody': render_custody()
        elif page == 'Reports': render_reports()
        elif page == 'Analytics': render_analytics()
        elif page == 'User Management': render_users()
        elif page == 'Audit Logs': render_audit_logs()
        elif page == 'Settings': render_settings()

if __name__ == "__main__":
    main()