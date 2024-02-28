import os
import django
import json
import requests
import time
from openai import OpenAI

# Configuration de Django pour accéder aux modèles
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserTrends, Trend

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Configuration du client OpenAI
client = OpenAI(api_key=open_file("openaiapikey.txt"))


BASE_PATH = '/Users/romain-pro/Desktop/factoryapp'
PROMPT_PATH = os.path.join(BASE_PATH, 'Prompts')


# Variables globales
WEBHOOK_URL = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/preshoot_suggestion"
USER_ID = '40'  # ID utilisateur pour lequel générer les suggestions

def get_user_email(user_id):
    try:
        user = User.objects.get(pk=user_id)
        print(f"Email de l'utilisateur récupéré : {user.email}")
        return user.email
    except User.DoesNotExist:
        print("Utilisateur non trouvé.")
        return None

def recuperer_tendances_utilisateur(user_id):
    tendances = Trend.objects.filter(user_id=user_id)
    print(f"{len(tendances)} tendances trouvées pour l'utilisateur {user_id}")
    return tendances

def filtrer_user_trends_par_tendance(tendance):
    user_trends = UserTrends.objects.all()
    titres_et_resumes = []

    main_topics = tendance.main_topics.split(", ")
    secondary_topics = tendance.secondary_topics.split(", ")  # Utilise le nom correct du champ dans Trend

    for user_trend in user_trends:
        if any(topic in user_trend.main_topics for topic in main_topics) or any(topic in user_trend.topics_secondaires for topic in secondary_topics):  # Utilise le nom correct du champ dans UserTrends
            titres_et_resumes.append({'titre': user_trend.titre, 'resume': user_trend.resume})

    print(f"{len(titres_et_resumes)} UserTrends correspondants trouvés pour la tendance '{tendance.titre}'")
    return titres_et_resumes

def lire_prompt_suggestiongpt():
    prompt_suggestiongpt_path = os.path.join(PROMPT_PATH, "SuggestionGPT.txt")
    with open(prompt_suggestiongpt_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
        print("Prompt pour SuggestionGPT lu.")
        return prompt

def analyser_suggestions_avec_IA(data, prompt_suggestiongpt):
    data_json = json.dumps(data, indent=4, ensure_ascii=False)
    prompt_complet = prompt_suggestiongpt
    messages = [{"role": "system", "content": prompt_complet}, 
                {"role": "user", "content": data_json}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            response_data = json.loads(response.choices[0].message.content)
            print("Réponse de SuggestionGPT:", response_data)
            return response_data
        else:
            print("Aucune réponse valide reçue de SuggestionGPT.")
            return None
    except Exception as e:
        print(f"Erreur lors de l'analyse IA : {e}")

def envoyer_a_bubble(data, webhook_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, headers=headers, json=data)
    return response.status_code, response.text

def creer_et_envoyer_json_suggestions2(response_data, webhook_url, user_email, titre_tendance):
    if not isinstance(response_data, dict):
        print("Les données de réponse doivent être un dictionnaire.")
        return

    for i, (key, value) in enumerate(response_data.items(), start=1):
        # Prépare le fichier JSON pour l'envoi
        filename = f"suggestion_{i}.json"
        suggestion_data = {
            "suggestion": value,
            "user_email": user_email,
            "titre_tendance": titre_tendance
        }

        # Écriture des données dans un fichier temporaire (pas nécessaire si vous envoyez directement)
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(suggestion_data, file, indent=4)

        # Envoi des données au webhook
        status, text = envoyer_a_bubble(suggestion_data, webhook_url)
        print(f"Envoi de la suggestion {filename} - Status: {status}, Response: {text}")

        # Pause entre les envois
        time.sleep(5)

def generer_suggestions_pour_toutes_tendances(user_id):
    user_email = get_user_email(user_id)
    if not user_email:
        print("Email utilisateur non trouvé, arrêt du script.")
        return

    tendances = recuperer_tendances_utilisateur(user_id)
    prompt_suggestiongpt = lire_prompt_suggestiongpt()

    for tendance in tendances:
        print(f"Traitement de la tendance '{tendance.titre}'...")
        titres_et_resumes = filtrer_user_trends_par_tendance(tendance)
        if titres_et_resumes:
            data_json = json.dumps(titres_et_resumes, indent=4)
            response_data = analyser_suggestions_avec_IA(data_json, prompt_suggestiongpt)
            if response_data:
                creer_et_envoyer_json_suggestions2(response_data, WEBHOOK_URL, user_email, tendance.titre)
            else:
                print(f"Aucune suggestion générée pour la tendance '{tendance.titre}'.")
        else:
            print(f"Aucun UserTrends correspondant trouvé pour la tendance '{tendance.titre}'.")

generer_suggestions_pour_toutes_tendances(USER_ID)
