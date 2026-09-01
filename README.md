# 🛡️ ForensicVault – Digital Evidence & Case Management System

A secure, Python-based web application for digital forensics, case management, and cryptographic evidence integrity verification.

## 🚀 Tech Stack
* **Language:** Python 3
* **Web Framework:** Streamlit (Pure Python UI)
* **Database:** SQLite 3 (`forensicvault.db`)
* **Data Processing & Analytics:** Pandas, Plotly Express
* **Cryptography & Security:** `hashlib` (SHA-256 evidence digests), salted password hashing

## ✨ Key Features
1. **Authentication & RBAC:** Multi-user login with role permissions (Administrator, Investigator, Forensic Analyst).
2. **Case Management:** Create, filter, update, and track investigation cases.
3. **Evidence Vault & SHA-256 Hashing:** Upload digital evidence with automatic SHA-256 digest calculation.
4. **Real-Time Integrity Verification:** Re-compute file hashes to detect any bit-level tampering.
5. **Chain of Custody:** Immutable audit log tracking all evidence access and modifications.
6. **Analytics & Reports:** Interactive Plotly charts and CSV/JSON report exports.
7. **System Audit Logging:** Complete security tracking for administrative evaluation.

## 🔑 Demo Credentials
* **Administrator:** `anact` / `Anact@245`
* **Investigator:** `anactt` / `Anact@245`
* **Forensic Analyst:** `anacttt` / `Anact@245`

## 💻 Local Setup
```bash
# 1. Clone the repository
git clone https://github.com/rosnnnn/ForensicVault.git
cd ForensicVault

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python database.py

# 5. Run Streamlit application
streamlit run app.py
