from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import hashlib
import hmac

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
    
    # Statut d'abonnement (\$39/mois)
    subscription_status = Column(String(50), default="TRIAL")  # TRIAL, ACTIVE, CANCELLED
    trial_ends_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=settings.TRIAL_DAYS))
    subscription_id = Column(String(255), nullable=True)
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
            trial_ends_at=datetime.utcnow() + timedelta(days=3)
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


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
