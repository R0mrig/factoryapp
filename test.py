import os
import re
import json


trends_dir = '/Users/romain-pro/Desktop/factoryapp/Trends'
sources_file_path = '/Users/romain-pro/Desktop/factoryapp/Sources.json'
trends_file_path = '/Users/romain-pro/Desktop/factoryapp/Trends.json'

def clean_and_update_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Supprimer les caractères de contrôle
            cleaned_content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
            # Charger le contenu nettoyé comme JSON pour vérifier sa validité
            json.loads(cleaned_content)

        # Réécrire le fichier avec le contenu nettoyé
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)
        return True
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON dans le fichier {file_path}: {e}")
        return False

def clean_and_update_all_json_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):  # Filtrer les fichiers .txt
            file_path = os.path.join(directory, filename)
            if not clean_and_update_json_file(file_path):
                print(f"Erreur lors de la mise à jour du fichier {file_path}")

# Chemin du répertoire contenant les fichiers à nettoyer
trends_dir = '/Users/romain-pro/Desktop/factoryapp/Trends'

# Nettoyer et mettre à jour tous les fichiers JSON dans le dossier Trends
clean_and_update_all_json_files(trends_dir)



def combine_json_files(directory):
    sources_data = []
    trends_data = []

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):  # Traiter uniquement les fichiers .txt
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    for article_key, article_data in data.items():
                        sources_data.append({
                            "lien": article_data.get("lien"),
                            "date": article_data.get("date"),
                            "mots_clés": article_data.get("mots_clés")
                        })
                        trends_data.append({
                            "Main_topics": article_data.get("Main_topics"),
                            "Topics_secondaires": article_data.get("Topics_secondaires"),
                            "mots_clés": article_data.get("mots_clés")
                        })
                except json.JSONDecodeError as e:
                    print(f"Erreur de décodage JSON dans le fichier {file_path}: {e}")

    return sources_data, trends_data

# Combinaison des fichiers JSON
sources_data, trends_data = combine_json_files(trends_dir)

# Sauvegarde des données combinées
with open(sources_file_path, 'w', encoding='utf-8') as file:
    json.dump(sources_data, file, indent=4, ensure_ascii=False)

with open(trends_file_path, 'w', encoding='utf-8') as file:
    json.dump(trends_data, file, indent=4, ensure_ascii=False)

print("Fichiers 'Sources' et 'Trends' créés avec succès.")
