import os
import sys
import requests
import json
import re
from colorama import Fore, Style
import colorama
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup
import datetime
import subprocess
import colorama
import tempfile
import shutil
import django
from openai import OpenAI
from django.core.exceptions import ObjectDoesNotExist


# Initialisation de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()

from database.models import User, UserSource, UserTrends

# Fonction pour lire la clé API d'un fichier
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Initialisation du client OpenAI
client = OpenAI(api_key=open_file("openaiapikey.txt"))


""""
# Récupérer l'ID de l'utilisateur depuis l'argument de la ligne de commande
if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    print("Aucun ID utilisateur fourni.")
    sys.exit(1)
"""

user_id = '40'

# Création d'un répertoire temporaire spécifique à l'utilisateur
BASE_PATH = '/Users/romain-pro/Desktop/factoryapp'
TEMP_DIR = os.path.join(BASE_PATH, 'Temp', str(user_id))  # Utilisez str(user_id) pour convertir l'ID en une chaîne
os.makedirs(TEMP_DIR, exist_ok=True)

user_temp_dir = TEMP_DIR


print(f"Répertoire temporaire pour l'utilisateur {user_id} : {TEMP_DIR}")

def get_user_sources(user_id):
    """
    Récupère les sources de l'utilisateur spécifié par son ID.
    """
    try:
        user = User.objects.get(pk=user_id)
        user_sources = UserSource.objects.filter(user_id=user_id).first()
        if user_sources:
            # Utiliser une fonction helper pour traiter les champs qui pourraient être des listes ou des chaînes
            def process_field(field):
                if isinstance(field, str):
                    return field.split(',')
                elif isinstance(field, list):
                    return field
                else:
                    return []

            return {
                'competitors': process_field(user_sources.competitors),
                'linkedin': user_sources.linkedin,
                'references': process_field(user_sources.references),
                'youtube': user_sources.youtube
            }
    except ObjectDoesNotExist:
        print(f"L'utilisateur avec l'ID {user_id} n'existe pas dans la base de données.")
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération des sources pour l'utilisateur {user_id}: {e}")
        return None

def extract_company_names_from_urls(urls):
    """
    Extrait les noms des entreprises à partir des URLs fournies.
    """
    company_names = []
    for url in urls:
        parsed_url = urlparse(url.strip())  # strip() pour enlever les espaces en début/fin d'URL
        # Extrait la partie du nom de domaine principal, exemple: 'www.securex.be' -> 'securex'
        domain_parts = parsed_url.netloc.split('.')
        if 'www' in domain_parts:
            company_name = domain_parts[1]  # Prendre la partie suivante si 'www' est présent
        else:
            company_name = domain_parts[0]  # Prendre la première partie sinon
        company_names.append(company_name.capitalize())
    return company_names

user_sources = get_user_sources(user_id)

if user_sources:
    print("Sources récupérées avec succès pour l'utilisateur ID:", user_id)
    print(user_sources)
else:
    print("Impossible de récupérer les sources pour l'utilisateur ID:", user_id)
    sys.exit(1)

# Maintenant, vous pouvez extraire les URL des concurrents en utilisant les données de user_sources
competitors_urls = user_sources.get('competitors', [])  # Utilisez une liste vide par défaut si la clé 'competitors' n'existe pas

# Maintenant, vous pouvez utiliser la variable competitors_urls dans votre code
company_names = extract_company_names_from_urls(competitors_urls)
print("Noms des entreprises extraites des URLs :", company_names)


# Suite du nouveau script

# Suite du code après l'extraction des noms des entreprises
def get_final_url(url):
    # Obtenir l'URL finale après redirection
    try:
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            return response.url  # URL finale après redirection
        else:
            return None
    except requests.RequestException:
        return None



def find_and_process_blog_url(competitor_url, found_blog_urls):
    test_blog_url = f"{competitor_url.rstrip('/')}/blog"
    response = requests.get(test_blog_url, allow_redirects=True)
    final_url = response.url if response.status_code == 200 else None

    if final_url and final_url != test_blog_url:
        print(f"Redirection détectée. URL du blog pour {competitor_url}: {final_url}")
        found_blog_urls.append(final_url)
    elif final_url:
        print(f"Blog valide trouvé pour {competitor_url}: {final_url}")
        found_blog_urls.append(final_url)
    else:
        print(f"Aucun blog valide pour {competitor_url} avec '/blog'. Utilisation de l'URL de base comme URL de blog.")
        found_blog_urls.append(competitor_url)

found_blog_urls = []
for competitor_url in user_sources.get('competitors', []):
    find_and_process_blog_url(competitor_url, found_blog_urls)

