import json
import ijson
import re
import html




def process_json_files(filename_path):
    genres = set()
    with open(filename_path, 'r', encoding='utf-8') as file:
        for song in ijson.items(file, 'item'):  # 'item' pour chaque chanson
            if "genre" in song:
                genres.add(song['genre'])
            elif "album_genre" in song:
                genres.add(song['album_genre'])
            else:
                genres.add("Undefined")

    with open('public/json/genreBeforeFormat.json', 'w', encoding='utf-8') as json_file:
        list_genre = list(genres)
        json.dump(list_genre, json_file, ensure_ascii=False, indent=4)


def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Le fichier JSON {file_path} n'existe pas.")
        return None
    except json.JSONDecodeError:
        print(f"Erreur lors du décodage du fichier JSON {file_path}.")
        return None

directory_path = 'public/json/song.json'

process_json_files(directory_path)


def extract_genres(subgenres):
    """Extrait tous les genres et sous-genres de manière récursive."""
    genres = set()
    for item in subgenres:
        main_genre = item.get("genre")
        subgenre_list = item.get("subgenres", [])
        if main_genre:
            genres.add(main_genre)  
        
        if isinstance(subgenre_list, list):
            for sub in subgenre_list:
                if isinstance(sub, dict):  
                    genres.update(extract_genres([sub]))  
                elif isinstance(sub, str): 
                    genres.add(sub)  
    
    return genres

genre_file_path = 'public/json/genre.json'
subgenre_file_path = 'public/json/sous-genre.json'
genres = load_json(genre_file_path)
subgenres = load_json(subgenre_file_path)
all_genres_in_subgenres = set()
for item in subgenres:
    main_genre = item.get("genre")
    subgenre_list = item.get("subgenres", [])
 
all_genres_in_subgenres = extract_genres(subgenres)
missing_genres = [genre for genre in genres if genre not in all_genres_in_subgenres]
    
if missing_genres:
    print("Genres manquants dans sous-genre.json :")
    for genre in missing_genres:
        print(genre)
    else:
        print("Tous les genres de genre.json sont présents dans sous-genre.json.")