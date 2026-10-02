import os
from pathlib import Path

# Disable C-extensions in SQLAlchemy to support Windows environments with DLL Application Control policies
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    
    # Instance directory for SQLite database
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{INSTANCE_DIR / 'finance.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini AI API Key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
    
    # Application settings
    APP_NAME = "Personal Finance Advisor"
    APP_SUBTITLE = "Understand your money. Plan smarter. Save better."
