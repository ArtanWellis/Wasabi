import json
import ijson
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
import argparse

def clean_genre_name(genre):
    if not genre:
        return ""
        
    # Dictionnaire de conversion des caractères spéciaux HTML
    html_chars = {
        # Caractères portugais/espagnols
        '&#xe3;': 'ã',    # ã
        '&#xf5;': 'õ',    # õ
        '&#xf1;': 'ñ',    # ñ
        
        # Caractères français
        '&#xe9;': 'é',    # é
        '&#xe8;': 'è',    # è
        '&#xea;': 'ê',    # ê
        '&#xe0;': 'à',    # à
        '&#xe2;': 'â',    # â
        '&#xf4;': 'ô',    # ô
        '&#xfb;': 'û',    # û
        '&#xee;': 'î',    # î
        '&#xef;': 'ï',    # ï
        '&#xe7;': 'ç',    # ç
        
        # Caractères espagnols
        '&#xed;': 'í',    # í
        '&#xe1;': 'á',    # á
        '&#xf3;': 'ó',    # ó
        '&#xfa;': 'ú',    # ú
        
        # Caractères allemands
        '&#xe4;': 'ä',    # ä
        '&#xeb;': 'ë',    # ë
        '&#xfc;': 'ü',    # ü
        '&#xff;': 'ÿ',    # ÿ
        
        # Caractères spéciaux
        '&#x200e;': '',   # Marqueur gauche-à-droite
        '&#x200f;': '',   # Marqueur droite-à-gauche
        '&amp;': '&',     # &
        '&apos;': "'",    # '
        '&quot;': '"',    # "
        '&lt;': '<',      # <
        '&gt;': '>'       # >
    }
    
    # Conversion en minuscules
    genre = genre.lower()
    
    # Remplacement des caractères spéciaux
    for html, char in html_chars.items():
        genre = genre.replace(html, char)
    
    # Nettoyage des espaces
    return genre.strip()

