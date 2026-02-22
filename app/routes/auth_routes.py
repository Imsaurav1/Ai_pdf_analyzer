from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from datetime import datetime
import jwt

from app.models.user_model import UserCreate, UserLogin
from app.database import users_collection
from app.config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(email: str):
    return jwt.encode({"email": email}, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register")
async def register(user: UserCreate):

    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = pwd_context.hash(user.password)

    await users_collection.insert_one({
        "email": user.email,
        "hashed_password": hashed,
        "created_at": datetime.utcnow(),
        "daily_requests": 0,
        "total_requests": 0,
        "last_request_date": "",
        "subscription_type": "free"
    })

    return {"message": "User created"}

@router.post("/login")
async def login(user: UserLogin):

    db_user = await users_collection.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_token(user.email)
    return {"access_token": token}