from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import hashlib
import hmac
import os

from .config import settings

# Configuration du moteur SQLite
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
# SÉCURITÉ MOT DE PASSE (SHA-256 + SALT)
# ==============================================================================

def hash_password(password: str) -> str:
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


# ==============================================================================
# MODÈLES DE DONNÉES JOBCATCH AI
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    target_role = Column(String(255), default="Software Engineer")
    target_location = Column(String(255), default="Remote, USA")
    
    # Rôle & Sécurité Fondateur
    is_admin = Column(Integer, default=0)  # 1 = Fondateur / Administrateur Exclusif, 0 = Candidat
    
    # Statut d'abonnement ($39/mois) & Paiement par Carte Obligatoire
    subscription_status = Column(String(50), default="TRIAL")  # TRIAL, ACTIVE, CANCELLED
    trial_ends_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=settings.TRIAL_DAYS))
    subscription_id = Column(String(255), nullable=True)
    auto_renew = Column(Integer, default=1)  # 1 = Renouvellement automatique $39/mo, 0 = Annulé
    
    # Données Carte Bancaire enregistrée pour le débit automatique après 3 jours
    card_brand = Column(String(50), default="Visa")
    card_last4 = Column(String(4), default="4242")
    card_exp = Column(String(10), default="12/28")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="Default Resume")
    full_text = Column(Text, nullable=False)
    skills = Column(String(500), default="Python, FastAPI, SQL, React, Cloud, Git")
    years_experience = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_location = Column(String(255), default="Remote, USA")
    salary_range = Column(String(100), default="$75,000 - $95,000/yr")
    platform = Column(String(50), default="LinkedIn")  # LinkedIn, Indeed, Handshake, ZipRecruiter
    
    # Score de correspondance ATS (Applicant Tracking System)
    match_score = Column(Integer, default=85)  # 0 à 100%
    status = Column(String(50), default="APPLIED")  # APPLIED, INTERVIEW, OFFER, REVIEWING
    
    tailored_summary = Column(Text, nullable=True)
    tailored_bullet_points = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="applications")


class PageVisit(Base):
    __tablename__ = "page_visits"

    id = Column(Integer, primary_key=True, index=True)
    ip_hash = Column(String(64), nullable=True)
    path = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=True)
    referrer = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ==============================================================================
# GESTION DES SESSIONS & INITIALISATION
# ==============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_demo_data(db):
    """Crée un utilisateur de démo réaliste pour les prospects américains"""
    demo_user = db.query(User).filter(User.email == "demo@jobcatch.ai").first()
    if not demo_user:
        demo_user = User(
            email="demo@jobcatch.ai",
            hashed_password=hash_password("jobcatch2026"),
            full_name="Alex Rivera",
            target_role="Full-Stack Developer",
            target_location="Remote / Austin, TX",
            subscription_status="TRIAL",
            trial_ends_at=datetime.utcnow() + timedelta(days=3),
            auto_renew=1,
            card_brand="Visa",
            card_last4="4242",
            card_exp="12/28"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        # CV de base
        demo_resume = Resume(
            user_id=demo_user.id,
            title="Alex Rivera - Full Stack Resume (Base)",
            full_text="Experienced Full-Stack Developer with 2+ years building web applications in Python, FastAPI, React, and PostgreSQL. Passionate about automated testing, scalable cloud microservices, and AI integrations. Built 3 production SaaS products handling over 10,000 daily active users.",
            skills="Python, FastAPI, SQL, PostgreSQL, React, TypeScript, Docker, Git, REST APIs, TailwindCSS",
            years_experience=2
        )
        db.add(demo_resume)

        # Candidatures de démonstration avec scores ATS élevés
        mock_jobs = [
            ("Junior Python / FastAPI Engineer", "Stripe", "San Francisco, CA (Remote)", "$95,000 - $115,000/yr", "LinkedIn", 96, "INTERVIEW"),
            ("Full-Stack Software Developer", "Carta", "Austin, TX (Hybrid)", "$85,000 - $105,000/yr", "Indeed", 92, "APPLIED"),
            ("Backend API Specialist", "DoorDash", "Remote, USA", "$90,000 - $110,000/yr", "Handshake", 94, "REVIEWING"),
            ("Junior Software Engineer", "Shopify", "Remote, USA", "$80,000 - $100,000/yr", "LinkedIn", 98, "OFFER"),
            ("Cloud Application Developer", "Datadog", "New York, NY (Remote)", "$90,000 - $115,000/yr", "ZipRecruiter", 89, "APPLIED")
        ]

        for title, company, loc, sal, plat, score, stat in mock_jobs:
            app = JobApplication(
                user_id=demo_user.id,
                job_title=title,
                company_name=company,
                job_location=loc,
                salary_range=sal,
                platform=plat,
                match_score=score,
                status=stat,
                tailored_summary=f"Optimized profile specifically highlighting microservices and automated API integration for {company}.",
                tailored_bullet_points="• Built asynchronous REST APIs serving 10k+ requests/sec with 99.9% uptime.\n• Implemented automated CI/CD deployment pipelines on Docker & Linux cloud.\n• Optimized database query bottlenecks reducing response latency by 42%.",
                cover_letter=f"Dear Hiring Team at {company},\n\nI am thrilled to apply for the {title} role. With hands-on experience delivering scalable Python and cloud architectures, I am excited about the opportunity to contribute immediately to your engineering roadmap.",
                applied_at=datetime.utcnow() - timedelta(hours=mock_jobs.index((title, company, loc, sal, plat, score, stat)) * 5)
            )
            db.add(app)
        
        db.commit()

        # Compte Fondateur & Administrateur Exclusif
        founder = db.query(User).filter(User.email == settings.FOUNDER_EMAIL).first()
        if not founder:
            founder = User(
                email=settings.FOUNDER_EMAIL,
                hashed_password=hash_password(settings.FOUNDER_PASSCODE),
                full_name="Assouman Abdoul Aziz Diabagate",
                target_role="Founder & CEO",
                target_location="Abidjan & US Market",
                is_admin=1,
                subscription_status="ACTIVE",
                auto_renew=1,
                card_brand="Push/AfrikaBanque",
                card_last4="8752",
                card_exp="12/30"
            )
            db.add(founder)
            db.commit()


def auto_migrate():
    """Vérifie et ajoute les colonnes manquantes dans SQLite sans casser les données"""
    try:
        with engine.connect() as conn:
            result = conn.execute(Base.metadata.tables["users"].select().limit(0))
    except Exception:
        pass
    
    # Pragma check direct pour SQLite
    if "sqlite" in settings.DATABASE_URL:
        import sqlite3
        db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(users)")
            existing_cols = {row[1] for row in c.fetchall()}
            
            columns_to_ensure = {
                "is_admin": "INTEGER DEFAULT 0",
                "card_brand": "VARCHAR(50) DEFAULT 'Visa'",
                "card_last4": "VARCHAR(4) DEFAULT '4242'",
                "card_exp": "VARCHAR(10) DEFAULT '12/28'",
                "auto_renew": "INTEGER DEFAULT 1",
                "subscription_status": "VARCHAR(50) DEFAULT 'TRIAL'",
                "subscription_id": "VARCHAR(255)"
            }
            for col, col_type in columns_to_ensure.items():
                if col not in existing_cols and existing_cols:
                    try:
                        c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass
            conn.commit()
            conn.close()


def init_db():
    auto_migrate()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
