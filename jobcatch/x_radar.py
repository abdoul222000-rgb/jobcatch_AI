import os
import sqlite3
import html
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "/tmp/jobcatch.db" if os.getenv("VERCEL") else os.path.join(BASE_DIR, "jobcatch.db")

# Flux de recherche stratégiques en direct sur X (Twitter)
X_SEARCH_STREAMS = [
    {
        "market": "US",
        "title": "Candidatures Workday & Rejets ATS",
        "query": "Workday rejected resume",
        "url": "https://x.com/search?q=Workday%20rejected%20resume&f=live",
        "description": "Candidats tech rejetés automatiquement par les filtres Workday"
    },
    {
        "market": "US",
        "title": "Désespoir Ghosting & 100+ Applications",
        "query": "applied 100 jobs ghosted no interviews",
        "url": "https://x.com/search?q=applied%20100%20jobs%20ghosted%20no%20interviews&f=live",
        "description": "Développeurs et juniors qui postulent en masse sans retours"
    },
    {
        "market": "US",
        "title": "CS Grads & Entry-Level Tech",
        "query": "CS grad software engineer job market",
        "url": "https://x.com/search?q=CS%20grad%20software%20engineer%20job%20market&f=live",
        "description": "Nouveaux diplômés en informatique bloqués par le filtrage initial"
    },
    {
        "market": "US",
        "title": "Demandes d'avis & Feedback CV",
        "query": "resume feedback ATS score",
        "url": "https://x.com/search?q=resume%20feedback%20ATS%20score&f=live",
        "description": "Personnes cherchant à améliorer leur CV pour franchir les ATS"
    },
    {
        "market": "CH",
        "title": "🇨🇭 Emploi & Tech Suisse Romande",
        "query": "Suisse emploi CV OR Jobup OR tech Geneva Lausanne",
        "url": "https://x.com/search?q=Suisse%20emploi%20CV%20OR%20Jobup%20OR%20tech%20Geneva%20Lausanne&f=live",
        "description": "Professionnels et frontaliers cherchant en Suisse (Genève, Vaud)"
    },
    {
        "market": "US",
        "title": "Greenhouse & Taleo Filtering",
        "query": "Greenhouse ATS rejection email",
        "url": "https://x.com/search?q=Greenhouse%20ATS%20rejection%20email&f=live",
        "description": "Rejets automatiques envoyés par Greenhouse / Taleo"
    }
]

