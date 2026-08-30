"""
ForensicVault - Utility Module
Common helper functions used across the application.
"""

import re
import uuid
from datetime import datetime
from pathlib import Path


# ==================== ID GENERATORS ====================
def generate_case_id() -> str:
    """Generate a unique case ID like CR-2025-XXXX."""
    year = datetime.now().year
    unique_suffix = str(uuid.uuid4().int)[:4]
    return f"CR-{year}-{unique_suffix}"


def generate_evidence_id() -> str:
    """Generate a unique evidence ID like EV-XXXXXXXX."""
    return f"EV-{str(uuid.uuid4().int)[:8]}"


def generate_report_id() -> str:
    """Generate a unique report ID like RPT-XXXXXXXX."""
    return f"RPT-{str(uuid.uuid4().int)[:8]}"


# ==================== VALIDATORS ====================
def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> tuple:
    """
    Validate username. Returns (is_valid, error_message).
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


def check_password_strength(password: str) -> tuple:
    """
    Check password strength. Returns (is_strong, message, score).
    Score: 0 (very weak) to 4 (very strong).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters", 0
    
    score = 0
    checks = []
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        checks.append("lowercase letter")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        checks.append("uppercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        checks.append("number")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        checks.append("special character")
    
    if score < 3:
        return False, f"Password needs: {', '.join(checks)}", score
    
    return True, "Strong password ✓", score


# ==================== FORMATTERS ====================
def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format (e.g., '2.5 MB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ['KB', 'MB', 'GB', 'TB']:
        size_bytes /= 1024
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
    return f"{size_bytes:.2f} PB"


def format_timestamp(iso_string: str, fmt: str = "%b %d, %Y at %I:%M %p") -> str:
    """Convert ISO timestamp to friendly format."""
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return iso_string


def get_current_timestamp() -> str:
    """Get current timestamp as ISO string."""
    return datetime.now().isoformat()


# ==================== FILE UTILITIES ====================
def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename to prevent path traversal.
    """
    # Remove any directory path components
    filename = Path(filename).name
    # Replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    return filename


def get_file_category(filename: str) -> str:
    """Determine file category from extension."""
    ext = Path(filename).suffix.lower().lstrip('.')
    
    categories = {
        'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
        'video': ['mp4', 'mov', 'avi', 'mkv', 'wmv'],
        'audio': ['mp3', 'wav', 'ogg', 'flac', 'm4a'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
        'spreadsheet': ['xls', 'xlsx', 'csv'],
        'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
    }
    
    for category, extensions in categories.items():
        if ext in extensions:
            return category.capitalize()
    return "Other"


# ==================== PERMISSIONS ====================
ROLE_PERMISSIONS = {
    'Administrator': [
        'dashboard', 'cases', 'evidence', 'custody', 
        'reports', 'analytics', 'users', 'settings', 'audit'
    ],
    'Investigator': [
        'dashboard', 'cases', 'evidence', 'custody', 
        'reports', 'analytics', 'settings'
    ],
    'Forensic Analyst': [
        'dashboard', 'evidence', 'custody', 
        'reports', 'settings'
    ],
}


def has_permission(role: str, page: str) -> bool:
    """Check if a role has permission to access a page."""
    return page in ROLE_PERMISSIONS.get(role, [])


def get_allowed_pages(role: str) -> list:
    """Get list of pages a role can access."""
    return ROLE_PERMISSIONS.get(role, [])


# ==================== STATUS COLORS ====================
STATUS_COLORS = {
    # Case statuses
    'New': '🔵',
    'Active': '🟠',
    'On Hold': '🟡',
    'Closed': '🟢',
    'Archived': '⚫',
    # Priorities
    'Critical': '🔴',
    'High': '🟠',
    'Medium': '🟡',
    'Low': '🟢',
    # Evidence statuses
    'Verified': '✅',
    'Pending': '⏳',
    'Tampered': '⚠️',
}


def get_status_emoji(status: str) -> str:
    """Get emoji icon for a status."""
    return STATUS_COLORS.get(status, '⚪')