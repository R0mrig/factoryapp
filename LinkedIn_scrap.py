import os
import django
import requests
import sys
import json

# Initialisation de Django pour accéder aux modèles
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserSource

WEBHOOK_URL = "https://inversi0n.app.n8n.cloud/webhook-test/d3548e27-88b6-4b85-a096-88b85ad3ccab"

def send_urls_to_webhook(user_id):
    try:
        # Récupération de l'utilisateur et des sources associées
        user_sources = UserSource.objects.filter(user_id=user_id).first()
        if user_sources:
            linkedin_urls = user_sources.linkedin  # Assurez-vous que le champ s'appelle 'linkedin'
            # Envoi de tous les URLs LinkedIn au webhook dans une seule requête
            response = requests.post(WEBHOOK_URL, json={"urls": linkedin_urls, "user_id":user_id})
            if response.status_code == 200:
                print("Les URLs LinkedIn ont été envoyées avec succès au webhook.")
            else:
                print("Échec de l'envoi des URLs au webhook. Code d'état :", response.status_code)
        else:
            print("Aucune source trouvée pour l'utilisateur ID:", user_id)
    except Exception as e:
        print("Erreur lors de l'envoi des URLs au webhook :", e)

if __name__ == "__main__":
    # Récupération de l'ID de l'utilisateur depuis les arguments de la ligne de commande
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        send_urls_to_webhook(user_id)
    else:
        print("ID utilisateur non fourni.")
