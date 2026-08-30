"""
ForensicVault - Case Management Module
Create, View, Filter, and Manage Investigation Cases.
"""

import streamlit as st
import pandas as pd
from database import fetch_all, fetch_one, execute_query
from utils import generate_case_id, get_current_timestamp, get_status_emoji
from auth import log_audit


def render_cases():
    st.title("📁 Case Management")
    st.caption("Register and manage digital forensic investigation cases.")
    st.divider()

    tab_view, tab_create = st.tabs(["📋 View All Cases", "➕ Register New Case"])

    # ---------- TAB 1: VIEW CASES ----------
    with tab_view:
        col_s, col_f1, col_f2 = st.columns([2, 1, 1])
        search = col_s.text_input("🔍 Search Cases", placeholder="Case ID, Title, Officer...")
        status_filter = col_f1.selectbox("Filter Status", ["All", "New", "Active", "On Hold", "Closed", "Archived"])
        priority_filter = col_f2.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"])

        query = "SELECT * FROM cases WHERE 1=1"
        params = []

        if status_filter != "All":
            query += " AND status = ?"
            params.append(status_filter)
        
        if priority_filter != "All":
            query += " AND priority = ?"
            params.append(priority_filter)

        if search:
            query += " AND (case_id LIKE ? OR case_title LIKE ? OR assigned_officer LIKE ? OR victim LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param, s_param])

        query += " ORDER BY id DESC"
        cases = fetch_all(query, tuple(params))

        if cases:
            df = pd.DataFrame([dict(c) for c in cases])
            # Format dataframe
            display_df = df[["case_id", "case_title", "crime_type", "priority", "status", "assigned_officer", "victim", "date_filed"]].copy()
            display_df.columns = ["Case ID", "Title", "Type", "Priority", "Status", "Officer", "Victim/Org", "Filed Date"]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Detail Inspector
            st.subheader("🔍 Case Inspector")
            selected_case_id = st.selectbox("Select Case to Inspect / Update", [c["case_id"] for c in cases])
            
            if selected_case_id:
                case_detail = fetch_one("SELECT * FROM cases WHERE case_id = ?", (selected_case_id,))
                
                with st.expander(f"Details for {case_detail['case_id']}: {case_detail['case_title']}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Crime Type:** {case_detail['crime_type']}")
                    c1.write(f"**Victim/Org:** {case_detail['victim']}")
                    c2.write(f"**Priority:** {case_detail['priority']}")
                    c2.write(f"**Status:** {case_detail['status']}")
                    c3.write(f"**Assigned Officer:** {case_detail['assigned_officer']}")
                    c3.write(f"**Location:** {case_detail['location']}")

                    st.write(f"**Description:** {case_detail['description']}")

                    # Update Status Form
                    with st.form(f"update_case_{case_detail['case_id']}"):
                        st.write("Update Case Status / Priority")
                        u1, u2, u3 = st.columns(3)
                        new_status = u1.selectbox("New Status", ["New", "Active", "On Hold", "Closed", "Archived"], index=["New", "Active", "On Hold", "Closed", "Archived"].index(case_detail['status']))
                        new_priority = u2.selectbox("New Priority", ["Critical", "High", "Medium", "Low"], index=["Critical", "High", "Medium", "Low"].index(case_detail['priority']))
                        new_officer = u3.text_input("Reassign Officer", value=case_detail['assigned_officer'])
                        
                        btn_update = st.form_submit_button("Update Case")
                        if btn_update:
                            now = get_current_timestamp()
                            execute_query("""
                                UPDATE cases SET status = ?, priority = ?, assigned_officer = ?, updated_at = ? WHERE case_id = ?
                            """, (new_status, new_priority, new_officer, now, selected_case_id))
                            log_audit(st.session_state.user_id, st.session_state.username, "Case Updated", f"Updated {selected_case_id} status to {new_status}")
                            st.success(f"Case {selected_case_id} updated successfully!")
                            st.rerun()
        else:
            st.info("No cases matching filters.")

    # ---------- TAB 2: CREATE CASE ----------
    with tab_create:
        with st.form("create_case_form"):
            st.write("Register New Forensic Case")
            col1, col2 = st.columns(2)
            
            title = col1.text_input("Case Title *")
            crime_type = col2.selectbox("Crime Type *", [
                "Ransomware", "Financial Fraud", "Identity Theft", "Data Breach", 
                "Phishing", "Insider Threat", "Malware", "Digital Extortion", "Other"
            ])
            
            victim = col1.text_input("Victim / Organization *")
            location = col2.text_input("Incident Location")
            
            priority = col1.selectbox("Priority *", ["Critical", "High", "Medium", "Low"], index=2)
            officer = col2.text_input("Assigned Officer *", value=st.session_state.full_name)
            
            description = st.text_area("Case Description")
            
            submit_case = st.form_submit_button("Create Case", use_container_width=True)
            
            if submit_case:
                if not title or not victim or not officer:
                    st.error("Please fill in all required fields marked with *")
                else:
                    new_case_id = generate_case_id()
                    now = get_current_timestamp()
                    
                    execute_query("""
                        INSERT INTO cases (case_id, case_title, crime_type, description, location, victim,
                                           assigned_officer, priority, status, created_by, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?, ?)
                    """, (new_case_id, title, crime_type, description, location, victim, officer, priority, st.session_state.user_id, now, now))
                    
                    log_audit(st.session_state.user_id, st.session_state.username, "Case Created", f"Created new case {new_case_id}: {title}")
                    st.success(f"✅ Case {new_case_id} created successfully!")
                    st.rerun()