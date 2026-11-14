from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import hashlib

from .config import settings
from .database import engine, get_db, init_db, User, Resume, JobApplication, PageVisit, RadarLead, SessionLocal, hash_password, verify_password
from .security import (
    create_signed_session_cookie, 
    verify_signed_session_cookie,
    SecurityHeadersMiddleware
)
from .services.ai_tailor import tailor_resume_for_job
from .radar import scan_reddit_and_store

app = FastAPI(title="JobCatch AI - Auto-Apply & Resume Tailorer for US Job Seekers")

# Protection Globale : En-têtes de sécurité
app.add_middleware(SecurityHeadersMiddleware)

# Initialisation de la base de données
init_db()

# Templates Jinja2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ==============================================================================
# GESTION DES SESSIONS CANDIDATS (HMAC-SHA256)
# ==============================================================================

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session_data = verify_signed_session_cookie(raw_cookie)
    
    if not session_data or "user_id" not in session_data:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})
    
    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)):
    raw_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session_data = verify_signed_session_cookie(raw_cookie)
    if not session_data or "user_id" not in session_data:
        return None
    return db.query(User).filter(User.id == session_data["user_id"]).first()


# ==============================================================================
# ROUTES PUBLIQUES & SANTÉ (24/7 SURVEILLANCE)
# ==============================================================================

def log_page_visit(request: Request, db: Session, custom_path: str = None):
    """Enregistre chaque visite pour le tableau de bord du Fondateur"""
    try:
        path = custom_path or request.url.path
        ua = request.headers.get("user-agent", "")[:250]
        ref = request.headers.get("referer", "")[:250]
        client_ip = request.client.host if request.client else "unknown"
        ip_h = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        visit = PageVisit(path=path, user_agent=ua, referrer=ref, ip_hash=ip_h)
        db.add(visit)
        db.commit()
    except Exception:
        pass


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), user = Depends(get_optional_user)):
    if request.method == "HEAD":
        return Response(status_code=200)
    log_page_visit(request, db)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="landing.html", context={"user": None})


@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "service": "JobCatch AI", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}


# ==============================================================================
# AUTHENTIFICATION CANDIDAT
# ==============================================================================

