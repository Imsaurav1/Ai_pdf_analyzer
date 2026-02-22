from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)

# Use default DB from URI
db = client.get_default_database()

users_collection = db["users"]
analysis_collection = db["analysis"]