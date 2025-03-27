import json
import logging
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render  # Added for rendering templates
from pymongo import MongoClient
from django.conf import settings
from .utils import hash_password, verify_password, create_jwt_token, verify_jwt_token, validate_signup_data, validate_login_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient(settings.MONGO_URI)
    # Test the connection by listing collections
    client.server_info()  # This will raise an error if the connection fails
    db = client[settings.MONGO_DB_NAME]
    users_collection = db["users"]
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    raise Exception(f"MongoDB connection failed: {str(e)}")

# Root endpoint
def root(request):
    logger.info("Root endpoint accessed")
    return render(request, 'home.html', {})

# Authentication middleware
def require_auth(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            logger.warning("Authentication failed: No token provided")
            return JsonResponse({"error": "Authentication required"}, status=401)
        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            logger.warning("Authentication failed: Invalid or expired token")
            return JsonResponse({"error": "Invalid or expired token"}, status=401)
        request.user_email = payload["email"]
        logger.info(f"User authenticated: {request.user_email}")
        return view_func(request, *args, **kwargs)
    return wrapper

# Signup endpoint
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email, password = data.get("email"), data.get("password")
            
            is_valid, error = validate_signup_data(email, password)
            if not is_valid:
                logger.warning(f"Signup failed: {error}")
                return JsonResponse({"error": error}, status=400)
            
            if users_collection.find_one({"email": email}):
                logger.warning(f"Signup failed: Email already exists - {email}")
                return JsonResponse({"error": "Email already exists"}, status=400)
            
            hashed_password = hash_password(password)
            users_collection.insert_one({"email": email, "password": hashed_password, "history": []})
            token = create_jwt_token(email)
            logger.info(f"Signup successful for user: {email}")
            return JsonResponse({"message": "Signup successful", "token": token}, status=201)
        except json.JSONDecodeError:
            logger.error("Signup failed: Invalid JSON in request body")
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"Signup failed: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    logger.warning("Signup failed: Method not allowed")
    return JsonResponse({"error": "Method not allowed"}, status=405)

# Login endpoint
def login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email, password = data.get("email"), data.get("password")
            
            is_valid, error = validate_login_data(email, password)
            if not is_valid:
                logger.warning(f"Login failed: {error}")
                return JsonResponse({"error": error}, status=400)
            
            user = users_collection.find_one({"email": email})
            if not user or not verify_password(password, user["password"]):
                logger.warning(f"Login failed: Invalid credentials for email - {email}")
                return JsonResponse({"error": "Invalid credentials"}, status=401)
            
            token = create_jwt_token(email)
            logger.info(f"Login successful for user: {email}")
            return JsonResponse({"message": "Login successful", "token": token}, status=200)
        except json.JSONDecodeError:
            logger.error("Login failed: Invalid JSON in request body")
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    logger.warning("Login failed: Method not allowed")
    return JsonResponse({"error": "Method not allowed"}, status=405)

# History endpoint
@require_auth
def history(request):
    if request.method == "GET":
        try:
            user = users_collection.find_one({"email": request.user_email})
            if not user:
                logger.warning(f"History retrieval failed: User not found - {request.user_email}")
                return JsonResponse({"error": "User not found"}, status=404)
            logger.info(f"History retrieved for user: {request.user_email}")
            return JsonResponse({"history": user["history"]}, status=200)
        except Exception as e:
            logger.error(f"History retrieval failed: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            source, destination = data.get("source"), data.get("destination")
            if not source or not destination:
                logger.warning("History update failed: Source and destination required")
                return JsonResponse({"error": "Source and destination required"}, status=400)
            
            history_entry = {
                "source": source,
                "destination": destination,
                "timestamp": datetime.utcnow().isoformat()
            }
            users_collection.update_one(
                {"email": request.user_email},
                {"$push": {"history": history_entry}}
            )
            logger.info(f"History updated for user: {request.user_email}")
            return JsonResponse({"message": "History updated"}, status=201)
        except json.JSONDecodeError:
            logger.error("History update failed: Invalid JSON in request body")
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"History update failed: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    
    logger.warning("History failed: Method not allowed")
    return JsonResponse({"error": "Method not allowed"}, status=405)