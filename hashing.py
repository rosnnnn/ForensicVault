"""
ForensicVault - Cryptography Module
"""

import hashlib
import secrets


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    combined = (password + salt).encode("utf-8")
    return hashlib.sha256(combined).hexdigest(), salt


def verify_password(password, stored_hash, salt):
    computed, _ = hash_password(password, salt)
    return computed == stored_hash


def generate_bytes_hash(data_bytes: bytes) -> str:
    return hashlib.sha256(data_bytes).hexdigest()


def generate_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()