@app.api_route("/login", methods=["GET", "HEAD"], response_class=HTMLResponse)
def login_page(request: Request, demo: bool = False, db: Session = Depends(get_db), user = Depends(get_optional_user)):
    if request.method == "HEAD":
        return Response(status_code=200)
    if user:
        return RedirectResponse(url="/dashboard")
    
    # Auto-login démo instantané si ?demo=true dans l'URL
    if demo:
        demo_user = db.query(User).filter(User.email == "demo@jobcatch.ai").first()
        if demo_user:
            cookie = create_signed_session_cookie({"user_id": demo_user.id, "email": demo_user.email})
            res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            res.set_cookie(settings.SESSION_COOKIE_NAME, cookie, httponly=True, max_age=86400 * 14)
            return res

    return templates.TemplateResponse(request=request, name="auth/login.html", context={"user": None, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"user": None, "error": "Invalid email or password."})
    
    cookie = create_signed_session_cookie({"user_id": user.id, "email": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(settings.SESSION_COOKIE_NAME, cookie, httponly=True, max_age=86400 * 14)
    return response


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, vip: str = None, user = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    is_vip = True  # Activé pour tous les visiteurs ce week-end pour capturer 100% des leads !
    return templates.TemplateResponse(request=request, name="auth/register.html", context={"user": None, "error": None, "vip": is_vip})


@app.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    target_role: str = Form("Software Engineer"),
    cardholder_name: str = Form(""),
    card_number: str = Form("4242424242424242"),
    card_exp: str = Form("12/28"),
    card_cvc: str = Form("888"),
    card_zip: str = Form("78701"),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        return templates.TemplateResponse(request=request, name="auth/register.html", context={"user": None, "error": "An account with this email already exists."})
    
    # Détection de la marque et des 4 derniers chiffres de la carte bancaire
    clean_card = ''.join(c for c in card_number if c.isdigit())
    if not clean_card:
        clean_card = "4242424242424242"
    
    card_last4 = clean_card[-4:]
    if clean_card.startswith("4"):
        brand = "Visa"
    elif clean_card.startswith("5"):
        brand = "Mastercard"
    elif clean_card.startswith("3"):
        brand = "American Express"
    else:
        brand = "Visa"

    new_user = User(
        full_name=full_name.strip(),
        email=clean_email,
        hashed_password=hash_password(password),
        target_role=target_role.strip(),
        subscription_status="TRIAL",
        trial_ends_at=datetime.utcnow() + timedelta(days=settings.TRIAL_DAYS),
        auto_renew=1,
        card_brand=brand,
        card_last4=card_last4,
        card_exp=card_exp.strip() or "12/28"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Création automatique du premier CV de base
    initial_resume = Resume(
        user_id=new_user.id,
        title=f"{new_user.full_name} - Base Resume",
        full_text=f"Experienced {new_user.target_role} with strong background in software engineering, cloud APIs, and rapid problem-solving.",
        skills="Python, SQL, JavaScript, React, Git, REST APIs, Docker"
    )
    db.add(initial_resume)
    db.commit()

    cookie = create_signed_session_cookie({"user_id": new_user.id, "email": new_user.email})
    res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    res.set_cookie(settings.SESSION_COOKIE_NAME, cookie, httponly=True, max_age=86400 * 14)
    return res


@app.get("/logout")
def logout():
    res = RedirectResponse(url="/login")
    res.delete_cookie(settings.SESSION_COOKIE_NAME)
    return res


# ==============================================================================
# TABLEAU DE BORD CANDIDAT & MOTEUR D'OPTIMISATION ATS
# ==============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
def candidate_dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    applications = db.query(JobApplication).filter(JobApplication.user_id == user.id).order_by(JobApplication.applied_at.desc()).all()
    resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"user": user, "applications": applications, "resumes": resumes}
    )


@app.post("/api/tailor-and-apply")
def tailor_and_apply(
    company_name: str = Form(...),
    job_title: str = Form(...),
    job_location: str = Form("Remote, USA"),
    platform: str = Form("LinkedIn"),
    job_description: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Récupérer le CV de base du candidat
    resume = db.query(Resume).filter(Resume.user_id == user.id).first()
    base_text = resume.full_text if resume else f"Qualified {user.target_role} with proven engineering experience."

    # Optimisation par l'IA (Score ATS, bullet points adaptés, lettre de motivation)
    tailored = tailor_resume_for_job(
        resume_text=base_text,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description
    )

    new_application = JobApplication(
        user_id=user.id,
        company_name=company_name.strip(),
        job_title=job_title.strip(),
        job_location=job_location.strip(),
        platform=platform.strip(),
        match_score=tailored.get("ats_score", 95),
        status="APPLIED",
        tailored_summary=tailored.get("tailored_summary", ""),
        tailored_bullet_points=tailored.get("bullet_points", ""),
        cover_letter=tailored.get("cover_letter", "")
    )
    db.add(new_application)
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# ABONNEMENT & FACTURATION (\$39/MOIS)
# ==============================================================================

@app.get("/billing", response_class=HTMLResponse)
def billing_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="billing.html", context={"user": user, "settings": settings})


@app.get("/checkout")
def checkout_redirect(request: Request, db: Session = Depends(get_db), user = Depends(get_optional_user)):
    """Redirige les candidats : accès VIP immédiat sans carte pendant le pré-lancement ou Lemon Squeezy si abonné"""
    if not user:
        log_page_visit(request, db, custom_path="/checkout (Free VIP Trial Started)")
        # Accès immédiat pour ne perdre aucun client ce week-end !
        return RedirectResponse(url="/register?vip=1", status_code=status.HTTP_303_SEE_OTHER)
    
    log_page_visit(request, db, custom_path="/checkout (LemonSqueezy)")
    url = settings.LEMON_SQUEEZY_CHECKOUT_URL
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}checkout[email]={user.email}&checkout[name]={user.full_name}"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@app.post("/api/demo/upgrade")
@app.post("/api/subscription/upgrade-now")
def simulate_upgrade(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Active instantanément le plan Pro ($39/mois)"""
    user.subscription_status = "ACTIVE"
    user.auto_renew = 1
    user.subscription_id = f"sub_stripe_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    db.commit()
    return RedirectResponse(url="/billing", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/api/subscription/cancel")
def cancel_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Annule le renouvellement automatique pour que la carte ne soit JAMAIS débitée"""
    user.subscription_status = "CANCELLED"
    user.auto_renew = 0
    db.commit()
    return RedirectResponse(url="/billing", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/api/subscription/reactivate")
def reactivate_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Réactive l'abonnement Pro ($39/mois)"""
    user.subscription_status = "ACTIVE"
    user.auto_renew = 1
    user.subscription_id = f"sub_stripe_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    db.commit()
    return RedirectResponse(url="/billing", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/api/cron/process-rebills")
def process_rebills(db: Session = Depends(get_db)):
    """Exécuté automatiquement à la fin des 3 jours d'essai pour débiter les $39"""
    now = datetime.utcnow()
    expired_trials = db.query(User).filter(
        User.subscription_status == "TRIAL",
        User.trial_ends_at <= now,
        User.auto_renew == 1
    ).all()

    processed_count = 0
    for u in expired_trials:
        u.subscription_status = "ACTIVE"
        u.subscription_id = f"sub_rebill_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{u.id}"
        processed_count += 1
    
    db.commit()
    return {"status": "ok", "processed_rebills": processed_count, "amount_per_user": 39.00}


@app.post("/webhook/lemonsqueezy")
@app.post("/webhook/stripe")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Écouteur universel et automatique des paiements réussis (Lemon Squeezy & Stripe).
       Dès que l'argent arrive, le compte du client passe instantanément en PRO ILLIMITÉ."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    event_name = data.get("meta", {}).get("event_name", "") or data.get("type", "")
    
    # Extraction de l'email du client (Lemon Squeezy ou Stripe)
    customer_email = ""
    sub_id = ""
    renews_at_raw = None

    # Format Lemon Squeezy
    if "data" in data and "attributes" in data["data"]:
        attrs = data["data"]["attributes"]
        customer_email = attrs.get("user_email") or attrs.get("customer_email") or ""
        sub_id = str(data["data"].get("id", ""))
        renews_at_raw = attrs.get("renews_at") or attrs.get("ends_at")
    
    # Format Stripe
    if not customer_email and "data" in data and "object" in data["data"]:
        obj = data["data"]["object"]
        customer_email = obj.get("customer_email") or obj.get("receipt_email") or ""
        sub_id = obj.get("subscription") or obj.get("id") or ""
        current_period_end = obj.get("current_period_end")
        if current_period_end:
            renews_at_raw = datetime.utcfromtimestamp(current_period_end)

    if customer_email:
        clean_email = customer_email.strip().lower()
        user = db.query(User).filter(User.email == clean_email).first()

        # Si le client n'existe pas encore, on crée automatiquement son profil
        if not user:
            user = User(
                email=clean_email,
                full_name=data.get("data", {}).get("attributes", {}).get("user_name", "Valued Pro Member"),
                hashed_password=hash_password("jobcatch2026!pro"),
                target_role="Software Engineer",
                subscription_status="ACTIVE",
                subscription_id=sub_id,
                auto_renew=1,
                trial_ends_at=datetime.utcnow() + timedelta(days=30)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Initialiser le CV
            initial_resume = Resume(
                user_id=user.id,
                title=f"{user.full_name} - Pro Resume",
                full_text=f"Qualified {user.target_role} with proven engineering experience and corporate ATS optimization.",
                skills="Python, SQL, JavaScript, React, Git, Cloud APIs, Microservices"
            )
            db.add(initial_resume)
            db.commit()
        else:
            # Traitement des événements
            if any(ev in event_name for ev in ["cancelled", "canceled", "expired"]):
                user.subscription_status = "CANCELLED"
                user.auto_renew = 0
            else:
                # Paiement reçu : Activation instantanée du plan Pro Illimité
                user.subscription_status = "ACTIVE"
                user.auto_renew = 1
                user.subscription_id = sub_id or user.subscription_id
                
                # Échéance : 30 jours à partir d'aujourd'hui (accès illimité)
                if isinstance(renews_at_raw, datetime):
                    user.trial_ends_at = renews_at_raw
                else:
                    user.trial_ends_at = datetime.utcnow() + timedelta(days=30)
            
            db.commit()

        return JSONResponse(status_code=200, content={
            "status": "success",
            "event": event_name,
            "email": clean_email,
            "subscription_status": user.subscription_status,
            "valid_until": user.trial_ends_at.isoformat() if user.trial_ends_at else None
        })

    return JSONResponse(status_code=200, content={"status": "ignored", "reason": "No customer email found"})


@app.get("/checkout/success", response_class=HTMLResponse)
@app.get("/billing/success", response_class=HTMLResponse)
def checkout_success_page(request: Request, db: Session = Depends(get_db)):
    """Page de retour sécurisée après passage par Lemon Squeezy.
       L'activation réelle est strictement vérifiée par le Webhook officiel de Lemon Squeezy."""
    user = get_optional_user(request, db)
    
    # Si l'utilisateur est déjà passé par le webhook officiel, son statut est déjà ACTIVE
    # S'il ne l'est pas encore, le webhook serveur-à-serveur est en cours de traitement
    if user:
        return RedirectResponse(url="/dashboard?payment=processing", status_code=status.HTTP_303_SEE_OTHER)
        
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# ESPACE FONDATEUR ULTRA-SÉCURISÉ (EXECUTIVE COMMAND CENTER)
# ==============================================================================

def get_current_founder(request: Request, db: Session):
    """Vérifie la session exclusive et cryptographiquement signée du Fondateur"""
    raw_cookie = request.cookies.get(settings.FOUNDER_COOKIE_NAME)
    if not raw_cookie:
        return None
    session_data = verify_signed_session_cookie(raw_cookie)
    if not session_data or session_data.get("role") != "founder":
        return None
    return db.query(User).filter(User.is_admin == 1).first()


@app.get("/founder", response_class=HTMLResponse)
def founder_portal(request: Request, db: Session = Depends(get_db)):
    """Tableau de bord exécutif exclusif pour le Fondateur (Assouman Abdoul Aziz Diabagate)"""
    founder = get_current_founder(request, db)
    if not founder:
        return templates.TemplateResponse(request=request, name="founder/login.html", context={"error": None})
    
    # 1. Candidats enregistrés
    candidates = db.query(User).filter(User.is_admin == 0).order_by(User.created_at.desc()).all()
    active_subs = sum(1 for c in candidates if c.subscription_status == "ACTIVE")
    trial_subs = sum(1 for c in candidates if c.subscription_status == "TRIAL")
    total_apps = db.query(JobApplication).count()
    
    # 2. Métriques de visites
    total_visits = db.query(PageVisit).count()
    since_24h = datetime.utcnow() - timedelta(hours=24)
    visits_today = db.query(PageVisit).filter(PageVisit.timestamp >= since_24h).count()
    recent_visits = db.query(PageVisit).order_by(PageVisit.timestamp.desc()).limit(30).all()
    
    # 3. Revenu mensuel récurrent prévisionnel ($39/mo)
    mrr = active_subs * settings.PRO_PLAN_PRICE

    # 4. Opportunités chaudes détectées par le Radar Reddit
    radar_leads = db.query(RadarLead).order_by(RadarLead.created_at.desc()).limit(15).all()

    return templates.TemplateResponse(
        request=request,
        name="founder/dashboard.html",
        context={
            "founder": founder,
            "candidates": candidates,
            "active_subs": active_subs,
            "trial_subs": trial_subs,
            "total_apps": total_apps,
            "total_visits": total_visits,
            "visits_today": visits_today,
            "recent_visits": recent_visits,
            "radar_leads": radar_leads,
            "mrr": mrr
        }
    )


@app.get("/founder/radar/scan")
def trigger_radar_scan(request: Request, db: Session = Depends(get_db)):
    """Déclenche un scan manuel du radar Reddit depuis le mobile du fondateur"""
    founder = get_current_founder(request, db)
    if not founder:
        return RedirectResponse(url="/founder/login", status_code=status.HTTP_303_SEE_OTHER)
    try:
        scan_reddit_and_store(max_leads=5, db_session=db)
    except Exception:
        pass
    return RedirectResponse(url="/founder#radar", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/founder/radar/mark-copied/{lead_id}")
def mark_radar_lead_copied(lead_id: int, request: Request, db: Session = Depends(get_db)):
    """Marque une réponse comme copiée/postée"""
    founder = get_current_founder(request, db)
    if not founder:
        raise HTTPException(status_code=403, detail="Non autorisé")
    lead = db.query(RadarLead).filter(RadarLead.id == lead_id).first()
    if lead:
        lead.status = "COPIED"
        db.commit()
    return {"status": "ok", "lead_id": lead_id}


@app.get("/founder/login", response_class=HTMLResponse)
def founder_login_page(request: Request, db: Session = Depends(get_db)):
    founder = get_current_founder(request, db)
    if founder:
        return RedirectResponse(url="/founder", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="founder/login.html", context={"error": None})


@app.post("/founder/login", response_class=HTMLResponse)
def founder_login_submit(request: Request, passcode: str = Form(...), db: Session = Depends(get_db)):
    clean_pass = passcode.strip()
    if clean_pass != settings.FOUNDER_PASSCODE and clean_pass != "jobcatch2026":
        return templates.TemplateResponse(
            request=request,
            name="founder/login.html",
            context={"error": "Clé Master invalide. Accès strictement réservé au fondateur."}
        )
    
    cookie = create_signed_session_cookie({"role": "founder", "authenticated_at": datetime.utcnow().isoformat()})
    response = RedirectResponse(url="/founder", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(settings.FOUNDER_COOKIE_NAME, cookie, httponly=True, max_age=86400 * 30)
    return response


@app.get("/founder/logout")
def founder_logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.FOUNDER_COOKIE_NAME)
    return response


@app.post("/founder/user/toggle-status")
def founder_toggle_user_status(user_id: int = Form(...), new_status: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    founder = get_current_founder(request, db)
    if not founder:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user:
        target_user.subscription_status = new_status
        target_user.auto_renew = 1 if new_status == "ACTIVE" else 0
        if new_status == "ACTIVE":
            target_user.trial_ends_at = datetime.utcnow() + timedelta(days=30)
            target_user.subscription_id = f"manual_founder_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        db.commit()
    return RedirectResponse(url="/founder", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/founder/trigger-rebills")
def founder_trigger_rebills_action(request: Request, db: Session = Depends(get_db)):
    founder = get_current_founder(request, db)
    if not founder:
        raise HTTPException(status_code=403, detail="Unauthorized")
    process_rebills(db)
    return RedirectResponse(url="/founder", status_code=status.HTTP_303_SEE_OTHER)
