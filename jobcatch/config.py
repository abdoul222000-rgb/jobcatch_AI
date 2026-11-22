import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "JobCatch AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    
    # Sécurité des sessions (HMAC-SHA256)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jobcatch-super-secret-key-prod-2026-us-career-ai")
    SESSION_COOKIE_NAME: str = "jobcatch_session"
    SESSION_EXPIRE_DAYS: int = 14
    
    # Base de données (Compatible Vercel Serverless /tmp et Chemin Absolu Local)
    JOBCATCH_DATABASE_URL: str = os.getenv(
        "JOBCATCH_DATABASE_URL", 
        "sqlite:////tmp/jobcatch.db" if os.getenv("VERCEL") else f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'jobcatch.db')}"
    )
    DATABASE_URL: str = JOBCATCH_DATABASE_URL
    
    # Tarification & Abonnement (\$39/mois avec 3 jours d'essai gratuit)
    PRO_PLAN_PRICE: float = 39.00
    TRIAL_DAYS: int = 3
    
    # Passerelle de paiement officielle (Whop - Carte, Apple Pay & Google Pay)
    WHOP_CHECKOUT_URL: str = os.getenv("WHOP_CHECKOUT_URL", "https://whop.com/jobcatch-ai/jobcatch-ai-87")
    LEMON_SQUEEZY_CHECKOUT_URL: str = os.getenv("LEMON_SQUEEZY_CHECKOUT_URL", "https://whop.com/jobcatch-ai/jobcatch-ai-87")
    
    # Compte Bancaire US de Réception (Lead Bank / Grey)
    LEAD_BANK_ROUTING: str = "101019644"
    LEAD_BANK_ACCOUNT_LAST4: str = "9479"
    LEAD_BANK_BENEFICIARY: str = "Assouman Abdoul Aziz Diabagate"
    
    # Espace Fondateur Ultra-Sécurisé (Executive Command Center)
    FOUNDER_EMAIL: str = os.getenv("FOUNDER_EMAIL", "abdoul222000@gmail.com")
    FOUNDER_PASSCODE: str = os.getenv("FOUNDER_PASSCODE", "JobCatch2026!Aziz")
    FOUNDER_COOKIE_NAME: str = "jobcatch_founder_session"
    
    # Notifications Telegram pour le Radar Reddit
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Intelligence Artificielle (Gemini / OpenAI pour l'optimisation ATS)
    AI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
