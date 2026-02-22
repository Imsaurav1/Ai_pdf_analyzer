import re
from app.config import TEXT_LIMIT

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text[:TEXT_LIMIT]