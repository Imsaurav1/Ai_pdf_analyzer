from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserDB(BaseModel):
    email: EmailStr
    hashed_password: str
    created_at: datetime
    daily_requests: int = 0
    total_requests: int = 0
    last_request_date: str
    subscription_type: str = "free"