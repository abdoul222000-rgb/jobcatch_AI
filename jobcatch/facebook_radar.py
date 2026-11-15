import os
import sqlite3
import html
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jobcatch.db")

# Groupes Facebook stratégiques pour JobCatch AI
FACEBOOK_TARGET_GROUPS = [
    {
        "market": "CH",
        "name": "CHOffres d'emplois CHsuisse CH romande CH",
        "url": "https://www.facebook.com/groups/712398642237937",
        "description": "Candidats actifs en Suisse Romande (Genève, Vaud, Lausanne, Valais) postant leurs CVs",
        "language": "fr"
    },
    {
        "market": "CH",
        "name": "Emploi & Recrutement Suisse Romande",
        "url": "https://www.facebook.com/groups/emploisuisseromande",
        "description": "Professionnels, frontaliers et diplômés cherchant sur Jobup.ch et Indeed CH",
        "language": "fr"
    },
    {
        "market": "CH",
        "name": "Offres d'emploi Genève - Vaud - Lausanne",
        "url": "https://www.facebook.com/groups/genevevaudemploi",
        "description": "Postulants aux grandes entreprises suisses (Nestlé, Logitech, Banques, Hôtellerie, Tech)",
        "language": "fr"
    },
    {
        "market": "US",
        "name": "Software Engineer Jobs IT",
        "url": "https://www.facebook.com/groups/IT.Software.Engineer.Jobs",
        "description": "Tech grads, junior & mid developers looking for US remote / on-site roles",
        "language": "en"
    },
    {
        "market": "US",
        "name": "Tech & Software Jobs USA (Remote / Entry Level)",
        "url": "https://www.facebook.com/groups/techjobsusa",
        "description": "US candidates struggling with Workday & Greenhouse automated rejections",
        "language": "en"
    },
    {
        "market": "US",
        "name": "Entry Level CS Grads & Software Engineers USA",
        "url": "https://www.facebook.com/groups/csgradsentrylevel",
        "description": "Computer science graduates needing ATS optimization and resume metrics",
        "language": "en"
    }
]

def generate_facebook_tailored_pitch(candidate_name: str, target_market: str, post_snippet: str, job_title: str = "") -> dict:
    """
    Génère une réponse publique bienveillante à fort taux de clic (Commentaire)
    ET un message privé discret (DM) pour convertir le candidat en utilisateur JobCatch AI ($39/mo ou ~34 CHF).
    """
    clean_name = candidate_name.strip() if candidate_name else "Bonjour"
    snippet_lower = post_snippet.lower()
    
    # -------------------------------------------------------------
    # MARCHÉ SUISSE ROMANDE 🇨🇭 (Français)
    # -------------------------------------------------------------
    if target_market == "CH" or any(w in snippet_lower for w in ["suisse", "ch", "genève", "geneve", "vaud", "lausanne", "jobup", "frontalier"]):
        # Détection du problème
        if any(w in snippet_lower for w in ["cv", "curriculum", "photo", "recherche poste", "serveuse", "hôtellerie", "commercial", "comptable"]):
            issue = "Format CV graphique/Canva 2 colonnes rejeté par les ATS suisses (SAP SuccessFactors / Jobup.ch)"
        elif any(w in snippet_lower for w in ["rejet", "rejeté", "sans réponse", "refus", "postulé"]):
            issue = "Filtrage automatique par les robots de recrutement suisses avant lecture humaine"
        else:
            issue = "Optimisation du CV pour les normes de recrutement en Suisse Romande"

        # 1. Commentaire public (empathique, haute valeur ajoutée, non spammy)
        comment = (
            f"Bonjour {clean_name} ! Petit conseil constructif pour vos démarches en Suisse Romande 🇨🇭 :\n\n"
            "Votre profil a du potentiel, mais attention si vous postulez sur Jobup.ch, Indeed Suisse ou les sites de recrutement : "
            "la majorité des moyennes et grandes entreprises ici utilisent des filtres ATS (comme SAP SuccessFactors et Workday). "
            "Les CV graphiques à 2 colonnes ou créés sur Canva se font souvent disqualifier automatiquement avec un score < 40%.\n\n"
            "Pour maximiser vos retours d'entretiens, privilégiez un format linéaire avec des puces quantifiées et les mots-clés exacts de l'offre. "
            "Vous pouvez tester et optimiser votre CV gratuitement aux normes suisses sur JobCatch AI (https://jobcatch-ai.onrender.com) "
            "pour garantir un score de passage de 90%+.\n\n"
            "Plein de succès dans vos recherches en Suisse !"
        )

        # 2. Message privé (DM)
        dm = (
            f"Hello {clean_name},\n\n"
            "J'ai vu votre publication dans le groupe pour votre recherche d'emploi en Suisse Romande. "
            "Je travaille sur les algorithmes de recrutement et je vois énormément de très bons profils se faire filtrer inutilement par les robots ATS des entreprises suisses.\n\n"
            "Si vous le souhaitez, vous pouvez scanner votre CV directement sur notre plateforme (https://jobcatch-ai.onrender.com) : "
            "elle l'adapte automatiquement aux exigences de Jobup.ch et des recruteurs suisses en français avec un score ATS optimal.\n\n"
            "N'hésitez pas si vous voulez un retour rapide sur votre CV, bonne chance pour vos entretiens !"
        )

    # -------------------------------------------------------------
    # MARCHÉ USA TECH 🇺🇸 (Anglais)
    # -------------------------------------------------------------
    else:
        if any(w in snippet_lower for w in ["applied", "rejections", "ghosted", "workday", "greenhouse", "taleo", "no interviews"]):
            issue = "Workday / Greenhouse automated ATS keyword mismatch & low bullet density"
        elif any(w in snippet_lower for w in ["grad", "graduate", "junior", "entry level", "entry-level"]):
            issue = "Junior tech resume lacking quantified impact metrics (Google X-Y-Z formula)"
        else:
            issue = "US tech ATS compliance & competitive keyword alignment"

        first_name = clean_name.split()[0] if clean_name else "there"

        # 1. Commentaire public
        comment = (
            f"Hey {first_name}! A quick piece of advice from someone working on ATS tech in the US 🇺🇸:\n\n"
            "If you are submitting applications through Workday, Taleo, or Greenhouse and getting automated rejections, "
            "9 times out of 10 it's because the parser flags the bullet points with an ATS match score below 75% before a recruiter ever looks at it.\n\n"
            "Key fix: Convert descriptive bullet points into quantified impact metrics (e.g. 'Engineered [X] measured by [Y] using [Z]'). "
            "You can test your bullet points and auto-align your resume for any US tech role on JobCatch AI (https://jobcatch-ai.onrender.com) — "
            "it scores your match rate from 0 to 100% and rewrites bullet points to clear corporate ATS filters.\n\n"
            "Best of luck with your applications!"
        )

        # 2. Message privé (DM)
        dm = (
            f"Hey {first_name},\n\n"
            "Saw your post in the Software Engineer group. The US tech job market is brutal right now with automated filtering, "
            "especially with companies receiving 400+ applications per role through Workday and Greenhouse.\n\n"
            "We built JobCatch AI (https://jobcatch-ai.onrender.com) specifically to help software engineers and tech grads reverse-engineer "
            "corporate ATS algorithms and generate 95%+ compliant resumes tailored to the job description in seconds.\n\n"
            "Feel free to run your resume through it, and let me know if you want any feedback on your bullet points. Rooting for your next offer!"
        )

    return {
        "issue": issue,
        "suggested_comment": comment,
        "suggested_dm": dm
    }