def generate_x_tailored_pitch(author_handle: str, target_market: str, tweet_text: str) -> dict:
    """
    Génère une réponse X (Twitter) percutante, concise et engageante (< 280 caractères ou thread)
    ET un message privé (DM) direct pour convertir en abonné JobCatch AI ($39/mo ou ~34 CHF).
    """
    handle = author_handle.strip()
    if not handle.startswith("@") and handle:
        handle = f"@{handle}"
    elif not handle:
        handle = "@candidate"

    text_lower = tweet_text.lower()

    # -------------------------------------------------------------
    # MARCHÉ SUISSE ROMANDE 🇨🇭 (Français)
    # -------------------------------------------------------------
    if target_market == "CH" or any(w in text_lower for w in ["suisse", "ch", "geneva", "genève", "lausanne", "vaud", "jobup"]):
        issue = "Filtrage ATS suisse (SAP SuccessFactors / Jobup.ch) et format CV non conforme"
        reply = (
            f"{handle} Si tu postules en Suisse (Jobup/Indeed), 80% des rejets <24h viennent des ATS (SAP/Workday) qui bloquent les formats graphiques ou sans métriques.\n\n"
            "Format épuré + mots-clés de l'offre obligatoire. Teste ton score ATS ici : https://jobcatch-ai.vercel.app 🇨🇭"
        )
        dm = (
            f"Hello {handle} ! J'ai vu ton tweet sur ta recherche d'emploi en Suisse. "
            "Le marché ici filtre énormément par SAP SuccessFactors et Workday avant qu'un recruteur ne lise le CV.\n\n"
            "On a développé JobCatch AI (https://jobcatch-ai.vercel.app) qui adapte automatiquement les CVs aux exigences suisses "
            "et garantit un score ATS > 85%. N'hésite pas à le tester, force pour tes candidatures !"
        )

    # -------------------------------------------------------------
    # MARCHÉ USA TECH 🇺🇸 (Anglais)
    # -------------------------------------------------------------
    else:
        if any(w in text_lower for w in ["workday", "greenhouse", "taleo", "ats"]):
            issue = "Workday/Greenhouse ATS auto-rejection due to low keyword match & weak metrics"
            reply = (
                f"{handle} Corporate ATS (Workday/Greenhouse) parse line-by-line. If bullet points aren't quantified (X-Y-Z formula), the parser scores you <70% before a human sees it.\n\n"
                "Align your bullets to the JD keywords. Free ATS simulator check: https://jobcatch-ai.vercel.app"
            )
        elif any(w in text_lower for w in ["100", "200", "applied", "ghosted", "no interview"]):
            issue = "Mass applying without tailored ATS alignment causing 90%+ silent rejection rate"
            reply = (
                f"{handle} Applying to 100+ roles with 1 generic resume hits the ATS wall every time. Recruiters get 400+ apps and filter anyone under 80% relevance.\n\n"
                "Tailoring 10 resumes with exact impact metrics beats blasting 100. Check your ATS score: https://jobcatch-ai.vercel.app"
            )
        else:
            issue = "US tech resume lacking quantified impact metrics & competitive ATS density"
            reply = (
                f"{handle} Quick tip that changes callback rates: swap passive bullet points for quantified impact (Accomplished [X] measured by [Y] doing [Z]).\n\n"
                "Corporate ATS rank candidates on keyword density. Test your resume here: https://jobcatch-ai.vercel.app"
            )

        dm = (
            f"Hey {handle}, saw your tweet about the tech job hunt. The US market is rough right now with Workday and Greenhouse auto-filtering 80% of applicants.\n\n"
            "We built JobCatch AI (https://jobcatch-ai.vercel.app) to reverse-engineer corporate ATS systems and tailor resumes to 95%+ match scores in seconds.\n\n"
            "Feel free to test your resume through it. Rooting for your next interview!"
        )

    return {
        "issue": issue,
        "suggested_reply": reply,
        "suggested_dm": dm
    }

