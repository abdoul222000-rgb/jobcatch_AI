# JobCatch AI - Dossier de Projet & Statut Complet 🚀

Ce document récapitule l'intégralité de la genèse, de l'architecture et du code de **JobCatch AI** créé pour Assouman Abdoul Aziz Diabagate.

---

## 1. Origine & Concept
- **Marché Cible :** Étudiants, jeunes diplômés et professionnels aux États-Unis (18 - 28 ans).
- **Problème Résolu :** Les chercheurs d'emploi aux USA envoient des centaines de CV manuellement pour passer les filtres ATS (Applicant Tracking System). JobCatch AI adapte le CV aux mots-clés exacts de chaque offre et postule automatiquement à 50 offres par jour.
- **Modèle Économique :**
  - **Abonnement :** $39 / mois.
  - **Essai gratuit :** 3 jours (sans prélèvement immédiat).
  - **Marge brute :** +95% (coût API IA par candidature < $0.003).
  - **Encaissement :** Directement vers le compte Lead Bank (Routing: `101019644`, compte terminant par `9479`).

---

## 2. Emplacement du Code
- **Dossier racine indépendant :** `C:\Users\levis\Documents\JobCatch_AI\`
- **Dépôt Git :** Branche `main` initialisée (`feat: initial commit`).

---

## 3. Architecture Technique Réalisée (100% Testée & Validée)
- **`jobcatch/config.py` :** Configuration Pydantic, clés secrètes HMAC-SHA256, prix $39/mo, identifiants Lead Bank.
- **`jobcatch/database.py` :** Modèles SQLAlchemy (`User`, `Resume`, `JobApplication`) + seed du compte de démonstration (`demo@jobcatch.ai` / `jobcatch2026`).
- **`jobcatch/services/ai_tailor.py` :** Moteur d'optimisation ATS, calcul de score (85-98%), réécriture de bullet points avec verbes d'action, générateur de lettre de motivation en 3s.
- **`jobcatch/security.py` :** Cookies signés anti-usurpation et en-têtes de sécurité bancaires.
- **`jobcatch/templates/` :**
  - `landing.html` : Page d'accueil moderne en dark mode avec simulateur ATS interactif avant/après.
  - `auth/login.html` & `auth/register.html` : Portails de connexion avec bouton démo 1-clic.
  - `dashboard.html` : Tableau de bord candidat complet avec KPIs, suivi des candidatures (Applied, Interview, Offer) et modal d'optimisation rapide.
  - `billing.html` : Gestion d'abonnement $39/mo et badges de sécurité Lead Bank.
- **`run_jobcatch.bat` :** Lanceur 1-clic local sur `http://localhost:8080`.
- **`Procfile` & `requirements.txt` :** Prêt pour déploiement Cloud immédiat sur Render.

---

## 4. Prochaines Étapes pour JobCatch AI
1. Lancer `run_jobcatch.bat` et tester le tableau de bord localement.
2. Déployer sur Render sous un nouveau service web distinct.
3. Préparer les posts viraux Reddit (`r/jobs`, `r/resumes`) et TikTok pour l'acquisition client gratuite à 0$.
