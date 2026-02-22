from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)
db = client["pdf_analyzer"]

users_collection = db["users"]
analysis_collection = db["analysis"]