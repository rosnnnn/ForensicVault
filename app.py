"""
ForensicVault - Main App
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime
import uuid

from database import init_db, seed_demo_data, fetch_all, fetch_one, execute_query
from auth import init_session, render_login_page, logout, log_audit
from hashing import generate_bytes_hash, generate_file_hash
from styles import apply_theme

st.set_page_config(page_title="ForensicVault", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
apply_theme()

init_db()
seed_demo_data()
init_session()

STORAGE_DIR = Path("evidence_storage")
STORAGE_DIR.mkdir(exist_ok=True)


def role_pages(role):
    mapping = {
        "Administrator": ["Dashboard", "Cases", "Evidence", "Chain of Custody", "Reports", "Analytics", "User Management", "Audit Logs", "Settings"],
        "Investigator": ["Dashboard", "Cases", "Evidence", "Chain of Custody", "Reports", "Analytics", "Settings"],
        "Forensic Analyst": ["Dashboard", "Evidence", "Chain of Custody", "Reports", "Settings"],
    }
    return mapping.get(role, ["Dashboard"])


def fmt_size(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} TB"


def new_case_id():
    return f"CR-{datetime.now().year}-{str(uuid.uuid4().int)[:4]}"


def new_evidence_id():
    return f"EV-{str(uuid.uuid4().int)[:8]}"


def page_dashboard():
    st.title("🏠 Dashboard Overview")
    st.caption(f"Welcome, **{st.session_state.full_name}** | Role: **{st.session_state.role}**")
    st.divider()

    with st.container(border=True):
        st.subheader("⚡ Quick Actions")
        a, b, c, d = st.columns(4)
        if a.button("📁 New Case", use_container_width=True, type="primary"):
            st.session_state.current_page = "Cases"; st.rerun()
        if b.button("📤 Upload Evidence", use_container_width=True):
            st.session_state.current_page = "Evidence"; st.rerun()
        if c.button("📊 Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"; st.rerun()
        if d.button("📄 Reports", use_container_width=True):
            st.session_state.current_page = "Reports"; st.rerun()

    total_cases = fetch_one("SELECT COUNT(*) FROM cases")[0]
    active_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status IN ('New','Active')")[0]
    closed_cases = fetch_one("SELECT COUNT(*) FROM cases WHERE status='Closed'")[0]
    total_ev = fetch_one("SELECT COUNT(*) FROM evidence")[0]
    verified = fetch_one("SELECT COUNT(*) FROM evidence WHERE verification_status='Verified'")[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cases", total_cases)
    m2.metric("Active Cases", active_cases, delta=f"{closed_cases} closed")
    m3.metric("Total Evidence", total_ev)
    m4.metric("Verified Evidence", verified)

    left, right = st.columns([2, 1])
    with left:
        with st.container(border=True):
            st.subheader("Recent Cases")
            rows = fetch_all("SELECT case_id, case_title, crime_type, priority, status, assigned_officer FROM cases ORDER BY id DESC LIMIT 5")
            if rows:
                df = pd.DataFrame([dict(r) for r in rows])
                df.columns = ["Case ID", "Title", "Type", "Priority", "Status", "Officer"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No cases yet.")

    with right:
        with st.container(border=True):
            st.subheader("Recent Activity")
            logs = fetch_all("""
                SELECT c.action, u.username, c.timestamp
                FROM custody_logs c JOIN users u ON c.performed_by=u.id
                ORDER BY c.id DESC LIMIT 5
            """)
            if logs:
                for log in logs:
                    st.markdown(f"**{log['action']}**")
                    st.caption(f"{log['username']} • {log['timestamp'][:16]}")
                    st.divider()
            else:
                st.info("No activity yet.")


def page_cases():
    st.title("📁 Case Management")
    st.divider()
    t1, t2 = st.tabs(["View Cases", "Create Case"])

    with t1:
        c1, c2, c3 = st.columns(3)
        search = c1.text_input("Search")
        status_f = c2.selectbox("Status", ["All", "New", "Active", "On Hold", "Closed"])
        priority_f = c3.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])

        q = "SELECT case_id, case_title, crime_type, priority, status, assigned_officer, victim, date_filed FROM cases WHERE 1=1"
        p = []
        if search:
            q += " AND (case_id LIKE ? OR case_title LIKE ? OR assigned_officer LIKE ? OR victim LIKE ?)"
            s = f"%{search}%"
            p += [s, s, s, s]
        if status_f != "All":
            q += " AND status=?"; p.append(status_f)
        if priority_f != "All":
            q += " AND priority=?"; p.append(priority_f)
        q += " ORDER BY id DESC"

        rows = fetch_all(q, tuple(p))
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            df.columns = ["Case ID", "Title", "Type", "Priority", "Status", "Officer", "Victim", "Date Filed"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No cases found.")

    with t2:
        with st.form("create_case"):
            a, b = st.columns(2)
            title = a.text_input("Case Title *")
            crime = b.selectbox("Crime Type", ["Ransomware", "Financial Fraud", "Identity Theft", "Data Breach", "Phishing", "Other"])
            victim = a.text_input("Victim/Org *")
            officer = b.text_input("Assigned Officer *", value=st.session_state.full_name)
            priority = a.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=2)
            status = b.selectbox("Status", ["New", "Active"])
            desc = st.text_area("Description")
            if st.form_submit_button("Create Case", type="primary", use_container_width=True):
                if not title or not victim or not officer:
                    st.error("Fill required fields.")
                else:
                    cid = new_case_id()
                    execute_query(
                        """
                        INSERT INTO cases (case_id, case_title, crime_type, description, victim, assigned_officer, priority, status, date_filed, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (cid, title, crime, desc, victim, officer, priority, status, datetime.now().strftime("%b %d, %Y"), st.session_state.user_id),
                    )
                    log_audit(st.session_state.username, "Case Created", f"Created {cid}")
                    st.success(f"Case {cid} created")
                    st.rerun()


