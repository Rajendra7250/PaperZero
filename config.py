import os
from dotenv import load_dotenv

load_dotenv()  # Reads from .env file if present

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-before-deploying")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///ecoflow.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5000").split(",")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"