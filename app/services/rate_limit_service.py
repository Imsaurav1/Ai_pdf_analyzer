from datetime import date
from app.config import FREE_DAILY_LIMIT

async def check_rate_limit(user):

    today = str(date.today())

    if user.get("last_request_date") != today:
        await user.update({
            "daily_requests": 0,
            "last_request_date": today
        })

    if user.get("daily_requests", 0) >= FREE_DAILY_LIMIT:
        return False

    return True