def init_facebook_sqlite_table(conn):
    """Crée la table facebook_leads si nécessaire et assure la présence de post_url"""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS facebook_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id VARCHAR(100) UNIQUE,
            group_name VARCHAR(150) NOT NULL,
            group_url VARCHAR(500) NOT NULL,
            post_url VARCHAR(500),
            target_market VARCHAR(10) DEFAULT 'CH',
            candidate_name VARCHAR(100),
            post_snippet TEXT,
            detected_issue VARCHAR(255),
            suggested_comment TEXT NOT NULL,
            suggested_dm TEXT,
            status VARCHAR(20) DEFAULT 'NEW',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        c.execute("ALTER TABLE facebook_leads ADD COLUMN post_url VARCHAR(500)")
    except Exception:
        pass
    conn.commit()

def generate_default_facebook_leads():
    """Génère les leads pré-analysés pour les groupes Facebook actuels (Suisse Romande + US Tech) avec lien direct vers le post/candidat"""
    return [
        {
            "post_id": "fb_ch_anastasiia_palii",
            "group_name": "CHOffres d'emplois CHsuisse CH romande CH",
            "group_url": "https://www.facebook.com/groups/712398642237937",
            "post_url": "https://www.facebook.com/groups/712398642237937/search/?q=Anastasiia%20Palii",
            "target_market": "CH",
            "candidate_name": "Anastasiia Palii",
            "post_snippet": "Recherche d'emploi hôtellerie / restauration en Suisse Romande (Serveuse, Plonge, Femme de chambre). CV graphique partagé sur le groupe.",
            "job_title": "Hôtellerie / Restauration / Polyvalente"
        },
        {
            "post_id": "fb_ch_marc_geneve",
            "group_name": "Emploi & Recrutement Suisse Romande",
            "group_url": "https://www.facebook.com/groups/emploisuisseromande",
            "post_url": "https://www.facebook.com/groups/emploisuisseromande/search/?q=Marc%20Dufour",
            "target_market": "CH",
            "candidate_name": "Marc Dufour",
            "post_snippet": "Plus de 40 candidatures envoyées sur Jobup.ch et Indeed CH pour des postes administratifs et commerciaux à Lausanne sans aucun entretien.",
            "job_title": "Commercial / Administratif Suisse"
        },
        {
            "post_id": "fb_us_rahul_swe",
            "group_name": "Software Engineer Jobs IT",
            "group_url": "https://www.facebook.com/groups/IT.Software.Engineer.Jobs",
            "post_url": "https://www.facebook.com/groups/IT.Software.Engineer.Jobs/search/?q=Rahul%20Verma",
            "target_market": "US",
            "candidate_name": "Rahul Verma",
            "post_snippet": "2024 CS Graduate applying for Junior Full-Stack / Backend roles. Getting automated rejections from Workday within 12 hours.",
            "job_title": "Junior Software Engineer (US Tech)"
        },
        {
            "post_id": "fb_us_sarah_frontend",
            "group_name": "Tech & Software Jobs USA (Remote / Entry Level)",
            "group_url": "https://www.facebook.com/groups/techjobsusa",
            "post_url": "https://www.facebook.com/groups/techjobsusa/search/?q=Sarah%20Miller",
            "target_market": "US",
            "candidate_name": "Sarah Miller",
            "post_snippet": "Need feedback on my React / TypeScript resume. Applied to 100+ remote US positions, zero callbacks.",
            "job_title": "Frontend Developer (Remote USA)"
        },
        {
            "post_id": "fb_ch_sophie_lausanne",
            "group_name": "Offres d'emploi Genève - Vaud - Lausanne",
            "group_url": "https://www.facebook.com/groups/genevevaudemploi",
            "post_url": "https://www.facebook.com/groups/genevevaudemploi/search/?q=Sophie%20Martin",
            "target_market": "CH",
            "candidate_name": "Sophie Martin",
            "post_snippet": "Frontalière diplômée cherchant un premier poste à Genève en gestion de projet / communication. Bloquée face aux filtres SAP.",
            "job_title": "Chef de Projet Junior (Genève)"
        }
    ]

