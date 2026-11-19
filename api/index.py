import sys
import os

# Assurer que le dossier racine du projet est dans sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from jobcatch.main import app

# Export de l'application pour le runtime Vercel Serverless
app = app
