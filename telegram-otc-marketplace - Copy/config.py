import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///marketplace.db')
    
    # Web App
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-me')
    WEB_APP_URL = os.getenv('WEB_APP_URL', 'http://localhost:5000')
    
    # Security
    ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []