"""
ForensicVault - Cryptographic Module
"""
import hashlib
import secrets


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    combined = (password + salt).encode('utf-8')
    hashed = hashlib.sha256(combined).hexdigest()
    return hashed, salt


def verify_password(password, stored_hash, salt):
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash


def generate_bytes_hash(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()


def generate_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()