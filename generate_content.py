import os
import django
import requests
import sys
import json
import colorama
from colorama import Fore, Style
from openai import OpenAI

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserTrends

# Configuration des chemins
BASE_PATH = '/Users/romain-pro/Desktop/factoryapp/'
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
       f"Tu rédiges du contenus pour la société suivante : {data['Company_info']}\n"
        f"Article à créer : {data['title']} et {data['base_content']}\n"
        f"Instructions : ton de voix : {data['tone_of_voice']}, "
        f"Type de contenu à écrire: {data['content_goal']}, le contenu doit être de longueur : {data['content_size']}.  .\n"
        f"objectif du contenu : {data['goals']}. Si c'est pertinent tu peux parler de leur produit : {data['product']}\n"
        f"Instruction supplémentaire de l'utilisateur : {data.get('user_comment', '')}\n"
        f"Pour t'aider à la rédaction, voici du contenu supplémentaire dont tu peux t'inspirer : {additional_content}."
    )
    return prompt

def analyser_contenu_avec_writergpt(prompt_complet, prompt_writergpt):
    messages = [{"role": "system", "content": prompt_writergpt}, 
                {"role": "user", "content": prompt_complet}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            return response.choices[0].message.content
        else:
            print(Fore.RED + "Aucune réponse valide reçue de WriterGPT.")
            return None
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l'analyse IA avec WriterGPT : {e}")
        return None

def envoyer_a_bubble_contenu(titre_filename, contenu_filename, webhook_url, email):
    try:
        with open(titre_filename, 'r', encoding='utf-8') as file:
            titre_content = file.read()
        with open(contenu_filename, 'r', encoding='utf-8') as file:
            contenu_content = file.read()
        data = {"titre": titre_content, "contenu": contenu_content, "email": email}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l'envoi du contenu à Bubble: {e}")
        return None, str(e)

def main(data):
    user_id = data.get("user_id", 1) 
    titles_and_summaries = get_user_trends_data(user_id)
    prompt_complet = create_writergpt_prompt(data, titles_and_summaries)
    response_data = analyser_contenu_avec_writergpt(prompt_complet, lire_prompt_writergpt())

    if response_data:
        titre_genere, contenu_genere = (response_data.split("SEPARATION", 1) if "SEPARATION" in response_data else ("", ""))
        titre_filename = "titre_genere.txt"
        contenu_filename = "contenu_genere.txt"
        with open(titre_filename, 'w', encoding='utf-8') as file:
            file.write(titre_genere)
        with open(contenu_filename, 'w', encoding='utf-8') as file:
            file.write(contenu_genere)
        webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/content_generation_content"
        email = data.get('email', '')  # Récupération de l'email depuis les données
        status, text = envoyer_a_bubble_contenu(titre_filename, contenu_filename, webhook_url, email)
        print(f"Envoi des données - Status: {status}, Response: {text}")
    else:
        print(Fore.RED + "Erreur lors de la génération du contenu.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        print("Données reçues:", data)  # Ajoutez cette ligne pour le débogage

        main(data)
    else:
        print("Aucune donnée fournie.")