print(f"Voici les urls de blog trouvées :{found_blog_urls}")


# Initialisation de colorama
colorama.init(autoreset=True)

def scraper_et_sauvegarder_blog(url):
    print(f"Scraping du blog : {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Sauvegarder le contenu HTML dans un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html') as temp_file:
        temp_file.write(str(soup))
        temp_file_name = temp_file.name

    print(f"Contenu HTML sauvegardé dans {temp_file_name}")
    return temp_file_name

def analyser_contenu_avec_IA(file_path, prompt_extractgpt, company_name):
    with open(file_path, 'r') as file:
        content = file.read()

    messages = [
        {"role": "system", "content": prompt_extractgpt},
        {"role": "user", "content": content}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            max_tokens=4000  # Ajustez selon vos besoins
        )

        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            temp_response_file_path = os.path.join(TEMP_DIR, f'response_{company_name}.txt')
            with open(temp_response_file_path, 'w') as temp_file:
                temp_file.write(f"json_response_{company_name} = '''{result}'''\n")
            return temp_response_file_path
        else:
            print(Fore.RED + "Aucune réponse valide pour " + file_path + Style.RESET_ALL)
            return None

    except Exception as e:
        print(Fore.RED + "Erreur lors de l'analyse IA pour " + file_path + ": " + str(e) + Style.RESET_ALL)
        return None

def lire_prompt_extractgpt():
    prompt_extractgpt = os.path.join(BASE_PATH, 'Prompts', 'ExtractGPT.txt')
    with open(prompt_extractgpt, 'r', encoding='utf-8') as file:
        return file.read()


# Chargement du prompt pour ExtractGPT

prompt_extractgpt = lire_prompt_extractgpt()

temp_files = []
for blog_url in found_blog_urls:
    print(f"Traitement du blog : {blog_url}")
    # Utilisez ici blog_url directement pour le scraping et l'analyse
    temp_file_name = scraper_et_sauvegarder_blog(blog_url)
    identifier = quote(blog_url, safe='')  # Utilisez blog_url pour identifier si nécessaire
    temp_response_file = analyser_contenu_avec_IA(temp_file_name, prompt_extractgpt, identifier)
    
    if temp_response_file:
        final_file_name = os.path.join(user_temp_dir, f'analysis_result_{identifier}.txt')
        os.rename(temp_response_file, final_file_name)
        print(f"Résultats de l'analyse sauvegardés dans {final_file_name}")
    
    os.remove(temp_file_name)  # Nettoyez après analyse
# Fonction pour imprimer les articles
def imprimer_articles(json_response):
    try:
        articles = json.loads(json_response)
        for article_key, article_details in articles.items():
            print(f"{article_key}:")
            for key, value in article_details.items():
                print(f"  {key}: {value}")
            print()
    except json.JSONDecodeError as e:
        print("Erreur lors de la conversion JSON:", e)

# Imprimer les articles pour chaque entreprise
for company_name in company_names:
    file_path = os.path.join(TEMP_DIR, f'set_up_blog.{company_name}.txt')
    try:
        with open(file_path, 'r') as file:
            json_response = file.read()
            print(f"Articles pour {company_name}:")
            imprimer_articles(json_response)
    except FileNotFoundError:
        print(f"Le fichier pour {company_name} est introuvable.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier pour {company_name}: {e}")




def clean_and_combine_json(directory):
    combined_data = {}
    article_counter = 1  # Compteur pour la renumérotation unique des articles

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):  # Traiter uniquement les fichiers .txt
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().split("'''", 1)[1].rsplit("'''", 1)[0].strip()
                try:
                    data = json.loads(content)
                    for article_key in list(data.keys()):
                        new_key = f"article_{article_counter}"  # Créer une nouvelle clé unique
                        combined_data[new_key] = data[article_key]
                        article_counter += 1  # Incrémenter le compteur pour le prochain article
                except json.JSONDecodeError as e:
                    print(f"Erreur de décodage JSON dans le fichier {file_path}: {e}")

    return combined_data

temp_dir_path = TEMP_DIR
output_file_path = os.path.join(temp_dir_path, 'combined_articles.json')

# Nettoyer et combiner les contenus JSON de tous les fichiers du répertoire
combined_data = clean_and_combine_json(temp_dir_path)

# Sauvegarder dans un nouveau fichier
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(combined_data, output_file, indent=4, ensure_ascii=False)

print("Fusion terminée, fichier créé :", output_file_path)



### TRAITEMENTs ET  ###

# Chemin du fichier combiné
combined_file_path = os.path.join(TEMP_DIR, 'combined_articles.json')