def process_genre_evolution(limit=None):
    songs_path = 'public/json/song.json'
    albums_path = 'public/json/album.json'
    artists_path = 'public/json/artist-without-members.json'
    output_path = 'public/karim/genre_evolution.json'
    
    # Chargement optimisé des albums
    print("Chargement des albums...")
    album_info = {}
    with open(albums_path, 'rb') as f:  # Utilisation de 'rb' pour de meilleures performances
        parser = ijson.parse(f)
        current_album = {}
        
        for prefix, event, value in parser:
            if prefix.endswith('._id.$oid'):
                if current_album:
                    album_info[current_album.get('id')] = {
                        'country': current_album.get('country', ''),
                        'id_artist': current_album.get('id_artist', ''),
                        'name': current_album.get('name', ''),
                        'publicationDate': current_album.get('publicationDate', ''),
                        'cover_small': current_album.get('cover_small', '')
                    }
                current_album = {'id': value}
            elif prefix.endswith('.country'):
                current_album['country'] = value
            elif prefix.endswith('.id_artist.$oid'):
                current_album['id_artist'] = value
            elif prefix.endswith('.name'):
                current_album['name'] = value
            elif prefix.endswith('.publicationDate'):
                current_album['publicationDate'] = value
            elif prefix.endswith('.cover.small'):
                current_album['cover_small'] = value
        
        # Dernier album
        if current_album:
            album_info[current_album.get('id')] = {
                'country': current_album.get('country', ''),
                'id_artist': current_album.get('id_artist', ''),
                'name': current_album.get('name', ''),
                'publicationDate': current_album.get('publicationDate', ''),
                'cover_small': current_album.get('cover_small', '')
            }

    # Chargement des artistes
    print("Chargement des artistes...")
    artist_info = {}
    with open(artists_path, 'rb') as f:
        artists = ijson.items(f, 'item')
        
        print("Début du chargement des artistes...")
        
        for artist in artists:
            artist_id = artist.get('_id', {}).get('$oid', '')
            if artist_id:
                artist_info[artist_id] = {
                    'name': artist.get('name', ''),
                    'picture_small': artist.get('picture', {}).get('small', ''),
                    'country': artist.get('location', {}).get('country', '')
                }

    # Structure pour stocker les données
    genre_evolution = defaultdict(lambda: defaultdict(lambda: {
        "count": 0,
        "rank_sum": 0,
        "rank_avg": 0,
        "albums": {},
        "artists": {}  # Nouvelle structure pour les artistes
    }))
    
    # Traitement des chansons
    print("Traitement des chansons...")
    with open(songs_path, 'rb') as f:
        songs = ijson.items(f, 'item')
        for i, song in enumerate(songs):
            if limit and i >= limit:
                break
                
            # Extraction rapide des données nécessaires
            pub_date = song.get('publicationDate', '')
            genre = clean_genre_name(song.get('album_genre', ''))
            rank = song.get('rank', 0)
            
            # Gestion des deux formats possibles d'id_album
            album_id = song.get('id_album', '')
            if isinstance(album_id, dict):
                album_id = album_id.get('$oid', '')
            
            if not all([pub_date, genre, rank, album_id]):
                continue
                
            try:
                year = str(datetime.strptime(pub_date, '%Y-%m-%d').year)
                rank = float(rank)
                
                # Mise à jour des données par année/genre
                if year not in genre_evolution:
                    genre_evolution[year] = defaultdict(dict)
                if genre not in genre_evolution[year]:
                    genre_evolution[year][genre] = {
                        "count": 0,
                        "rank_sum": 0,
                        "rank_avg": 0,
                        "albums": {},
                        "artists": {}
                    }
                
                year_genre = genre_evolution[year][genre]
                year_genre["count"] += 1
                year_genre["rank_sum"] += rank
                year_genre["rank_avg"] = year_genre["rank_sum"] / year_genre["count"]
                
                # Récupération des infos de l'album et de l'artiste
                album_info_current = album_info.get(album_id, {})
                artist_id = album_info_current.get('id_artist', '')

        
                
                # Mise à jour des statistiques de l'artiste
                if artist_id:
                    if artist_id not in year_genre["artists"]:
                        artist_data = artist_info.get(artist_id, {})  # Récupérer les infos de l'artiste depuis artist_info
                        year_genre["artists"][artist_id] = {
                            "name": artist_data.get('name', 'Artiste inconnu'),
                            "picture_small": artist_data.get('picture_small', ''),
                            "country": artist_data.get('country', ''),
                            "count": 0,
                            "rank_sum": 0,
                            "rank_avg": 0
                        }
                    
                    artist_stats = year_genre["artists"][artist_id]
                    artist_stats["count"] += 1
                    artist_stats["rank_sum"] += rank
                    artist_stats["rank_avg"] = artist_stats["rank_sum"] / artist_stats["count"]

                # Mise à jour des statistiques de l'album
                if album_id not in year_genre["albums"]:
                    year_genre["albums"][album_id] = {
                        "count": 0,
                        "rank_sum": 0,
                        "rank_avg": 0,
                        "country": album_info_current.get('country', ''),
                        "name": album_info_current.get('name', ''),
                        "cover_small": album_info_current.get('cover_small', ''),
                        "id_artist": artist_id
                    }
                
                album_stats = year_genre["albums"][album_id]
                album_stats["count"] += 1
                album_stats["rank_sum"] += rank
                album_stats["rank_avg"] = album_stats["rank_sum"] / album_stats["count"]

            except (ValueError, TypeError):
                continue
    
    # Filtrage des années et sauvegarde
    filtered_evolution = {
        year: data 
        for year, data in genre_evolution.items() 
        if 1950 <= int(year) <= 2026
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_evolution, f, ensure_ascii=False)
    
    print("Traitement terminé!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Traite les données de chansons pour l\'évolution des genres.')
    parser.add_argument('--limit', type=int, help='Nombre limite de chansons à traiter (optionnel)')
    args = parser.parse_args()
    process_genre_evolution(args.limit)
