import os
import django
import requests
import sys
import time
import json
import colorama
from colorama import Fore, Style
from openai import OpenAI

# Configuration de Django
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

def lire_prompt_SuggestionGPT():
    prompt_SuggestionGPT_path = os.path.join(PROMPT_PATH, 'trends-suggestionGPT.txt')
    with open(prompt_SuggestionGPT_path, 'r', encoding='utf-8') as file:
        return file.read()

def create_SuggestionGPT_prompt(data, titles_and_summaries):
    additional_content = " ".join(titles_and_summaries)
    prompt = (
        f"Aujour'dhui tu travailles pour la société suivante {data['Company_info']}. TOn objectif va être de rédigéer des suggestion d'article super personnalisées qui prendront en compte, les informations de l'entreprises, certaines tendances de contenus que l'on va te fournir ainsi que un ou plusieurs produit de cette société.\n"
        f"Ecris des suggestions d'articles en te basant sur la/les tendance(s) suivante(s) : {data['titre']} et {data['base_content']}\n"
        f"Tes suggestions doivent parler du/des produit(s) de la société suivant :  {data['product']} qui fait/font respectivement : {data['description']} "
        f"Voici une liste d'article et de leur résumer sur divers tendance, parcours la et inspire toi uniquement des tendance similaire à {data['titre']} et {data['base_content']} pour tes suggestions: {additional_content}."
    )
    return prompt

def analyser_suggestions_avec_SuggestionGPT(prompt_complet, prompt_SuggestionGPT):
    messages = [{"role": "system", "content": prompt_SuggestionGPT}, 
                {"role": "user", "content": prompt_complet}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            suggestions_dict = json.loads(response.choices[0].message.content)
            print("Réponse de SuggestionGPT:", suggestions_dict)
            return suggestions_dict
        else:
            print(Fore.RED + "Aucune réponse valide reçue de SuggestionGPT.")
            return None
    except Exception as e:
        print(Fore.RED + f"Erreur lors de l'analyse IA avec SuggestionGPT : {e}")
        return None

def creer_et_envoyer_json_suggestions(suggestions_dict):
    filenames = []
    for i, (key, suggestion) in enumerate(suggestions_dict.items()):
        filename = f"suggestion_{i + 1}.json"
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(suggestion, file, indent=4, ensure_ascii=False)
        filenames.append(filename)
    return filenames

def envoyer_tous_les_json(filenames, webhook_url):
    for filename in filenames:
        status, text = envoyer_a_bubble(filename, webhook_url)
        print(f"Envoi de la suggestion {filename} - Status: {status}, Response: {text}")
        time.sleep(5)  # Pause de 5 secondes


def envoyer_a_bubble(filename, webhook_url, email):
    headers = {'Content-Type': 'application/json'}
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    data['email'] = email  # Ajout de l'email aux données

    try:
        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(f"Erreur lors de l'envoi des données à Bubble: {e}")
        return None, str(e)

def supprimer_fichiers_json():
    for fichier in os.listdir():
        if fichier.endswith(".json") and (fichier.startswith("topic_") or fichier.startswith("suggestion_")):
            os.remove(fichier)
            print(f"Fichier {fichier} supprimé.")

# Appel de la fonction pour supprimer les fichiers JSON
def main(data):
    user_id = data.get("user_id", 1)
    email = data.get('email', '')  # Récupération de l'email depuis les données
    titles_and_summaries = get_user_trends_data(user_id)
    prompt_complet = create_SuggestionGPT_prompt(data, titles_and_summaries)
    response_data = analyser_suggestions_avec_SuggestionGPT(prompt_complet, lire_prompt_SuggestionGPT())

    if response_data:
        filenames = creer_et_envoyer_json_suggestions(response_data)
        for filename in filenames:
            envoyer_a_bubble(filename, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/tailor_made_suggestion/initialize", email)
            time.sleep(5)  # Pause de 5 secondes entre les envois
        supprimer_fichiers_json()  
    else:
        print(Fore.RED + "Erreur lors de la génération des suggestions.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        main(data)
    else:
        print("Aucune donnée fournie pour la suggestion de tendance.")