def find_link_after_text(url, target_text):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        target = soup.find(text=re.compile(target_text))
        if target:
            next_link = target.find_next('a', href=True)
            if next_link and next_link['href']:
                return next_link['href']
    return None

def update_article_links(file_path, target_website, target_text):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    updated_count = 0
    for article_key in data:
        if target_website in data[article_key]['lien']:
            new_link = find_link_after_text(data[article_key]['lien'], target_text)
            if new_link:
                data[article_key]['lien'] = new_link
                updated_count += 1

    if updated_count > 0:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return f"{updated_count} liens mis à jour avec succès."
    else:
        return "Aucun lien à mettre à jour n'a été trouvé."

# Appel de la fonction
result = update_article_links(combined_file_path, "www.hralert.be", "Pour aller plus loin")
print(result)

### ANALYSES DES CONTENUS ###

# Fonction pour sauvegarder les informations de l'article dans la base de données
def save_to_database(article_info, user_id):
    try:
        user = User.objects.get(pk=user_id)  # Récupère l'objet utilisateur
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
        print(f"L'article '{article_info['titre']}' a été enregistré pour l'utilisateur {user.name}.")
    except User.DoesNotExist:
        print("Utilisateur non trouvé.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans la base de données: {e}")

combined_file_path = '/Users/romain-pro/Desktop/factoryapp/Temp/combined_articles.json'

TRENDS_PATH = TEMP_DIR
combined_file_path = os.path.join(TEMP_DIR, 'combined_articles.json')

# Assurer la création du dossier Trends
os.makedirs(TRENDS_PATH, exist_ok=True)

def scrape_article_content(article):
    lien = article['lien']  # Extraction du lien
    response = requests.get(lien)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = ' '.join(soup.stripped_strings)
        article['contenu'] = text_content
        return article
    else:
        return {"erreur": f"Impossible de récupérer le contenu de {lien}"}

def lire_prompt_analystgpt():
    prompt_analystgpt_path = os.path.join(BASE_PATH, 'Prompts', 'AnalystGPT.txt')
    with open(prompt_analystgpt_path, 'r', encoding='utf-8') as file:
        return file.read()

def analyser_article_avec_IA(article_info, prompt_analystgpt):
    article_json = json.dumps(article_info, indent=4, ensure_ascii=False)
    prompt_complet = prompt_analystgpt
    messages = [{"role": "system", "content": prompt_complet}, 
                {"role": "user", "content": article_json}]
    try:
        response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
        if response.choices:
            # Afficher la réponse de l'IA
            print("Réponse de l'IA:", response.choices[0].message.content)
            # Convertir la réponse en dictionnaire
            return json.loads(response.choices[0].message.content)
        else:
            print("Aucune réponse valide reçue de AnalystGPT.")
            return None
    except Exception as e:
        print(f"Erreur lors de l'analyse IA : {e}")
        return None

def enregistrer_resultat(resultat, article_number):
    with open(os.path.join(TRENDS_PATH, f'article_{article_number}.txt'), 'w', encoding='utf-8') as file:
        file.write(resultat)

# Charger le prompt pour AnalystGPT
prompt_analystgpt = lire_prompt_analystgpt()

# Lire et traiter tous les articles
with open(combined_file_path, 'r', encoding='utf-8') as file:
    articles = json.load(file)

# Pour chaque article, scrape le contenu, analyse-le avec l'IA et sauvegarde les résultats
for index, (article_key, article) in enumerate(articles.items()):
    scraped_article = scrape_article_content(article)
    if 'erreur' not in scraped_article:
        analysis_result = analyser_article_avec_IA(scraped_article, prompt_analystgpt)
        if isinstance(analysis_result, dict):  # Vérifie que le résultat est un dictionnaire
            save_to_database(analysis_result, user_id)
        elif analysis_result is None:
            print(f"Erreur lors de l'analyse de l'article {index + 1}. Aucun résultat à enregistrer.")
        else:
            print(f"Le résultat de l'analyse n'est pas dans le format attendu pour l'article {index + 1}.")
    else:
        print(scraped_article['erreur'])

# Supprimer le dossier temporaire
try:
    shutil.rmtree(TEMP_DIR)
    print(f"Dossier temporaire {TEMP_DIR} supprimé avec succès.")
except Exception as e:
    print(f"Erreur lors de la suppression du dossier temporaire {TEMP_DIR}: {e}")


""""
# Appel à User_trends.py avec l'ID de l'utilisateur
path_to_user_trends = os.path.join(BASE_PATH, 'User_trends.py')
subprocess.call(["python", path_to_user_trends, str(user_id)])
"""


# Fin du script
sys.exit(0)