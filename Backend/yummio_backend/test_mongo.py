from pymongo import MongoClient
from decouple import config

MONGO_URI = config('MONGO_URI', default='mongodb+srv://mandalriddhi89:Riddhi5002@cluster0.xp0m0qg.mongodb.net/yummio?retryWrites=true&w=majority&appName=Cluster0')
MONGO_DB_NAME = "yummio"

try:
    client = MongoClient(MONGO_URI)
    client.server_info()  # Test the connection
    db = client[MONGO_DB_NAME]
    print("Connected successfully!")
    print("Collections:", db.list_collection_names())
    client.close()
except Exception as e:
    print("Connection failed:", str(e))