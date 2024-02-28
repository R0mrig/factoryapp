import sys
from django.conf import settings
import django
import json
import os
import openai
from openai import OpenAI

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import LinkedInPost, UserTrends, User

# Fonction pour lire la clé API d'un fichier
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Initialisation du client OpenAI
client = OpenAI(api_key=open_file("openaiapikey.txt"))

BASE_PATH = '/Users/romain-pro/Desktop/factoryapp'

def save_to_database(article_info, user_id):
    print(f"Tentative d'enregistrement dans la base de données pour l'utilisateur ID: {user_id}")
    try:
        user = User.objects.get(pk=user_id)  # Récupère l'objet utilisateur
        print(f"Utilisateur trouvé: {user.email} (ID: {user.id})")
        # Crée un nouvel objet UserTrends avec les informations de l'article
        user_trend = UserTrends(
            user=user,
            titre=article_info['titre'],
            lien=article_info['lien'],
            date=article_info['date'],
            main_topics=article_info['Main_topics'],
            topics_secondaires=article_info['Topics_secondaires'],
            mots_cles=article_info['mots_clés'],
            resume=article_info['Résumé']
        )
        user_trend.save()  # Sauvegarde l'objet dans la base de données
        print(f"L'article '{article_info['titre']}' a été enregistré pour l'utilisateur {user.email}.")
    except User.DoesNotExist:
        print("Utilisateur non trouvé.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans la base de données: {e}")

def lire_prompt_analystgpt():
    prompt_analystgpt_path = os.path.join(BASE_PATH, 'Prompts', 'AnalystGPT.txt')
    with open(prompt_analystgpt_path, 'r', encoding='utf-8') as file:
        return file.read()

def analyser_article_avec_IA(post_content, prompt_analystgpt):
    prompt_complet = prompt_analystgpt
    messages = [{"role": "system", "content": prompt_complet}, {"role": "user", "content": post_content}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            print("Réponse de l'IA:", response.choices[0].message.content)
            return json.loads(response.choices[0].message.content)
        else:
            print("Aucune réponse valide reçue de AnalystGPT.")
            return None
    except Exception as e:
        print(f"Erreur lors de l'analyse IA : {e}")
        return None

def main(user_id, post_id):
    print(f"User ID reçu: {user_id}")
    print(f"Post ID reçu: {post_id}")

    # Récupération du post LinkedIn dans la base de données
    linkedin_post = LinkedInPost.objects.get(id=post_id)
    post_content = linkedin_post.postContent

    print(f"Contenu du post pour l'analyse: {post_content}")

    prompt_analystgpt = lire_prompt_analystgpt()
    article_info = analyser_article_avec_IA(post_content, prompt_analystgpt)
    
    if article_info:
        print("Analyse réussie, enregistrement des résultats...")
        save_to_database(article_info, user_id)
    else:
        print("Analyse non réussie. Aucun résultat à enregistrer.")

    print("Fin de l'analyse et enregistrement des résultats.")

if __name__ == '__main__':
    user_id_arg = sys.argv[1]
    post_id_arg = sys.argv[2]
    main(user_id_arg, post_id_arg)