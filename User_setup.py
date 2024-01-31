import requests
from bs4 import BeautifulSoup
import json
import os
from openai import OpenAI
import sys

# Chemin de base du projet et autres chemins nécessaires
BASE_PATH = '/Users/romain-pro/Desktop/factoryapp/'
PROMPT_PATH = os.path.join(BASE_PATH, 'Prompts')
SCRAPED_CONTENT_PATH = os.path.join(BASE_PATH, 'Scraped_Content')
CLEANED_CONTENT_PATH = os.path.join(BASE_PATH, 'Cleaned_Content')



def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

# Configuration du client OpenAI
client = OpenAI(api_key=open_file("openaiapikey.txt"))

# Fonction pour scraper la page et chercher tous les liens
def scraper_page_et_liens(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erreur lors de l'accès à l'URL {url} : Statut {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        liens = set()
        for lien in soup.find_all('a', href=True):
            href = lien['href']
            if href.startswith('/'):
                # Construire l'URL complet en évitant les doublons
                url_complet = url.rstrip('/') + href
            elif not href.startswith('http'):
                # Gérer les autres cas d'URL relatifs
                url_complet = url + href
            else:
                # Utiliser l'URL tel quel s'il est déjà complet
                url_complet = href
            liens.add(url_complet)

        return liens
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la connexion à {url} : {e}")
        return []

# Fonction pour traiter les données reçues de l'API et scraper l'URL de la compagnie
def traiter_donnees_api_et_scraper(data):
    url_company = data.get('company_url')
    if not url_company:
        print("URL de la compagnie non fournie dans les données de l'API.")
        return

    print("Début du scraping de l'URL de la compagnie:", url_company)
    liens = scraper_page_et_liens(url_company)

    for lien in liens:
        print(lien)
    
    return liens

### CLASSIFICATION DES LIENS ###

def classifier_liens(liens):
    print("Classification des liens...")

    PROMPT_ClassifyAI = os.path.join(PROMPT_PATH, 'ClassifyAI.txt')
    classify_prompt = open_file(PROMPT_ClassifyAI)

    conversation = [
        {"role": "system", "content": classify_prompt},
        {"role": "user", "content": f"Classifiez ces liens: {json.dumps(list(liens))}"}
    ]

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=conversation
    )

    if response.choices:
        classification_result = response.choices[0].message.content
        print("Classification terminée.")
        return classification_result
    else:
        print("Erreur lors de la classification des liens.")
        return {}

### Extract content from Important company business content links ### 

def scrape_to_json(link, json_filename):
    headers = {'User-Agent': 'Mozilla/5.0'}  # Ajout d'un User-Agent
    try:
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text(strip=True)
            data = {'url': link, 'content': content}
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file)
        else:
            print(f"Erreur lors de l'accès à {link}: Statut {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la connexion à {link} : {e}")


### CLEAN DE LA DATA ###

# Chemin vers le fichier de prompt pour CleanerGPT
prompt_cleanergpt_path = os.path.join(PROMPT_PATH, 'CleanerGPT.txt')
with open(prompt_cleanergpt_path, 'r', encoding='utf-8') as file:
    prompt_cleanergpt = file.read()

