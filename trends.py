import os
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

BASE_PATH = '/Users/romain-pro/Desktop/factoryapp'


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

client = OpenAI(api_key=open_file("openaiapikey.txt"))



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factoryapp.settings')
django.setup()


# Fonction pour extraire les noms des entreprises à partir des URL
def extract_company_names_from_urls(urls):
    company_names = []
    for url in urls:
        parsed_url = urlparse(url)
        # Extrait la partie du nom de domaine principal, exemple: 'www.securex.be' -> 'securex'
        company_name = parsed_url.netloc.split('.')[-2]
        company_names.append(company_name)
    return company_names

from database.models import User, UserSource
from database.models import UserTrends


def get_user_sources(user_id):
    try:
        user = User.objects.get(pk=user_id)
        user_sources = UserSource.objects.filter(user=user)
        return list(user_sources.values('competitors', 'linkedin', 'references', 'youtube'))
    except User.DoesNotExist:
        return None  # Retourner None si l'utilisateur n'existe pas
    except Exception as e:
        print(str(e))
        return None

# Récupération des sources pour l'utilisateur avec ID = 1
user_sources = get_user_sources(1)


### TRAITEMENT COMPETITORS ###

# Vérification si des sources ont été trouvées
if user_sources:
    # Extraction des URLs des concurrents
    competitors_urls = user_sources[0]['competitors']
    # Extraction des noms des entreprises à partir des URLs
    company_names = extract_company_names_from_urls(competitors_urls)

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

def find_blog_or_news_section(url):
    # Chercher une section blog ou news dans le contenu HTML
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        blog_or_news_content = soup.find_all(['section', 'div'], text=re.compile("blog|news", re.IGNORECASE))
        if blog_or_news_content:
            return [nb.get_text(strip=True) for nb in blog_or_news_content]
        else:
            return []
    except requests.RequestException as e:
        print(f"Erreur lors de la recherche dans {url}: {e}")
        return []

found_blog_urls = []  # Liste pour stocker les URL de blogs valides


for competitor_url in competitors_urls:
    test_blog_url = f"{competitor_url.rstrip('/')}/blog"
    final_url = get_final_url(test_blog_url)

    if final_url and final_url != test_blog_url:
        print(f"Redirection détectée. URL du blog pour {competitor_url}: {final_url}")
        found_blog_urls.append(final_url)
    elif final_url:
        print(f"Blog valide trouvé pour {competitor_url}: {final_url}")
        found_blog_urls.append(final_url)
    else:
        print(f"Aucun blog valide pour {competitor_url}. Recherche de sections 'blog' ou 'news'.")
        blog_or_news_content = find_blog_or_news_section(competitor_url)
        if blog_or_news_content:
            print(f"Contenu 'blog' ou 'news' trouvé pour {competitor_url}:")
            for content in blog_or_news_content:
                print(content)


###   POUR CHAQUE BLOG TROUVER _ FIND BLOG ARTICLES ###

TEMP_DIR = os.path.join(BASE_PATH, 'Temp')

# Assurer la création du dossier temporaire
os.makedirs(TEMP_DIR, exist_ok=True)


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
for blog_url, company_name in zip(found_blog_urls, company_names):
    temp_file_name = scraper_et_sauvegarder_blog(blog_url)
    temp_response_file = analyser_contenu_avec_IA(temp_file_name, prompt_extractgpt, company_name)
    if temp_response_file:
        # Modification ici: Renommer le fichier temporaire pour chaque entreprise
        final_file_name = os.path.join(TEMP_DIR, f'set_up_blog.{company_name}.txt')
        os.rename(temp_response_file, final_file_name)
        print(f"Résultats pour {company_name} sauvegardés dans {final_file_name}")
    os.remove(temp_file_name)  # Supprimer le fichier HTML temporaire après analyse

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



### TRAITEMENT REFERENCES ###
        
        # Fonction pour lire le prompt de referenceGPT
def lire_prompt_referencegpt():
    prompt_referencegpt = os.path.join(BASE_PATH, 'Prompts', 'ReferenceGPT.txt')
    with open(prompt_referencegpt, 'r', encoding='utf-8') as file:
        return file.read()

# Chargement du prompt pour referenceGPT
prompt_referencegpt = lire_prompt_referencegpt()

# Extraction des URLs des "references"
references_urls = user_sources[0]['references']

# Fonction pour analyser les références avec ExtractGPT
def analyser_references_avec_IA(file_path, prompt_referencegpt, company_name):
    with open(file_path, 'r') as file:
        content = file.read()

    messages = [
        {"role": "system", "content": prompt_referencegpt},
        {"role": "user", "content": content}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            max_tokens=4000
        )

        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            temp_response_file_path = os.path.join(TEMP_DIR, f'response_{company_name}_reference.txt')
            with open(temp_response_file_path, 'w') as temp_file:
                temp_file.write(f"json_response_{company_name}_reference = '''{result}'''\n")
            return temp_response_file_path
        else:
            print(Fore.RED + "Aucune réponse valide pour " + file_path + Style.RESET_ALL)
            return None

    except Exception as e:
        print(Fore.RED + "Erreur lors de l'analyse IA pour " + file_path + ": " + str(e) + Style.RESET_ALL)
        return None

# Traiter chaque URL de référence
temp_files_references = []
for reference_url, company_name in zip(references_urls, company_names):
    temp_file_name = scraper_et_sauvegarder_blog(reference_url)  # Utiliser la même fonction de scraping
    temp_response_file = analyser_references_avec_IA(temp_file_name, prompt_referencegpt, company_name)
    if temp_response_file:
        temp_files_references.append(temp_response_file)
    os.remove(temp_file_name)

# Compiler les fichiers de références
compiled_references_path = os.path.join(TEMP_DIR, 'set_up_references.txt')
with open(compiled_references_path, 'w') as compiled_file:
    for file_path in temp_files_references:
        with open(file_path, 'r') as temp_file:
            compiled_file.write(temp_file.read() + '\n')
        os.remove(file_path)

# Lire le fichier compilé de références
with open(compiled_references_path, 'r') as compiled_file:
    exec(compiled_file.read())

# Imprimer les articles de référence
for company_name in company_names:
    json_response_var = f'json_response_{company_name}_reference'
    if json_response_var in globals():
        print(f"Articles de référence pour {company_name}:")
        imprimer_articles(globals()[json_response_var])



### CLEAN AND GROUP DATA ###


# Chemin du répertoire temporaire
temp_dir_path = '/Users/romain-pro/Desktop/factoryapp/Temp/'
output_file_path = '/Users/romain-pro/Desktop/factoryapp/Temp/combined_articles.json'

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

# Nettoyer et combiner les contenus JSON de tous les fichiers du répertoire
combined_data = clean_and_combine_json(temp_dir_path)

# Sauvegarder dans un nouveau fichier
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(combined_data, output_file, indent=4, ensure_ascii=False)

print("Fusion terminée, fichier créé :", output_file_path)



### TRAITEMENTs ET  ###

# Chemin du fichier combiné
combined_file_path = '/Users/romain-pro/Desktop/factoryapp/Temp/combined_articles.json'



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

user_id = 1  

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

TRENDS_PATH = os.path.join(BASE_PATH, 'Trends')
combined_file_path = os.path.join(BASE_PATH, 'Temp', 'combined_articles.json')

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

