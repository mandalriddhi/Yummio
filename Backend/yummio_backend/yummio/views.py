from django.http import JsonResponse
from pymongo import MongoClient
from django.conf import settings
from .utils import hash_password, verify_password, create_jwt_token, verify_jwt_token, validate_signup_data, validate_login_data
import json
from datetime import datetime


# MongoDB connection (this is where the connection occurs)
try:
    client = MongoClient(settings.MONGO_URI)
    # Test the connection by listing collections
    client.server_info()  # This will raise an error if the connection fails
    db = client[settings.MONGO_DB_NAME]
    users_collection = db["users"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    raise Exception(f"MongoDB connection failed: {str(e)}")

def root(request):
    return JsonResponse({"message": "Welcome to Yummio API"}, status=200)

# Authentication middleware
def require_auth(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JsonResponse({"error": "Authentication required"}, status=401)
        token = token.split(" ")[1]
        payload = verify_jwt_token(token)
        if not payload:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)
        request.user_email = payload["email"]
        return view_func(request, *args, **kwargs)
    return wrapper

# Signup
def signup(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email, password = data.get("email"), data.get("password")
        
        is_valid, error = validate_signup_data(email, password)
        if not is_valid:
            return JsonResponse({"error": error}, status=400)
        
        if users_collection.find_one({"email": email}):
            return JsonResponse({"error": "Email already exists"}, status=400)
        
        hashed_password = hash_password(password)
        users_collection.insert_one({"email": email, "password": hashed_password, "history": []})
        token = create_jwt_token(email)
        return JsonResponse({"message": "Signup successful", "token": token}, status=201)
    return JsonResponse({"error": "Method not allowed"}, status=405)

# Login
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email, password = data.get("email"), data.get("password")
        
        is_valid, error = validate_login_data(email, password)
        if not is_valid:
            return JsonResponse({"error": error}, status=400)
        
        user = users_collection.find_one({"email": email})
        if not user or not verify_password(password, user["password"]):
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        
        token = create_jwt_token(email)
        return JsonResponse({"message": "Login successful", "token": token}, status=200)
    return JsonResponse({"error": "Method not allowed"}, status=405)

# History
@require_auth
def history(request):
    if request.method == "GET":
        user = users_collection.find_one({"email": request.user_email})
        return JsonResponse({"history": user["history"]}, status=200)
    
    elif request.method == "POST":
        data = json.loads(request.body)
        source, destination = data.get("source"), data.get("destination")
        if not source or not destination:
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
        return JsonResponse({"message": "History updated"}, status=201)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)