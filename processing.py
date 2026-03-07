import json
import html
import re
import numpy as np
from collections import Counter
from database.database import MangaDatabase
from sentence_transformers import SentenceTransformer

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    final_text = text.split('\n')

    return final_text[0].strip()

def clean_description_from_html(manga) -> str:
    description = clean_text(manga.get("description", "")) or "No description available."
    return description

def get_popular_tags(manga_data: list, min_count: int) -> set:
    all_tags = [tag["name"] for manga in manga_data for tag in manga.get("tags", [])]
    tag_counts = Counter(all_tags)
    popular_tags = {tag for tag, count in tag_counts.items() if count >= min_count}
    return popular_tags

def build_features_for_manga(manga_id: int, manga_features: dict, bool_rank: bool) -> list:
    if(bool_rank):
        features = []

        for tag, rank in manga_features[manga_id]:
            weight = 3 if rank >= 90 else 2 if rank >= 75 else 1
            features.extend([tag] * weight)

        features = ", ".join(features)

    else:
        features = ", ".join(manga_features[manga_id])
    return features

def build_manga_embedding(model, manga_genre_dict: dict, manga_tag_dict: dict, manga_description_dict: dict):
    genre_embeddings = model.encode(list(manga_genre_dict.values()), batch_size=32, show_progress_bar=True)
    tag_embeddings = model.encode(list(manga_tag_dict.values()), batch_size=32, show_progress_bar=True)
    description_embeddings = model.encode(list(manga_description_dict.values()), batch_size=32, show_progress_bar=True)
    ids = list(manga_genre_dict.keys())
    np.savez("embeddings.npz", ids=ids, genre_embeddings=genre_embeddings, tag_embeddings=tag_embeddings, description_embeddings=description_embeddings)
    
    



if __name__ == '__main__':
    db = MangaDatabase()
    # db.insert_many(manga_data)

    manga_genres = {}
    manga_tags = {}
    manga_descriptions_concatenated = {}
    for manga_id, genre in db.get_genres_for_manga():
        manga_genres.setdefault(manga_id, []).append(genre)
    for manga_id, tag, rank in db.get_tags_for_manga_with_rank():
        manga_tags.setdefault(manga_id, []).append((tag, rank))
    for manga_id, description in db.get_description_for_manga():
        manga_descriptions_concatenated[manga_id] = description
    
    db.close()
    print("Gotowe!")

    print(len(manga_genres))
    print(len(manga_tags))
    print(len(manga_descriptions_concatenated))

    manga_genres_concatenated = {}
    manga_tags_concatenated = {}
    for manga_id in manga_genres:
        manga_genres_concatenated[manga_id] = build_features_for_manga(manga_id, manga_genres, False)
    for manga_id in manga_tags:
        manga_tags_concatenated[manga_id] = build_features_for_manga(manga_id, manga_tags, True)

    print(len(manga_genres_concatenated))
    print(len(manga_tags_concatenated))
    print(len(manga_descriptions_concatenated))

    model = SentenceTransformer("all-MiniLM-L6-v2")
    build_manga_embedding(model, manga_genres_concatenated, manga_tags_concatenated, manga_descriptions_concatenated)


    
    # print(manga_genres)
    # print(manga_tags)
    # print(manga_descriptions)