def page_evidence():
    st.title("🗂️ Evidence Management")
    st.divider()
    t1, t2, t3 = st.tabs(["Registry", "Upload", "Verify Hash"])

    with t1:
        rows = fetch_all(
            """
            SELECT e.evidence_id, e.case_id, e.evidence_type, e.original_filename, e.file_size,
                   e.sha256_hash, e.verification_status, u.username, e.uploaded_at
            FROM evidence e JOIN users u ON e.uploaded_by=u.id
            ORDER BY e.id DESC
            """
        )
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            df["file_size"] = df["file_size"].apply(fmt_size)
            df["sha256_hash"] = df["sha256_hash"].apply(lambda x: x[:18] + "...")
            df.columns = ["Evidence ID", "Case ID", "Type", "Filename", "Size", "SHA-256", "Status", "Uploader", "Uploaded"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No evidence yet.")

    with t2:
        cases = fetch_all("SELECT case_id, case_title FROM cases ORDER BY id DESC")
        if not cases:
            st.warning("Create a case first.")
        else:
            with st.form("upload_form"):
                opts = {f"{c['case_id']} - {c['case_title']}": c["case_id"] for c in cases}
                selected = st.selectbox("Link to Case", list(opts.keys()))
                f = st.file_uploader("Choose file")
                etype = st.selectbox("Type", ["Image", "Document", "Video", "Audio", "Other"])
                desc = st.text_area("Description")
                if st.form_submit_button("Upload & Generate SHA-256", type="primary", use_container_width=True):
                    if not f:
                        st.error("Select a file")
                    else:
                        data = f.read()
                        digest = generate_bytes_hash(data)
                        eid = new_evidence_id()
                        stored = f"{eid}_{f.name}"
                        path = STORAGE_DIR / stored
                        path.write_bytes(data)
                        now = datetime.now().isoformat()
                        execute_query(
                            """
                            INSERT INTO evidence (evidence_id, case_id, evidence_type, description, original_filename, stored_filename, file_size, sha256_hash, verification_status, uploaded_by, uploaded_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Verified', ?, ?)
                            """,
                            (eid, opts[selected], etype, desc, f.name, stored, len(data), digest, st.session_state.user_id, now),
                        )
                        execute_query(
                            "INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp) VALUES (?, 'Evidence Uploaded', ?, ?, ?)",
                            (eid, st.session_state.user_id, f"Uploaded {f.name}", now),
                        )
                        log_audit(st.session_state.username, "Evidence Uploaded", f"{eid} -> {opts[selected]}")
                        st.success(f"Uploaded {eid}")
                        st.code(digest)

    with t3:
        rows = fetch_all("SELECT evidence_id, original_filename, stored_filename, sha256_hash FROM evidence ORDER BY id DESC")
        if not rows:
            st.info("No evidence to verify.")
        else:
            mp = {f"{r['evidence_id']} - {r['original_filename']}": r for r in rows}
            choice = st.selectbox("Select evidence", list(mp.keys()))
            item = mp[choice]
            st.code(item["sha256_hash"])
            if st.button("Verify Integrity", type="primary"):
                p = STORAGE_DIR / item["stored_filename"]
                if not p.exists():
                    st.warning("Demo metadata only (no physical demo binary). Upload a real file to test full verification.")
                else:
                    cur = generate_file_hash(p)
                    st.code(cur)
                    if cur == item["sha256_hash"]:
                        st.success("✅ INTEGRITY VERIFIED")
                        execute_query("UPDATE evidence SET verification_status='Verified', last_verified=? WHERE evidence_id=?", (datetime.now().isoformat(), item["evidence_id"]))
                    else:
                        st.error("⚠️ TAMPERING DETECTED")
                        execute_query("UPDATE evidence SET verification_status='Tampered', last_verified=? WHERE evidence_id=?", (datetime.now().isoformat(), item["evidence_id"]))
                    execute_query(
                        "INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp) VALUES (?, 'Hash Verification', ?, ?, ?)",
                        (item["evidence_id"], st.session_state.user_id, "Verification executed", datetime.now().isoformat()),
                    )


def page_custody():
    st.title("⛓️ Chain of Custody")
    st.divider()
    rows = fetch_all(
        """
        SELECT c.timestamp, c.evidence_id, c.action, u.username, c.description
        FROM custody_logs c JOIN users u ON c.performed_by=u.id
        ORDER BY c.id DESC
        """
    )
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df.columns = ["Timestamp", "Evidence ID", "Action", "User", "Description"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No custody logs.")


def page_reports():
    st.title("📄 Reports")
    st.divider()
    choice = st.selectbox("Report Type", ["Case Summary Report", "Evidence Inventory Report", "Chain of Custody Audit"])
    if choice == "Case Summary Report":
        rows = fetch_all("SELECT case_id, case_title, crime_type, priority, status, assigned_officer, victim, date_filed FROM cases ORDER BY id DESC")
    elif choice == "Evidence Inventory Report":
        rows = fetch_all("SELECT evidence_id, case_id, evidence_type, original_filename, file_size, sha256_hash, verification_status, uploaded_at FROM evidence ORDER BY id DESC")
    else:
        rows = fetch_all(
            """
            SELECT c.timestamp, c.evidence_id, c.action, u.username, c.description
            FROM custody_logs c JOIN users u ON c.performed_by=u.id ORDER BY c.id DESC
            """
        )

    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), file_name="report.csv", mime="text/csv", type="primary")
    else:
        st.info("No data.")