# Fonction pour analyser le contenu avec CleanerGPT
def analyze_content_with_cleanergpt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_content = json.load(file)
        content = json_content.get('content', '')
    except UnicodeDecodeError:
        print(f"Erreur de décodage UTF-8 dans le fichier : {file_path}")
        return ""

    messages = [{"role": "system", "content": prompt_cleanergpt},
                {"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages
    )

    return response.choices[0].message.content if response.choices else ""

# Analyser et nettoyer le contenu de chaque fichier JSON
for file_name in sorted(os.listdir(SCRAPED_CONTENT_PATH)):
    file_path = os.path.join(SCRAPED_CONTENT_PATH, file_name)
    print(f"Nettoyage du fichier : {file_name}")
    cleaned_content = analyze_content_with_cleanergpt(file_path)

    # Enregistrement du contenu nettoyé
    result_file_path = os.path.join(BASE_PATH, 'Cleaned_Content', f"cleaned_{file_name}")
    os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        result_file.write(cleaned_content)
    print(f"Contenu nettoyé enregistré pour {file_name}")



### BUSINESS ANALYSE ###
    
def compiler_json_en_global():
    global_file_path = os.path.join(BASE_PATH, 'Global.txt')
    with open(global_file_path, 'w', encoding='utf-8') as global_file:
        for file_name in sorted(os.listdir(CLEANED_CONTENT_PATH)):
            if file_name.endswith('.txt') and not file_name.startswith('.'):
                file_path = os.path.join(CLEANED_CONTENT_PATH, file_name)
                with open(file_path, 'r', encoding='utf-8') as txt_file:
                    content = txt_file.read()
                    global_file.write(content + '\n\n')

def analyser_avec_business_setupgpt():
    global_file_path = os.path.join(BASE_PATH, 'Global.txt')
    with open(global_file_path, 'r', encoding='utf-8') as global_file:
        content = global_file.read()

    prompt_business_setupgpt_path = os.path.join(PROMPT_PATH, 'Business_setupGPT.txt')
    prompt_business_setupgpt = open_file(prompt_business_setupgpt_path)

    messages = [{"role": "system", "content": prompt_business_setupgpt},
                {"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages
    )

    return response.choices[0].message.content if response.choices else ""


### PREPARATION JSON ET ENVOI A BUBLE ###

# Fonction pour envoyer les données au webhook
def send_to_webhook(data, webhook_url):
    try:
        response = requests.post(webhook_url, json=data)
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi au webhook: {e}")
        return None

# Fonction pour préparer et envoyer les résumés
def send_resume(data, email):
    resume_data = {
        "resume": data["résumer"]["resume"],
        "email": email
    }
    webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/technical analyse/initialize"
    return send_to_webhook(resume_data, webhook_url)

# Fonction pour préparer et envoyer les produits/services
def send_produits(resultat_json, user_email):
    produits = resultat_json["Produits/service"]

    for key, value in produits.items():
        if key.startswith("Produits_"):
            product_name = value
            description_key = f"description_{key}"
            product_description = produits.get(description_key, "Description non disponible")

            produit_data = {
                "produit_x": product_name,
                "description_produit_x": product_description,
                "email": user_email
            }
            webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/set-up_produits/initialize"
            envoyer_a_bubble(produit_data, webhook_url)

# Fonction pour préparer et envoyer les forces
def send_forces(data, email):
    for key, value in data["points forts/force"].items():
        force_data = {
            "force_x": value,
            "email": email
        }
        webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/set_up_force/initialize"
        send_to_webhook(force_data, webhook_url)

def envoyer_a_bubble(data, webhook_url):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(webhook_url, headers=headers, json=data)
        return response.status_code, response.text
    except Exception as e:
        print(f"Erreur lors de l'envoi des données à Bubble: {e}")
        return None, str(e)

def supprimer_fichiers(dossier):
    for fichier in os.listdir(dossier):
        if fichier.endswith(".txt") or fichier.endswith(".json"):
            chemin_fichier = os.path.join(dossier, fichier)
            os.remove(chemin_fichier)
            print(f"Fichier {fichier} supprimé du dossier {dossier}.")


def main(data_as_json):
    data = json.loads(data_as_json)
    url_company = data.get('company_url')
    user_email = data.get('email')  # Assurez-vous que cette donnée est fournie

    if not url_company:
        print("URL de la compagnie non fournie dans les données.")
        return

    print("Début du scraping de l'URL de la compagnie:", url_company)
    liens = scraper_page_et_liens(url_company)

    business_links = []
    if liens:
        classification_response = classifier_liens(liens)
        print(f"Réponse de classification : {classification_response}")
        classification_result = json.loads(classification_response)
        business_links = classification_result.get("Important company business content", [])

    for i, link in enumerate(business_links):
        json_filename = os.path.join(SCRAPED_CONTENT_PATH, f'scraped_{i+1}.json')
        scrape_to_json(link, json_filename)

    # Nettoyer le contenu de chaque fichier JSON après le scraping
    for file_name in sorted(os.listdir(SCRAPED_CONTENT_PATH)):
        if file_name.endswith('.json') and not file_name.startswith('.'):
            file_path = os.path.join(SCRAPED_CONTENT_PATH, file_name)
            print(f"Nettoyage du fichier : {file_name}")
            cleaned_content = analyze_content_with_cleanergpt(file_path)

            # Enregistrement du contenu nettoyé en format TXT
            txt_file_name = file_name.replace('.json', '.txt')
            result_file_path = os.path.join(CLEANED_CONTENT_PATH, txt_file_name)
            os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            with open(result_file_path, 'w', encoding='utf-8') as result_file:
                result_file.write(cleaned_content)
            print(f"Contenu nettoyé enregistré pour {txt_file_name}")

    # Compilation des fichiers TXT en Global.txt
    compiler_json_en_global()

    # Analyse avec Business_setupGPT
    analyse_resultat = analyser_avec_business_setupgpt()
    print("Résultat de l'analyse avec Business_setupGPT :")
    print(analyse_resultat)

    # Traitement et envoi des données à Bubble
    resultat_json = json.loads(analyse_resultat)

    # Envoyer le résumé
    resume_data = {
        "resume": resultat_json["résumer"]["resume"],
        "email": user_email
    }
    envoyer_a_bubble(resume_data, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/technical_analyse")

    # Envoyer les produits avec leur description
    produits = resultat_json["Produits/service"]
    for key, value in produits.items():
        if key.startswith("Produits_"):
            product_name = value
            description_key = f"description_{key}"
            product_description = produits.get(description_key, "Description non disponible")
            produit_data = {
                "produit_x": product_name,
                "description_produit_x": product_description,
                "email": user_email
            }
            webhook_url = "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/set-up_produits"
            envoyer_a_bubble(produit_data, webhook_url)

    # Envoyer les forces
    for key, value in resultat_json["points forts/force"].items():
        force_data = {
            "force_x": value,
            "email": user_email
        }
        envoyer_a_bubble(force_data, "https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/set_up_force")

    supprimer_fichiers(SCRAPED_CONTENT_PATH)
    supprimer_fichiers(CLEANED_CONTENT_PATH)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data_as_json = sys.argv[1]
        main(data_as_json)
    else:
        print("Aucune donnée fournie.")