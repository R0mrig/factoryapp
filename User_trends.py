import os
import sys
import django
import requests
import json
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import datetime
import tempfile
import openai
from colorama import Fore, Style
import colorama
from urllib.parse import quote
from openai import OpenAI
import time



# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserTrends, Trend

# Configuration des chemins
BASE_PATH = '/Users/romain-pro/Desktop/factoryapp'
PROMPT_PATH = os.path.join(BASE_PATH, 'Prompts')

# Initialisation de colorama
colorama.init(autoreset=True)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Configuration du client OpenAI
client = OpenAI(api_key=open_file("openaiapikey.txt"))



if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    print("Aucun ID utilisateur fourni.")
    sys.exit(1)



### Trends & topics GENERATION ###



PROMPT_PATH = os.path.join(BASE_PATH, 'Prompts')

def enregistrer_tendances(user_id, tendances):
    user = User.objects.get(pk=user_id)  # Assurez-vous que l'utilisateur existe
    for cle, tendance in tendances.items():  # Itérez sur les clés (topic_x) et valeurs (détails de chaque tendance)
        # Assurez-vous que toutes les clés nécessaires sont présentes dans chaque dictionnaire de tendance
        try:
            Trend.objects.create(
                user=user,
                titre=tendance.get('titre', 'Titre par défaut'),  # Utilisez get pour éviter KeyError si la clé est absente
                resume=tendance.get('resume', 'Résumé par défaut'),
                main_topics=tendance.get('main_topics', 'Aucun sujet principal'),
                secondary_topics=tendance.get('secondary_topics', 'Aucun sujet secondaire'),
                ponderation=tendance.get('ponderation', 0)  # Assurez-vous que la pondération est un décimal approprié
            )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la tendance: {e}")
            # Vous pouvez choisir de lever une exception, de continuer avec une valeur par défaut, ou de simplement logger l'erreur

def get_user_trends_data(user_id):
    try:
        user = User.objects.get(pk=user_id)
        user_trends = UserTrends.objects.filter(user=user)

        all_keywords = []
        all_main_topics = []
        all_secondary_topics = []
        titles_and_summaries = []

        for trend in user_trends:
            all_keywords.extend(trend.mots_cles.split(', '))
            all_main_topics.append(trend.main_topics)
            all_secondary_topics.append(trend.topics_secondaires)
            titles_and_summaries.append(f"{trend.titre}: {trend.resume}")

        return all_keywords, all_main_topics, all_secondary_topics, titles_and_summaries
    except User.DoesNotExist:
        print(Fore.RED + "Utilisateur non trouvé.")
        return [], [], [], []
    except Exception as e:
        print(Fore.RED + f"Erreur lors de la récupération des tendances: {e}")
        return [], [], [], []



# Récupération des informations
keywords, main_topics, secondary_topics, titles_and_summaries = get_user_trends_data(user_id)

# Affichage des informations avec des couleurs
print(Fore.GREEN + "Mots-clés:" + Fore.YELLOW, keywords)
print(Fore.GREEN + "Topics Primaires:" + Fore.YELLOW, main_topics)
print(Fore.GREEN + "Topics Secondaires:" + Fore.YELLOW, secondary_topics)
print(Fore.GREEN + "Titres et Résumés:")
for ts in titles_and_summaries:
    print(Fore.CYAN + ts)

def get_user_email(user_id):
    try:
        user = User.objects.get(pk=user_id)
        return user.email
    except User.DoesNotExist:
        print("Utilisateur non trouvé.")
        return None

# Récupération de l'email de l'utilisateur
user_email = get_user_email(user_id)
if not user_email:
    sys.exit("E-mail utilisateur non trouvé.")

### ANALYSE AVEC TrendsGPT ###
        
def lire_prompt_trendsgpt():
    prompt_trendsgpt_path = os.path.join(PROMPT_PATH, 'TrendsGPT.txt')
    with open(prompt_trendsgpt_path, 'r', encoding='utf-8') as file:
        return file.read()