def page_analytics():
    st.title("📊 Analytics")
    st.divider()
    cases = fetch_all("SELECT crime_type, priority, status FROM cases")
    if not cases:
        st.info("No data.")
        return
    df = pd.DataFrame([dict(c) for c in cases])
    a, b = st.columns(2)
    with a:
        st.plotly_chart(px.pie(df, names="crime_type", title="Cases by Crime Type", hole=0.45), use_container_width=True)
    with b:
        st.plotly_chart(px.bar(df, x="priority", title="Cases by Priority", color="priority"), use_container_width=True)


def page_users():
    st.title("👥 User Management")
    st.divider()
    rows = fetch_all("SELECT first_name, last_name, username, email, role, status, last_login FROM users ORDER BY id")
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_audit():
    st.title("🛡️ Audit Logs")
    st.divider()
    rows = fetch_all("SELECT timestamp, username, action_type, action_description FROM audit_logs ORDER BY id DESC")
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df.columns = ["Timestamp", "Username", "Event Type", "Description"]
        st.dataframe(df, use_container_width=True, hide_index=True)


def page_settings():
    st.title("⚙️ Settings")
    st.divider()
    user = fetch_one("SELECT * FROM users WHERE id=?", (st.session_state.user_id,))
    t1, t2, t3 = st.tabs(["Profile", "Edit Profile", "Change Password"])

    with t1:
        st.write(f"**Name:** {user['first_name']} {user['last_name']}")
        st.write(f"**Username:** `{user['username']}`")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role']}")

    with t2:
        with st.form("edit_profile"):
            f, l = st.columns(2)
            fn = f.text_input("First Name", value=user["first_name"])
            ln = l.text_input("Last Name", value=user["last_name"])
            un = st.text_input("Username", value=user["username"])
            em = st.text_input("Email", value=user["email"])
            if st.form_submit_button("Save Profile", type="primary"):
                execute_query(
                    "UPDATE users SET first_name=?, last_name=?, username=?, email=? WHERE id=?",
                    (fn, ln, un, em, user["id"]),
                )
                st.session_state.full_name = f"{fn} {ln}"
                st.session_state.username = un
                st.success("Profile updated")
                st.rerun()

    with t3:
        with st.form("change_pw"):
            old = st.text_input("Current Password", type="password")
            new = st.text_input("New Password", type="password")
            conf = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update Password", type="primary"):
                from hashing import verify_password, hash_password
                if not verify_password(old, user["password_hash"], user["salt"]):
                    st.error("Current password incorrect")
                elif new != conf:
                    st.error("Passwords do not match")
                elif len(new) < 8:
                    st.error("Min 8 characters")
                else:
                    h, s = hash_password(new)
                    execute_query("UPDATE users SET password_hash=?, salt=? WHERE id=?", (h, s, user["id"]))
                    st.success("Password updated")


def main():
    if not st.session_state.authenticated:
        render_login_page()
        return

    with st.sidebar:
        st.markdown("## 🛡️ ForensicVault")
        st.caption(f"{st.session_state.full_name}")
        st.caption(f"Role: {st.session_state.role}")
        st.divider()
        pages = role_pages(st.session_state.role)
        for p in pages:
            if st.button(p, use_container_width=True, key=f"nav_{p}",
                         type="primary" if st.session_state.current_page == p else "secondary"):
                st.session_state.current_page = p
                st.rerun()
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout()

    page = st.session_state.current_page
    if page == "Dashboard":
        page_dashboard()
    elif page == "Cases":
        page_cases()
    elif page == "Evidence":
        page_evidence()
    elif page == "Chain of Custody":
        page_custody()
    elif page == "Reports":
        page_reports()
    elif page == "Analytics":
        page_analytics()
    elif page == "User Management":
        page_users()
    elif page == "Audit Logs":
        page_audit()
    elif page == "Settings":
        page_settings()


if __name__ == "__main__":
    main()