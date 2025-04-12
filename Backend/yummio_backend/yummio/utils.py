import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from functools import wraps

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
    
def validate_identifier(identifier: str) -> tuple[bool, str]:
    """Validate either email or phone number"""
    if not identifier:
        return False, "Email or phone number is required"
    
    # Simple email validation
    if "@" in identifier:
        if "." not in identifier.split("@")[1]:
            return False, "Invalid email format"
        return True, ""
    
    # Simple phone validation (adjust as needed)
    if identifier.isdigit() and len(identifier) >= 10:
        return True, ""
    
    return False, "Invalid email or phone number format"
    

# Validation
def validate_signup_data(identifier: str, password: str) -> tuple[bool, str]:
    is_valid, error = validate_identifier(identifier)
    if not is_valid:
        return False, error
        
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

def validate_login_data(email: str, password: str) -> tuple[bool, str]:
    if not email or not isinstance(email, str):
        return False, "Email is required"
    if not password or not isinstance(password, str):
        return False, "Password is required"
    return True, ""

# Authentication decorator
def require_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Extract token from Authorization header (assuming format: "Bearer <token>")
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'error': 'Authentication token required'}, status=401)
        
        # Split "Bearer" prefix if present
        token_parts = auth_header.split()
        if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
            return JsonResponse({'error': 'Invalid authorization header format. Use: Bearer <token>'}, status=401)
        
        token = token_parts[1]
        
        # Verify the token
        payload = verify_jwt_token(token)
        if not payload:
            return JsonResponse({'error': 'Invalid or expired token'}, status=401)
        
        # Attach email to request for use in the view
        request.user_email = payload.get('email')
        
        # Proceed to the view
        return view_func(request, *args, **kwargs)
    return wrapper