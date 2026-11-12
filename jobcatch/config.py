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
    
    # Base de données
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jobcatch.db")
    
    # Tarification & Abonnement (\$39/mois avec 3 jours d'essai gratuit)
    PRO_PLAN_PRICE: float = 39.00
    TRIAL_DAYS: int = 3
    
    # Passerelle de paiement (Stripe / Lemon Squeezy)
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    LEMON_SQUEEZY_API_KEY: str = os.getenv("LEMON_SQUEEZY_API_KEY", "")
    LEMON_SQUEEZY_STORE_ID: str = os.getenv("LEMON_SQUEEZY_STORE_ID", "")
    LEMON_SQUEEZY_CHECKOUT_URL: str = os.getenv("LEMON_SQUEEZY_CHECKOUT_URL", "https://jobcatch-ai.lemonsqueezy.com/checkout/buy/4bfc9c2d-14f7-45ef-ac35-cc1e23c80d42")
    
    # Compte Bancaire US de Réception (Lead Bank / Grey)
    LEAD_BANK_ROUTING: str = "101019644"
    LEAD_BANK_ACCOUNT_LAST4: str = "9479"
    LEAD_BANK_BENEFICIARY: str = "Assouman Abdoul Aziz Diabagate"
    
    # Intelligence Artificielle (Gemini / OpenAI pour l'optimisation ATS)
    AI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