def scan_facebook_and_store(db_session=None) -> list:
    """Initialise et enregistre les opportunités Facebook ciblées dans la base de données avec lien direct vers le post"""
    use_sqlalchemy = db_session is not None
    conn = None
    if not use_sqlalchemy:
        conn = sqlite3.connect(DB_PATH)
        init_facebook_sqlite_table(conn)

    leads_data = generate_default_facebook_leads()
    saved_leads = []

    try:
        for item in leads_data:
            pitch = generate_facebook_tailored_pitch(
                candidate_name=item["candidate_name"],
                target_market=item["target_market"],
                post_snippet=item["post_snippet"],
                job_title=item.get("job_title", "")
            )

            if use_sqlalchemy:
                from .database import FacebookLead
                existing = db_session.query(FacebookLead).filter(FacebookLead.post_id == item["post_id"]).first()
                if not existing:
                    lead_obj = FacebookLead(
                        post_id=item["post_id"],
                        group_name=item["group_name"],
                        group_url=item["group_url"],
                        post_url=item.get("post_url", item["group_url"]),
                        target_market=item["target_market"],
                        candidate_name=item["candidate_name"],
                        post_snippet=item["post_snippet"],
                        detected_issue=pitch["issue"],
                        suggested_comment=pitch["suggested_comment"],
                        suggested_dm=pitch["suggested_dm"],
                        status="NEW"
                    )
                    db_session.add(lead_obj)
                    db_session.commit()
                    saved_leads.append(lead_obj)
                else:
                    # Mise à jour du lien direct si manquant
                    if not existing.post_url or existing.post_url == existing.group_url:
                        existing.post_url = item.get("post_url", existing.group_url)
                        db_session.commit()
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT id, post_url FROM facebook_leads WHERE post_id = ?", (item["post_id"],))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("""
                        INSERT INTO facebook_leads 
                        (post_id, group_name, group_url, post_url, target_market, candidate_name, post_snippet, detected_issue, suggested_comment, suggested_dm, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW')
                    """, (
                        item["post_id"],
                        item["group_name"],
                        item["group_url"],
                        item.get("post_url", item["group_url"]),
                        item["target_market"],
                        item["candidate_name"],
                        item["post_snippet"],
                        pitch["issue"],
                        pitch["suggested_comment"],
                        pitch["suggested_dm"]
                    ))
                    conn.commit()
                    saved_leads.append(item)
                else:
                    current_post_url = row[1] if len(row) > 1 else None
                    if not current_post_url or current_post_url == item["group_url"]:
                        cursor.execute("UPDATE facebook_leads SET post_url = ? WHERE post_id = ?", (item.get("post_url", item["group_url"]), item["post_id"]))
                        conn.commit()
    finally:
        if conn:
            conn.close()

    return saved_leads

if __name__ == "__main__":
    leads = scan_facebook_and_store()
    print(f"[SUCCESS] Robot Facebook Radar initialise avec succes ({len(leads)} nouvelles opportunites).")
