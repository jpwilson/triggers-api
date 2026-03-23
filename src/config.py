import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./triggers.db")
API_KEY = os.getenv("API_KEY", "dev-api-key")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
