"""
ForensicVault - Database Module (SQLite)
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_DIR = Path("database")
DB_PATH = DB_DIR / "forensicvault.db"


def get_db():
    """Open SQLite connection successfully."""
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            case_title TEXT NOT NULL,
            crime_type TEXT NOT NULL,
            description TEXT,
            victim TEXT NOT NULL,
            assigned_officer TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            date_filed TEXT NOT NULL,
            created_by INTEGER NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE NOT NULL,
            case_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            description TEXT,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            sha256_hash TEXT NOT NULL,
            verification_status TEXT DEFAULT 'Verified',
            uploaded_by INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL,
            last_verified TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS custody_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT NOT NULL,
            action TEXT NOT NULL,
            performed_by INTEGER NOT NULL,
            description TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action_description TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def seed_demo_data():
    from hashing import hash_password

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.now().isoformat()
    date_str = datetime.now().strftime("%b %d, %Y")

    users = [
        ("Admin", "User", "anact", "admin@forensicvault.gov", "Anact@245", "Administrator"),
        ("Investigator", "User", "anactt", "investigator@forensicvault.gov", "Anact@245", "Investigator"),
        ("Analyst", "User", "anacttt", "analyst@forensicvault.gov", "Anact@245", "Forensic Analyst"),
    ]
    for fn, ln, un, em, pw, role in users:
        p_hash, salt = hash_password(pw)
        c.execute(
            """
            INSERT INTO users (first_name, last_name, username, email, password_hash, salt, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fn, ln, un, em, p_hash, salt, role, now),
        )

    cases = [
        ("CR-2025-001", "Corporate Ransomware Attack", "Ransomware", "Encrypted servers at TechCorp", "TechCorp Ltd", "Investigator User", "Critical", "Active", date_str, 1),
        ("CR-2025-002", "Bank Wire Fraud", "Financial Fraud", "Unauthorized transfers detected", "First National Bank", "Investigator User", "High", "Active", date_str, 1),
        ("CR-2025-003", "Identity Theft Case", "Identity Theft", "Fraud using stolen identity", "Jane Doe", "Analyst User", "Medium", "New", date_str, 1),
        ("CR-2025-004", "Hospital Data Breach", "Data Breach", "Patient records leaked", "MedSystems Inc", "Investigator User", "High", "Active", date_str, 1),
        ("CR-2025-005", "Phishing Campaign", "Phishing", "Mass phishing emails", "Govt. Agency", "Analyst User", "Low", "Closed", date_str, 1),
    ]
    c.executemany(
        """
        INSERT INTO cases (case_id, case_title, crime_type, description, victim, assigned_officer, priority, status, date_filed, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cases,
    )

    evidence = [
        ("EV-10001", "CR-2025-001", "Image", "Ransomware note screenshot", "ransom_note.png", "EV-10001_demo.bin", 102400, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "Verified", 2, now, now),
        ("EV-10002", "CR-2025-001", "Document", "Infected server logs", "system_logs.txt", "EV-10002_demo.bin", 204800, "a3f8c91d2e4b67890f1a2b3c4d5e6f7890a1b2c3d4e5f6789012345678901234", "Verified", 2, now, now),
        ("EV-10003", "CR-2025-002", "Document", "Bank transaction export", "bank_txns.pdf", "EV-10003_demo.bin", 512000, "b4c9d02e3f5a78901b2c3d4e5f67890a1b2c3d4e5f67890123456789012345bc", "Verified", 2, now, now),
        ("EV-10004", "CR-2025-003", "Image", "Fake ID used in fraud", "fake_id.jpg", "EV-10004_demo.bin", 76800, "c5d0e13f4a6b89012c3d4e5f6789012a3b4c5d6e7f890123456789012345cdef", "Pending", 3, now, None),
        ("EV-10005", "CR-2025-004", "Video", "CCTV clip of breach area", "cctv.mp4", "EV-10005_demo.bin", 5242880, "d6e1f24a5b7c90123d4e5f6789012a3b4c5d6e7f8901234567890123456defab", "Verified", 2, now, now),
    ]
    c.executemany(
        """
        INSERT INTO evidence (evidence_id, case_id, evidence_type, description, original_filename, stored_filename, file_size, sha256_hash, verification_status, uploaded_by, uploaded_at, last_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        evidence,
    )

    custody = [
        ("EV-10001", "Evidence Uploaded", 2, "File uploaded and hashed", now),
        ("EV-10001", "Hash Verified", 3, "Integrity verification passed", now),
        ("EV-10001", "Evidence Viewed", 3, "Analyst reviewed evidence", now),
        ("EV-10002", "Evidence Uploaded", 2, "Server logs uploaded", now),
        ("EV-10002", "Hash Verified", 2, "Auto-verify on upload", now),
        ("EV-10003", "Evidence Uploaded", 2, "Bank records uploaded", now),
        ("EV-10003", "Report Generated", 2, "Summary created for CR-2025-002", now),
        ("EV-10004", "Evidence Uploaded", 3, "Fake ID image uploaded", now),
        ("EV-10005", "Evidence Uploaded", 2, "CCTV footage uploaded", now),
        ("EV-10005", "Hash Verified", 3, "Video integrity confirmed", now),
    ]
    c.executemany(
        """
        INSERT INTO custody_logs (evidence_id, action, performed_by, description, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        custody,
    )

    audits = [
        ("anact", "Login", "Administrator logged in", now),
        ("anactt", "Case Created", "Created CR-2025-001", now),
        ("anacttt", "Evidence Verified", "Verified EV-10001", now),
        ("anact", "User Created", "System seeded demo users", now),
    ]
    c.executemany(
        """
        INSERT INTO audit_logs (username, action_type, action_description, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        audits,
    )

    conn.commit()
    conn.close()


def fetch_all(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_one(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def execute_query(query, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    last_id = cur.lastrowid
    conn.commit()
    conn.close()
    return last_id