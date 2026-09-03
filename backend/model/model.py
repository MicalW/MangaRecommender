import sys
import os
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from sentence_transformers import SentenceTransformer, util
from database.database import MangaDatabase

def add_manga(user_embedding, n, manga_embedding):

    user_embedding = (user_embedding * n + manga_embedding) / (n + 1)
    n += 1

    return user_embedding, n
def add_like_and_get_new_recommendations(new_manga_id, liked_ids, ids, desc_embeddings_norm, tag_embeddings_norm, genre_embeddings_norm):
    liked_ids.append(new_manga_id)

    db = MangaDatabase()
    db.add_user_like(new_manga_id)
    db.close()

    print(f"Adding {new_manga_id} to liked IDs: {liked_ids}")
    
    # Safely find indices only for IDs present in the dataset
    idx = []
    for mid in liked_ids:
        where_res = np.where(ids == mid)[0]
        if len(where_res) > 0:
            idx.append(where_res[0])
        else:
            print(f"Warning: Manga ID {mid} not found in dataset.")

    if not idx:
        print("Error: No valid liked manga IDs found in dataset.")
        return np.array([])
    new_user_profile_desc = np.mean(desc_embeddings_norm[idx], axis=0)
    new_user_profile_tag = np.mean(tag_embeddings_norm[idx], axis=0)
    new_user_profile_genre = np.mean(genre_embeddings_norm[idx], axis=0)

    u_desc_norm = new_user_profile_desc / (np.linalg.norm(new_user_profile_desc) + 1e-9)
    u_tag_norm = new_user_profile_tag / (np.linalg.norm(new_user_profile_tag) + 1e-9)
    u_genre_norm = new_user_profile_genre / (np.linalg.norm(new_user_profile_genre) + 1e-9)
    
    print("1 metoda zakonczona pomyslnie")
    
    return get_recommendations(desc_embeddings_norm, tag_embeddings_norm, genre_embeddings_norm, u_desc_norm, u_tag_norm, u_genre_norm, liked_ids, ids)

def get_recommendations(desc_embeddings_norm, tag_embeddings_norm, genre_embeddings_norm, u_desc_norm, u_tag_norm, u_genre_norm, liked_ids, all_ids):
    scores_desc = desc_embeddings_norm @ u_desc_norm
    scores_tag = tag_embeddings_norm @ u_tag_norm
    scores_genre = genre_embeddings_norm @ u_genre_norm
    print("2 metoda zakonczona pomyslnie")
    return get_weight(scores_desc, scores_tag, scores_genre, liked_ids, all_ids)
def get_weight(score_desc, score_tag, score_genre, liked_ids, all_ids, w_desc = 0.3, w_tag = 0.5, w_genre = 0.2):
    final_scores = (score_desc*w_desc + score_tag*w_tag + score_genre*w_genre)
    liked_indices = [np.where(all_ids == mid)[0][0] for mid in liked_ids if mid in all_ids]
    print("3 metoda zakonczona pomyslnie")
    final_scores[liked_indices] = -1.0
    return final_scores.argsort()[::-1]
    

    
def load_manga_embeddings(file_path):
    """Loads and normalizes embeddings from a .npz file."""
    data = np.load(file_path)
    ids = data["ids"]
    
    desc = data["description_embeddings"]
    genre = data["genre_embeddings"]
    tag = data["tag_embeddings"]

    # Pre-normalize for faster similarity calculation
    desc_norm = desc / (np.linalg.norm(desc, axis=1, keepdims=True) + 1e-9)
    genre_norm = genre / (np.linalg.norm(genre, axis=1, keepdims=True) + 1e-9)
    tag_norm = tag / (np.linalg.norm(tag, axis=1, keepdims=True) + 1e-9)

    return ids, desc_norm, genre_norm, tag_norm

if __name__ == "__main__":
    embeddings_path = "data/embeddings.npz"
    ids, description_embeddings_norm, genre_embeddings_norm, tag_embeddings_norm = load_manga_embeddings(embeddings_path)

    db = MangaDatabase()
    db.create_user_table()
    user_liked_manga_ids = db.get_user_likes()
    db.close()
    
    sorted_indices = add_like_and_get_new_recommendations(30564, user_liked_manga_ids, ids, description_embeddings_norm, tag_embeddings_norm, genre_embeddings_norm)
    top_1_id = int(ids[sorted_indices[0]])
    db = MangaDatabase()
    manga_info = db.get_manga_by_id(top_1_id)
    db.close()
    print(f"Top 1 Recommendation: {manga_info} (ID: {top_1_id})")

    sorted_indices = add_like_and_get_new_recommendations(30028, user_liked_manga_ids, ids, description_embeddings_norm, tag_embeddings_norm, genre_embeddings_norm)
    top_1_id = int(ids[sorted_indices[0]])
    db = MangaDatabase()
    manga_info = db.get_manga_by_id(top_1_id)
    db.close()
    print(f"Top 1 Recommendation after adding more: {manga_info} (ID: {top_1_id})")