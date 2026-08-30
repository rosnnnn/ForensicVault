"""
ForensicVault - Evidence & SHA-256 Integrity Verification Module
Handles File Upload, Storage, SHA-256 Hash Computation & Verification.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from database import fetch_all, fetch_one, execute_query
from hashing import generate_file_hash, generate_bytes_hash, verify_file_integrity
from utils import generate_evidence_id, get_current_timestamp, format_file_size, get_file_category
from auth import log_audit

STORAGE_DIR = Path("evidence_storage")


def render_evidence():
    STORAGE_DIR.mkdir(exist_ok=True)  # Ensure folder exists
    st.title("🗂️ Digital Evidence Management")
    st.caption("Tamper-proof file storage with real-time SHA-256 integrity verification.")
    st.divider()

    tab_view, tab_upload, tab_verify = st.tabs(["📦 Evidence Registry", "📤 Upload Evidence", "🔐 Verify SHA-256 Hash"])

    # ---------- TAB 1: REGISTRY ----------
    with tab_view:
        search = st.text_input("🔍 Search Evidence", placeholder="Evidence ID, Case ID, Description, Filename...")
        
        query = """
            SELECT e.evidence_id, e.case_id, e.evidence_type, e.original_filename, 
                   e.file_size, e.sha256_hash, e.verification_status, e.uploaded_at, u.username
            FROM evidence e
            JOIN users u ON e.uploaded_by = u.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (e.evidence_id LIKE ? OR e.case_id LIKE ? OR e.original_filename LIKE ? OR e.description LIKE ?)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp, sp])
        
        query += " ORDER BY e.id DESC"
        evidence_list = fetch_all(query, tuple(params))

        if evidence_list:
            df = pd.DataFrame([dict(e) for e in evidence_list])
            df["file_size"] = df["file_size"].apply(format_file_size)
            df.columns = ["Evidence ID", "Case ID", "Type", "Filename", "Size", "SHA-256 Hash", "Status", "Uploaded Date", "Uploader"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No evidence records found.")

    # ---------- TAB 2: UPLOAD EVIDENCE ----------
    with tab_upload:
        cases = fetch_all("SELECT case_id, case_title FROM cases ORDER BY id DESC")
        if not cases:
            st.warning("⚠️ No active cases found. Please create a case first before uploading evidence.")
        else:
            case_options = {f"{c['case_id']} - {c['case_title']}": c['case_id'] for c in cases}
            
            with st.form("upload_evidence_form"):
                st.write("Upload New Evidence File")
                selected_case = st.selectbox("Link to Case *", list(case_options.keys()))
                uploaded_file = st.file_uploader("Select Evidence File *", help="Files are saved securely and hashed using SHA-256")
                description = st.text_area("Evidence Description")
                
                submit_upload = st.form_submit_button("Upload & Compute SHA-256 Hash", use_container_width=True)

                if submit_upload:
                    if not uploaded_file or not selected_case:
                        st.error("Please select a file and link to a case.")
                    else:
                        case_id = case_options[selected_case]
                        evidence_id = generate_evidence_id()
                        original_filename = uploaded_file.name
                        file_bytes = uploaded_file.read()
                        
                        # 1. Compute SHA-256 Hash
                        sha256_hash = generate_bytes_hash(file_bytes)
                        
                        # 2. Save file safely
                        file_ext = Path(original_filename).suffix
                        stored_filename = f"{evidence_id}{file_ext}"
                        stored_path = STORAGE_DIR / stored_filename
                        
                        with open(stored_path, "wb") as f:
                            f.write(file_bytes)
                        
                        # 3. Store in DB
                        now = get_current_timestamp()
                        file_size = len(file_bytes)
                        file_category = get_file_category(original_filename)
                        
                        execute_query("""
                            INSERT INTO evidence (evidence_id, case_id, evidence_type, description,
                                                  original_filename, stored_filename, file_size,
                                                  sha256_hash, verification_status, uploaded_by, uploaded_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Verified', ?, ?)
                        """, (evidence_id, case_id, file_category, description,
                              original_filename, stored_filename, file_size,
                              sha256_hash, st.session_state.user_id, now))
                        
                        # 4. Chain of Custody Log
                        execute_query("""
                            INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp)
                            VALUES (?, 'Evidence Uploaded', ?, ?, ?)
                        """, (evidence_id, st.session_state.user_id, f"Uploaded {original_filename} ({format_file_size(file_size)})", now))
                        
                        log_audit(st.session_state.user_id, st.session_state.username, "Evidence Uploaded", f"Uploaded {evidence_id} to case {case_id}")
                        
                        st.success(f"✅ Evidence {evidence_id} uploaded successfully!")
                        st.code(f"SHA-256: {sha256_hash}", language="text")

    # ---------- TAB 3: VERIFY SHA-256 HASH ----------
    with tab_verify:
        st.subheader("🔐 Evidence Hash Integrity Inspector")
        all_ev = fetch_all("SELECT evidence_id, original_filename, sha256_hash FROM evidence ORDER BY id DESC")
        
        if not all_ev:
            st.info("No evidence available to verify.")
        else:
            ev_options = {f"{e['evidence_id']} ({e['original_filename']})": e['evidence_id'] for e in all_ev}
            selected_ev_key = st.selectbox("Select Evidence Item to Verify", list(ev_options.keys()))
            
            if selected_ev_key:
                ev_id = ev_options[selected_ev_key]
                ev_record = fetch_one("SELECT * FROM evidence WHERE evidence_id = ?", (ev_id,))
                
                st.write(f"**Stored Hash:** `{ev_record['sha256_hash']}`")
                
                if st.button("🔍 Perform SHA-256 Integrity Verification", use_container_width=True):
                    stored_file_path = STORAGE_DIR / ev_record['stored_filename']
                    result = verify_file_integrity(stored_file_path, ev_record['sha256_hash'])
                    
                    if result['is_valid']:
                        st.success(result['message'])
                        execute_query("UPDATE evidence SET verification_status = 'Verified', last_verified = ? WHERE evidence_id = ?", 
                                      (get_current_timestamp(), ev_id))
                    else:
                        st.error(result['message'])
                        execute_query("UPDATE evidence SET verification_status = 'Tampered', last_verified = ? WHERE evidence_id = ?", 
                                      (get_current_timestamp(), ev_id))
                    
                    # Log custody action
                    execute_query("""
                        INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp)
                        VALUES (?, 'Hash Verification', ?, ?, ?)
                    """, (ev_id, st.session_state.user_id, f"Verification result: {result['status']}", get_current_timestamp()))