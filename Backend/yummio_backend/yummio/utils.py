import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from django.conf import settings

# Password hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# JWT functions
def create_jwt_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRY),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# Validation
def validate_signup_data(email: str, password: str) -> tuple[bool, str]:
    if not email or "@" not in email:
        return False, "Invalid email format"
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

def validate_login_data(email: str, password: str) -> tuple[bool, str]:
    if not email or not password:
        return False, "Email and password are required"
    return True, ""