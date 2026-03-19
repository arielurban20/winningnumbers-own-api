import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:margarita12A%40@127.0.0.1:5432/lottery_api_own"
)