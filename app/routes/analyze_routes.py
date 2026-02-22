from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import jwt

from app.models.analysis_model import AnalyzeRequest
from app.database import users_collection, analysis_collection
from app.services.ai_service import analyze_with_ai
from app.utils.text_cleaner import clean_text
from app.config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter()

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["email"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/analyze")
async def analyze(data: AnalyzeRequest, token: str):

    email = get_current_user(token)
    user = await users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    clean = clean_text(data.text)

    ai_result = await analyze_with_ai(clean, data.document_type)

    await analysis_collection.insert_one({
        "user_email": email,
        "document_type": data.document_type,
        "summary": ai_result,
        "strengths": [],
        "weaknesses": [],
        "suggestions": [],
        "tokens_used": len(clean),
        "created_at": datetime.utcnow()
    })

    await users_collection.update_one(
        {"email": email},
        {"$inc": {"daily_requests": 1, "total_requests": 1}}
    )

    return {"result": ai_result}