def analyser_tendances_avec_IA(data, prompt_trendsgpt):
    data_json = json.dumps(data, indent=4, ensure_ascii=False)
    print("Data JSON envoyé:", data_json)  # Pour debug
    prompt_complet = prompt_trendsgpt
    messages = [{"role": "system", "content": prompt_complet}, 
                {"role": "user", "content": data_json}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            response_data = json.loads(response.choices[0].message.content)
            print("Réponse de TrendsGPT:", response_data)
            return response_data
        else:
            print("Aucune réponse valide reçue de TrendsGPT.")
            return None
    except Exception as e:
        print(f"Erreur lors de l'analyse IA : {e}")
        return None

def creer_et_envoyer_json(response_data, webhook_url, user_email):
    # Ajout de l'email dans les données
    response_data['user_email'] = user_email

    # Pour chaque élément dans response_data, créer et envoyer un fichier JSON
    for i, (_, value) in enumerate(response_data.items()):
        filename = f"topic_{i + 1}.json"
        topic_data = {"topic": value, "user_email": user_email}  # Inclure l'email dans chaque fichier JSON
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(topic_data, file, indent=4, ensure_ascii=False)

        status, text = envoyer_a_bubble(filename, webhook_url)
        print(f"Envoi du fichier {filename} - Status: {status}, Response: {text}")
        time.sleep(5)  # Pause de 5 secondes avant l'envoi du fichier suivant

    # Supprimer les fichiers JSON créés après leur envoi
    for fichier in os.listdir():
        if fichier.endswith(".json") and fichier.startswith("topic_"):
            os.remove(fichier)
            print(f"Fichier {fichier} supprimé.")


def envoyer_a_bubble(filename, webhook_url):
    headers = {'Content-Type': 'application/json'}
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(f"Erreur lors de l'envoi des données à Bubble: {e}")
        return None, str(e)

# Données à analyser
data_to_analyze = {
    "keywords": keywords,
    "main_topics": main_topics,
    "secondary_topics": secondary_topics,
    "titles_and_summaries": titles_and_summaries
}

prompt_trendsgpt = lire_prompt_trendsgpt()
response_data = analyser_tendances_avec_IA(data_to_analyze, prompt_trendsgpt)
if response_data:
    creer_et_envoyer_json(response_data, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/trends", user_email)
    enregistrer_tendances(user_id, response_data)




### SUGGESTIONS GENERATION AVEC SuggestionGPT ###

def lire_prompt_suggestiongpt():
    prompt_suggestiongpt_path = os.path.join(PROMPT_PATH, 'SuggestionGPT.txt')
    with open(prompt_suggestiongpt_path, 'r', encoding='utf-8') as file:
        return file.read()

def analyser_suggestions_avec_IA(data, prompt_suggestiongpt):
    data_json = json.dumps(data, indent=4, ensure_ascii=False)
    print("Data JSON envoyé:", data_json)  # Pour debug
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
        return None

def creer_et_envoyer_json_suggestions(response_data, webhook_url, user_email):
    for i, (_, value) in enumerate(response_data.items()):
        filename = f"suggestion_{i + 1}.json"
        suggestion_data = {"suggestion": value, "user_email": user_email,}
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(suggestion_data, file, indent=4, ensure_ascii=False)

        status, text = envoyer_a_bubble(filename, webhook_url)
        print(f"Envoi de la suggestion {filename} - Status: {status}, Response: {text}")
        time.sleep(5)  # Pause de 5 secondes avant l'envoi du fichier suivant

    # Supprimer les fichiers JSON créés après leur envoi
    for fichier in os.listdir():
        if fichier.endswith(".json") and fichier.startswith("suggestion_"):
            os.remove(fichier)
            print(f"Fichier {fichier} supprimé.")


def envoyer_a_bubble(filename, webhook_url):
    headers = {'Content-Type': 'application/json'}
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(f"Erreur lors de l'envoi des données à Bubble: {e}")
        return None, str(e)

# Utilisation de data_to_analyze déjà défini dans le script précédent
prompt_suggestiongpt = lire_prompt_suggestiongpt()
response_data = analyser_suggestions_avec_IA(data_to_analyze, prompt_suggestiongpt)

if response_data:
    creer_et_envoyer_json_suggestions(response_data, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/suggestions", user_email)

def supprimer_fichiers_json():
    for fichier in os.listdir():
        if fichier.endswith(".json") and (fichier.startswith("topic_") or fichier.startswith("suggestion_")):
            os.remove(fichier)
            print(f"Fichier {fichier} supprimé.")



def recuperer_tendances_utilisateur(user_id):
    return Trend.objects.filter(user_id=user_id)


def filtrer_user_trends_par_tendance(tendance):
    user_trends = UserTrends.objects.all()
    titres_et_resumes = []

    # Supposons que main_topics et secondary_topics sont stockés comme des chaînes de caractères séparées par des virgules
    main_topics = tendance.main_topics.split(", ")
    secondary_topics = tendance.secondary_topics.split(", ")

    for user_trend in user_trends:
        if any(topic in user_trend.main_topics for topic in main_topics) or any(topic in user_trend.topics_secondaires for topic in secondary_topics):
            titres_et_resumes.append({'titre': user_trend.titre, 'resume': user_trend.resume})

    return titres_et_resumes

def creer_et_envoyer_json_suggestions2(response_data, webhook_url, user_email, titre_tendance):
    for i, (_, value) in enumerate(response_data.items()):
        filename = f"suggestion_{i + 1}.json"
        suggestion_data = {
            "suggestion": value, 
            "user_email": user_email,
            "titre_tendance": titre_tendance  # Ajoute le titre de la tendance ici
        }
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(suggestion_data, file, indent=4, ensure_ascii=False)

        status, text = envoyer_a_bubble(filename, webhook_url)
        print(f"Envoi de la suggestion {filename} - Status: {status}, Response: {text}")
        time.sleep(5)  # Pause de 5 secondes avant l'envoi du fichier suivant

    # Supprimer les fichiers JSON créés après leur envoi
    for fichier in os.listdir():
        if fichier.endswith(".json") and fichier.startswith("suggestion_"):
            os.remove(fichier)
            print(f"Fichier {fichier} supprimé.")



def generer_suggestions_pour_toutes_tendances(user_id):
    tendances = recuperer_tendances_utilisateur(user_id)
    prompt_suggestiongpt = lire_prompt_suggestiongpt()

    for tendance in tendances:
        titres_et_resumes = filtrer_user_trends_par_tendance(tendance)
        if titres_et_resumes:  # Assure-toi d'avoir des données à envoyer
            data_json = json.dumps(titres_et_resumes, indent=4, ensure_ascii=False)
            response_data = analyser_suggestions_avec_IA(data_json, prompt_suggestiongpt)
            if response_data:
               creer_et_envoyer_json_suggestions2(response_data, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/preshoot_suggestion", user_email, tendance.titre)
            
        print(response_data)

generer_suggestions_pour_toutes_tendances(user_id)

# Appel de la fonction pour supprimer les fichiers JSON
supprimer_fichiers_json()