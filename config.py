import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    # OpenAI GPT
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Anthropic Claude
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
    
    # DeepSeek (OpenAI-compatible API)
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    # Default AI Model
    DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'openai')  # openai, claude, deepseek

config = Config()
