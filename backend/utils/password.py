""" Utility functions for password operations """

import bcrypt

def generate_salt() -> str:
    """ Generate a random salt """
    return bcrypt.gensalt().decode('utf-8')

def hash_password_with_salt(password: str, salt: str) -> str:
    """ Hash a password with a salt using bcrypt """
    return bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')

def verify_password_with_salt(password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash (salt is embedded in the hash)."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))