import httpx
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
import os
import sqlite3

# Chemins et configurations (Vercel Serverless & Local)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "/tmp/jobcatch.db" if os.getenv("VERCEL") else os.path.join(BASE_DIR, "jobcatch.db")

SUBREDDITS = ["resumes", "jobs", "cscareerquestions", "csmajors", "recruitinghell"]

KEYWORDS = [
    "applied", "rejection", "rejected", "ghosting", "ghosted", "ats", 
    "no interview", "no interviews", "workday", "greenhouse", "taleo", 
    "bullet point", "bullet points", "entry level", "entry-level", 
    "junior", "grad", "graduate", "screening", "keyword", "keywords",
    "few interviews", "need help", "feedback"
]

def clean_html(raw_html: str) -> str:
    """Nettoie le HTML du feed RSS pour extraire le texte brut"""
    text = html.unescape(raw_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_tailored_reply(title: str, text: str, subreddit: str) -> str:
    """Génère une réponse professionnelle, empathique et axée sur la valeur pour Reddit US"""
    t_lower = (title + " " + text).lower()
    
    if "workday" in t_lower or "greenhouse" in t_lower or "taleo" in t_lower or "ats" in t_lower:
        advice = (
            "Corporate ATS systems (like Workday, Taleo, and Greenhouse) parse resumes line-by-line "
            "looking for exact keyword density and quantified metrics (X-Y-Z formula: Accomplished [X] as measured by [Y], by doing [Z]). "
            "If bullet points are generic or task-based, algorithms tag them with low match scores before a recruiter opens the PDF."
        )
    elif "applied" in t_lower or "no interview" in t_lower or "ghosted" in t_lower:
        advice = (
            "When you apply to dozens of roles and hear back with automated rejections, 90% of the time it is an ATS keyword mismatch. "
            "Companies receive 300+ applications per junior role and filter out anyone below an 80% relevance score."
        )
    else:
        advice = (
            "One concrete tweak that makes an immediate difference: upgrade passive bullet points into quantifiable impact metrics. "
            "Instead of 'Worked on application features', write 'Engineered full-stack features using Python and React, accelerating user onboarding by 28%'."
        )

    reply = (
        f"I completely relate to this. {advice}\n\n"
        "A practical move is testing your bullet points through a live ATS parser simulator before submitting applications. "
        "I built an interactive ATS simulator on JobCatch AI (https://jobcatch-ai.vercel.app) "
        "that scores bullet points from 0 to 100% and illustrates how to transform generic 40% bullets into 95%+ impact lines for tech and corporate roles.\n\n"
        "Hope this helps you break through the filter—rooting for your next interview!"
    )
    return reply

def send_telegram_alert(lead: dict, bot_token: str = None, chat_id: str = None) -> bool:
    """Envoie une notification Telegram au fondateur si configuré"""
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        return False
        
    message = (
        f"🎯 <b>OPPORTUNITÉ REDDIT ({lead['subreddit']})</b>\n\n"
        f"📌 <b>Titre :</b> {html.escape(lead['title'])}\n"
        f"🔗 <b>Lien :</b> <a href=\"{lead['url']}\">Ouvrir sur Reddit</a>\n"
        f"🔑 <b>Mots-clés :</b> {html.escape(lead.get('matched_keyword', ''))}\n\n"
        f"📝 <b>RÉPONSE TOUTE PRÊTE :</b>\n"
        f"<code>{html.escape(lead['suggested_reply'])}</code>\n\n"
        f"<i>💡 Cliquez sur le texte pour le copier et collez-le sur Reddit !</i>"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        with httpx.Client(timeout=8.0) as client:
            res = client.post(url, json=payload)
            return res.status_code == 200
    except Exception:
        return False

def init_sqlite_table(conn):
    """Crée la table radar_leads si nécessaire en sqlite direct"""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS radar_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reddit_id VARCHAR(50) UNIQUE,
            subreddit VARCHAR(50),
            title VARCHAR(500),
            url VARCHAR(500),
            author VARCHAR(100),
            snippet TEXT,
            matched_keyword VARCHAR(100),
            suggested_reply TEXT,
            status VARCHAR(20) DEFAULT 'NEW',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def scan_reddit_and_store(max_leads: int = 10, db_session = None) -> list:
    """Scanne Reddit, enregistre les nouvelles opportunités dans la BDD et alerte Telegram"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    new_leads = []
    
    # Utiliser SQLAlchemy si disponible dans le contexte FastAPI, sinon sqlite3 direct
    use_sqlalchemy = db_session is not None
    conn = None
    if not use_sqlalchemy:
        conn = sqlite3.connect(DB_PATH)
        init_sqlite_table(conn)

    try:
        with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
            for sub in SUBREDDITS:
                if len(new_leads) >= max_leads:
                    break
                    
                rss_url = f"https://www.reddit.com/r/{sub}/new.rss"
                try:
                    response = client.get(rss_url)
                    if response.status_code != 200:
                        continue
                        
                    root = ET.fromstring(response.text)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    for entry in root.findall('atom:entry', ns):
                        entry_id_elem = entry.find('atom:id', ns)
                        entry_id = entry_id_elem.text if entry_id_elem is not None else ""
                        if not entry_id:
                            continue
                            
                        # Vérifier doublon
                        if use_sqlalchemy:
                            from .database import RadarLead
                            existing = db_session.query(RadarLead).filter(RadarLead.reddit_id == entry_id).first()
                            if existing:
                                continue
                        else:
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM radar_leads WHERE reddit_id = ?", (entry_id,))
                            if cursor.fetchone():
                                continue

                        title_elem = entry.find('atom:title', ns)
                        title = title_elem.text if title_elem is not None else "Untitled Post"

                        link_elem = entry.find('atom:link', ns)
                        link = link_elem.get('href') if link_elem is not None else ""

                        content_elem = entry.find('atom:content', ns)
                        raw_content = content_elem.text if content_elem is not None else ""
                        clean_text = clean_html(raw_content)

                        author_elem = entry.find('atom:author/atom:name', ns)
                        author = author_elem.text if author_elem is not None else "Anonymous"

                        combined = f"{title} {clean_text}".lower()
                        matched = [kw for kw in KEYWORDS if kw in combined]
                        
                        if matched:
                            suggested = generate_tailored_reply(title, clean_text, sub)
                            snippet = clean_text[:280] + ("..." if len(clean_text) > 280 else "")
                            kw_str = ", ".join(matched[:3])

                            if use_sqlalchemy:
                                from .database import RadarLead
                                lead_record = RadarLead(
                                    reddit_id=entry_id,
                                    subreddit=f"r/{sub}",
                                    title=title,
                                    url=link,
                                    author=author,
                                    snippet=snippet,
                                    matched_keyword=kw_str,
                                    suggested_reply=suggested,
                                    status="NEW"
                                )
                                db_session.add(lead_record)
                                db_session.commit()
                            else:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO radar_leads (reddit_id, subreddit, title, url, author, snippet, matched_keyword, suggested_reply, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW')
                                """, (entry_id, f"r/{sub}", title, link, author, snippet, kw_str, suggested))
                                conn.commit()

                            lead_dict = {
                                "subreddit": f"r/{sub}",
                                "title": title,
                                "url": link,
                                "author": author,
                                "snippet": snippet,
                                "matched_keyword": kw_str,
                                "suggested_reply": suggested
                            }
                            
                            # Envoyer alerte Telegram si configuré
                            send_telegram_alert(lead_dict)
                            new_leads.append(lead_dict)

                            if len(new_leads) >= max_leads:
                                break
                except Exception:
                    continue
    finally:
        if conn:
            conn.close()
            
    return new_leads

if __name__ == "__main__":
    leads = scan_reddit_and_store(max_leads=5)
    print(f"[SUCCESS] {len(leads)} opportunites Reddit detectees et stockees.")
    for l in leads:
        try:
            print(f"\n[{l['subreddit']}] {l['title'][:80]}")
            print(f"Lien : {l['url']}")
            print(f"Keywords : {l['matched_keyword']}")
        except Exception:
            pass
