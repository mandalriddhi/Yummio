from datetime import datetime
from django.conf import settings
from pymongo import MongoClient
from typing import Optional, List, Dict, Any
from .utils import hash_password, verify_password
import logging


logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

class User:
    """
    Represents a user in the system.
    MongoDB collection: users
    """
    collection = db["users"]

    def __init__(
        self,
        identifier: str,  # Can be email or phone
        password: str,
        name: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        is_email: bool = True
    ):
       self.identifier = identifier
       self.is_email = is_email
       self.password = password
       self.name = name
       self.history = history or []

    @classmethod
    def create(cls, identifier: str, password: str, name: Optional[str] = None) -> 'User':
        """Create a new user in the database"""
        # Hash the password before storing
        hashed_password = hash_password(password)
        is_email = "@" in identifier
        
        user_data = {
            "identifier": identifier,
            "is_email": is_email,
            "password": hashed_password,
            "history": []
        }
        
        # Only add name if provided
        if name and name.strip():
            user_data["name"] = name.strip()
            
        try:
            result = cls.collection.insert_one(user_data)
            if not result.inserted_id:
                raise Exception("Failed to create user")
                
            return cls(
                identifier=identifier,
                password=hashed_password,
                name=name,
                is_email=is_email
            )
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise  # Re-raise the exception for the view to handle
        
    @classmethod
    def find_by_identifier(cls, identifier: str) -> Optional['User']:
        """Find a user by email or phone"""
        try:
            user_data = cls.collection.find_one({"identifier": identifier})
            if not user_data:
                return None
                
            return cls(
                identifier=user_data["identifier"],
                password=user_data["password"],
                name=user_data.get("name"),
                history=user_data.get("history", []),
                is_email=user_data.get("is_email", True)
            )
        except Exception as e:
            logger.error(f"Error finding user: {str(e)}")
            return None    
        

    def add_history(self, source: str, destination: str) -> bool:
        """Add a search to user's history"""
        try:
            history_entry = {
                "source": source,
                "destination": destination,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = self.collection.update_one(
                {"identifier": self.identifier},
                {"$push": {"history": history_entry}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding history for user {self.identifier}: {str(e)}")
            return False
    

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find a user by email"""
        try:
            user_data = cls.collection.find_one({"email": email})
            if not user_data:
                return None
                
            return cls(
                email=user_data["email"],
                password=user_data["password"],  # This is the hashed password
                name=user_data.get("name"),
                history=user_data.get("history", [])
            )
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None

    def verify_password(self, provided_password: str) -> bool:
        """Verify the user's password"""
        try:
            return verify_password(provided_password, self.password)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False


class Item:
    """
    Represents an item in the system.
    MongoDB collection: items
    """
    collection = db["items"]

    def __init__(
        self,
        name: str,
        description: str,
        created_by: str,
        created_at: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow().isoformat()

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        created_by: str
    ) -> 'Item':
        """Create a new item in the database"""
        item_data = {
            "name": name.strip(),
            "description": description.strip(),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": created_by
        }
        result = cls.collection.insert_one(item_data)
        if result.inserted_id:
            return cls(**item_data)
        raise Exception("Failed to create item")

    # @classmethod
    # def find_all(cls) -> List[Dict[str, Any]]:
    #     """Find all items in the database"""
    #     items = list(cls.collection.find({}, {"_id": 0}))  # Exclude MongoDB's _id field
    #     return items


class AuthToken:
    """
    Handles JWT token operations (though tokens are stateless)
    """
    @staticmethod
    def create_token(email: str) -> str:
        from .utils import create_jwt_token
        return create_jwt_token(email)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        from .utils import verify_jwt_token
        return verify_jwt_token(token)