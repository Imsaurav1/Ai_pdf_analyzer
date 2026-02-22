import os
import re
import jwt
from datetime import datetime, date
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from groq import Groq

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

MONGODB_URI     = os.getenv("MONGODB_URI")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
JWT_SECRET      = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM   = "HS256"
FREE_DAILY_LIMIT = 5
TEXT_LIMIT      = 6000

# ── Database ──────────────────────────────────────────────────────────────────
mongo_client        = AsyncIOMotorClient(MONGODB_URI)
db                  = mongo_client.get_default_database()
users_collection    = db["users"]
analysis_collection = db["analysis"]

# ── AI Client ─────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)

# ── Models ────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AnalyzeRequest(BaseModel):
    text: str
    document_type: str  # "resume" or "general"

# ── Helpers ───────────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(email: str) -> str:
    return jwt.encode({"email": email}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["email"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text[:TEXT_LIMIT]

async def analyze_with_ai(text: str, document_type: str) -> str:
    if document_type == "resume":
        prompt = f"""You are an HR expert.
Analyze the resume and return JSON:
{{"summary": "", "strengths": [], "weaknesses": [], "suggestions": []}}

Resume:
{text}"""
    else:
        prompt = f"Summarize clearly:\n{text}"

    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return completion.choices[0].message.content

async def check_rate_limit(user: dict) -> bool:
    today = str(date.today())
    if user.get("last_request_date") != today:
        await users_collection.update_one(
            {"email": user["email"]},
            {"$set": {"daily_requests": 0, "last_request_date": today}},
        )
        user["daily_requests"] = 0
    return user.get("daily_requests", 0) < FREE_DAILY_LIMIT

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.post("/register")
async def register(user: UserCreate):
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    await users_collection.insert_one({
        "email": user.email,
        "hashed_password": pwd_context.hash(user.password),
        "created_at": datetime.utcnow(),
        "daily_requests": 0,
        "total_requests": 0,
        "last_request_date": "",
        "subscription_type": "free",
    })
    return {"message": "User created"}

@app.post("login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {"access_token": create_token(user.email)}

# ── Analyze Route ─────────────────────────────────────────────────────────────
@app.post("/analyze")
async def analyze(data: AnalyzeRequest, token: str = Header(...)):
    email = get_current_user(token)
    user  = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not await check_rate_limit(user):
        raise HTTPException(status_code=429, detail="Daily limit reached")

    clean     = clean_text(data.text)
    ai_result = await analyze_with_ai(clean, data.document_type)

    await analysis_collection.insert_one({
        "user_email":    email,
        "document_type": data.document_type,
        "summary":       ai_result,
        "strengths":     [],
        "weaknesses":    [],
        "suggestions":   [],
        "tokens_used":   len(clean),
        "created_at":    datetime.utcnow(),
    })

    await users_collection.update_one(
        {"email": email},
        {"$inc": {"daily_requests": 1, "total_requests": 1}},
    )

    return {"result": ai_result}

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "AI PDF Analyzer Running"}
