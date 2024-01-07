import os
import json
import django
import requests
import time
import colorama
from colorama import Fore, Style
from openai import OpenAI

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserTrends


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

def get_user_trends_data(user_id):
    try:
        user = User.objects.get(pk=user_id)
        user_trends = UserTrends.objects.filter(user=user)
        titles_and_summaries = [f"{trend.titre}: {trend.resume}" for trend in user_trends]
        return titles_and_summaries
    except User.DoesNotExist:
        print(Fore.RED + "Utilisateur non trouvé.")
        return []
    except Exception as e:
        print(Fore.RED + f"Erreur lors de la récupération des tendances: {e}")
        return []

def lire_prompt_writergpt():
    prompt_writergpt_path = os.path.join(PROMPT_PATH, 'WriterGPT.txt')
    with open(prompt_writergpt_path, 'r', encoding='utf-8') as file:
        return file.read()

def create_writergpt_prompt(data, titles_and_summaries):
    additional_content = " ".join(titles_and_summaries)
    prompt = (
        f"Article à créer : {data['title']} et {data['base_content']}\n"
        f"Instructions : ton de voix : {data['tone_of_voice']}, "
        f"objectif de contenu : {data['content_goal']}, écris en : {data['language']}.\n"
        f"Instruction supplémentaire de l'utilisateur : {data['user_comment']}\n"
        f"Pour t'aider à la rédaction, voici du contenu supplémentaire dont tu peux t'inspirer : {additional_content}."
    )
    return prompt

def analyser_contenu_avec_writergpt(prompt_complet, prompt_writergpt):
    messages = [{"role": "system", "content": prompt_writergpt}, 
                {"role": "user", "content": prompt_complet}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            response_str = response.choices[0].message.content

            # Affichage de la réponse pour le débogage
            print(Fore.YELLOW + "Réponse brute de WriterGPT:" + Fore.CYAN, response_str)

            return response_str
        else:
            print(Fore.RED + "Aucune réponse valide reçue de WriterGPT.")
            return None
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l'analyse IA avec WriterGPT : {e}")
        return None


# ID de l'utilisateur pour le test
user_id = 1

# Données brutes pour le test
data_brute = {
  "title": "Absenteïsme féminin : entre réalité biologique et pressions sociétales",
  "base_content": "Cet article mettra en lumière les facteurs impactant le taux plus élevé d'absentéisme chez les femmes, en croisant données sociologiques et responsabilités familiales. Un focus sur les politiques d'entreprise inclusives sera proposé pour atténuer cette disparité.",
  "tone_of_voice": "professionnal",
  "content_goal": "Blog Post",
  "language": "Français",
  "user_comment" :""
}

# Exécution du script
titles_and_summaries = get_user_trends_data(user_id)
print("Titres et Résumés récupérés:", titles_and_summaries)

prompt_complet = create_writergpt_prompt(data_brute, titles_and_summaries)
print("Prompt complet pour WriterGPT:", prompt_complet)

prompt_writergpt = lire_prompt_writergpt()
response_data = analyser_contenu_avec_writergpt(prompt_complet, prompt_writergpt)

def envoyer_a_bubble_contenu(titre_filename, contenu_filename, webhook_url):
    try:
        with open(titre_filename, 'r', encoding='utf-8') as file:
            titre_content = file.read()

        with open(contenu_filename, 'r', encoding='utf-8') as file:
            contenu_content = file.read()

        data = {
            "titre": titre_content,
            "contenu": contenu_content
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l'envoi du contenu à Bubble: {e}")
        return None, str(e)

if response_data:
    # Séparation du titre et du contenu
    if "SEPARATION" in response_data:
        titre_genere, contenu_genere = response_data.split("SEPARATION", 1)
        titre_genere = titre_genere.strip()
        contenu_genere = contenu_genere.strip()
    else:
        print(Fore.RED + "Le format de la réponse de WriterGPT n'est pas conforme.")
        titre_genere = ""
        contenu_genere = ""

    # Création et enregistrement du fichier texte pour le titre
    titre_filename = "titre_genere.txt"
    with open(titre_filename, 'w', encoding='utf-8') as file:
        file.write(titre_genere)

    # Création et enregistrement du fichier texte pour le contenu
    contenu_filename = "contenu_genere.txt"
    with open(contenu_filename, 'w', encoding='utf-8') as file:
        file.write(contenu_genere)

    webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/content_generation_content"
    status, text = envoyer_a_bubble_contenu(titre_filename, contenu_filename, webhook_url)
    print(f"Envoi des données - Status: {status}, Response: {text}")