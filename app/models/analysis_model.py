from pydantic import BaseModel
from datetime import datetime

class AnalyzeRequest(BaseModel):
    text: str
    document_type: str  # resume or general

class AnalysisDB(BaseModel):
    user_email: str
    document_type: str
    summary: str
    strengths: list
    weaknesses: list
    suggestions: list
    tokens_used: int
    created_at: datetime