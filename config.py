# config.py
from dotenv import load_dotenv
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

class Config:
    # Use DATABASE URI (required name for Flask-SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///hospital.db")
    
    # Track modifications (Boolean)
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False") == "True"
    
    # Secret key for sessions
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")