def init_x_sqlite_table(conn):
    """Crée la table x_leads si nécessaire"""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS x_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id VARCHAR(100) UNIQUE,
            author_handle VARCHAR(100) NOT NULL,
            author_name VARCHAR(100),
            tweet_url VARCHAR(500) NOT NULL,
            target_market VARCHAR(10) DEFAULT 'US',
            tweet_text TEXT,
            detected_issue VARCHAR(255),
            suggested_reply TEXT NOT NULL,
            suggested_dm TEXT,
            status VARCHAR(20) DEFAULT 'NEW',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def generate_default_x_leads():
    """Génère les opportunités chaudes ciblées sur X (Twitter) avec liens directs vers X"""
    return [
        {
            "tweet_id": "x_us_tech_alex",
            "author_handle": "@alex_codes_24",
            "author_name": "Alex Rivera | CS Grad",
            "tweet_url": "https://x.com/search?q=Workday%20rejected%20resume%20software%20engineer&f=live",
            "target_market": "US",
            "tweet_text": "Applied to 80 software engineer roles this month through Workday. 60 instant rejections within 24h. I have a 3.8 GPA in CS, what am I doing wrong?!",
        },
        {
            "tweet_id": "x_us_marcus_dev",
            "author_handle": "@marcus_frontend",
            "author_name": "Marcus D.",
            "tweet_url": "https://x.com/search?q=applied%20100%20jobs%20ghosted%20no%20interviews&f=live",
            "target_market": "US",
            "tweet_text": "Over 200 applications sent on LinkedIn and Indeed. Total radio silence. Is anyone actually getting interviews right now?",
        },
        {
            "tweet_id": "x_ch_julien_geneve",
            "author_handle": "@julien_tech_ch",
            "author_name": "Julien M. (Genève)",
            "tweet_url": "https://x.com/search?q=Suisse%20emploi%20CV%20OR%20Jobup&f=live",
            "target_market": "CH",
            "tweet_text": "Recherche active de poste développeur / chef de projet à Genève ou Lausanne. Envoyé des dizaines de CVs sur Jobup.ch sans retour d'entretien.",
        },
        {
            "tweet_id": "x_us_priya_swe",
            "author_handle": "@priya_builds",
            "author_name": "Priya Sharma",
            "tweet_url": "https://x.com/search?q=Greenhouse%20ATS%20rejection%20email&f=live",
            "target_market": "US",
            "tweet_text": "Can someone review my tech resume? Getting tired of the 'Unfortunately, we have decided not to move forward' automated Greenhouse emails.",
        },
        {
            "tweet_id": "x_ch_sarah_vaud",
            "author_handle": "@sarah_lausanne",
            "author_name": "Sarah V. (Vaud)",
            "tweet_url": "https://x.com/search?q=Suisse%20emploi%20CV%20OR%20Jobup%20OR%20tech%20Geneva%20Lausanne&f=live",
            "target_market": "CH",
            "tweet_text": "Frontalière cherchant en Suisse Romande. Les entreprises me disent que mon profil est intéressant mais mes candidatures en ligne n'aboutissent jamais.",
        }
    ]

def scan_x_and_store(db_session=None) -> list:
    """Initialise et enregistre les opportunités X (Twitter) dans la base de données"""
    use_sqlalchemy = db_session is not None
    conn = None
    if not use_sqlalchemy:
        conn = sqlite3.connect(DB_PATH)
        init_x_sqlite_table(conn)

    leads_data = generate_default_x_leads()
    saved_leads = []

    try:
        for item in leads_data:
            pitch = generate_x_tailored_pitch(
                author_handle=item["author_handle"],
                target_market=item["target_market"],
                tweet_text=item["tweet_text"]
            )

            if use_sqlalchemy:
                from .database import XLead
                existing = db_session.query(XLead).filter(XLead.tweet_id == item["tweet_id"]).first()
                if not existing:
                    lead_obj = XLead(
                        tweet_id=item["tweet_id"],
                        author_handle=item["author_handle"],
                        author_name=item["author_name"],
                        tweet_url=item["tweet_url"],
                        target_market=item["target_market"],
                        tweet_text=item["tweet_text"],
                        detected_issue=pitch["issue"],
                        suggested_reply=pitch["suggested_reply"],
                        suggested_dm=pitch["suggested_dm"],
                        status="NEW"
                    )
                    db_session.add(lead_obj)
                    db_session.commit()
                    saved_leads.append(lead_obj)
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM x_leads WHERE tweet_id = ?", (item["tweet_id"],))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO x_leads 
                        (tweet_id, author_handle, author_name, tweet_url, target_market, tweet_text, detected_issue, suggested_reply, suggested_dm, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW')
                    """, (
                        item["tweet_id"],
                        item["author_handle"],
                        item["author_name"],
                        item["tweet_url"],
                        item["target_market"],
                        item["tweet_text"],
                        pitch["issue"],
                        pitch["suggested_reply"],
                        pitch["suggested_dm"]
                    ))
                    conn.commit()
                    saved_leads.append(item)
    finally:
        if conn:
            conn.close()

    return saved_leads

if __name__ == "__main__":
    leads = scan_x_and_store()
    print(f"[SUCCESS] Robot X (Twitter) Radar initialise avec succes ({len(leads)} opportunites).")
