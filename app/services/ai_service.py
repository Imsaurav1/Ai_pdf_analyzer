from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

async def analyze_with_ai(text: str, document_type: str):

    if document_type == "resume":
        prompt = f"""
        You are an HR expert.
        Analyze the resume and return JSON:

        {{
          "summary": "",
          "strengths": [],
          "weaknesses": [],
          "suggestions": []
        }}

        Resume:
        {text}
        """
    else:
        prompt = f"Summarize clearly:\n{text}"

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return completion.choices[0].message.content