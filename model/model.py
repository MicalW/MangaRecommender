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
    

    

if __name__ == "__main__":
    
    embeddings = np.load("data/embeddings.npz")
    ids = embeddings["ids"]
    genre_embeddings = embeddings["genre_embeddings"]
    tag_embeddings = embeddings["tag_embeddings"]
    description_embeddings = embeddings["description_embeddings"]

    db = MangaDatabase()
    db.create_user_table() # Opcjonalnie, żeby mieć pewność, że tabela istnieje
    user_liked_manga_ids = db.get_user_likes()
    db.close()

    # if(not user_liked_manga_ids.empty):
    #     idx = [np.where(ids == mid)[0][0] for mid in user_liked_manga_ids]
    #     user_desc_embedding = np.mean(description_embeddings[idx], axis=0)
    #     user_tag_embedding = np.mean(tag_embeddings[idx], axis=0)
    #     user_genre_embedding = np.mean(genre_embeddings[idx], axis=0)
    # else:
    #     user_desc_embedding = np.zeros(384)
    #     user_tag_embedding = np.zeros(384)
    #     user_genre_embedding = np.zeros(384)

    description_embeddings_norm = description_embeddings / (np.linalg.norm(description_embeddings, axis=1, keepdims=True) + 1e-9)
    genre_embeddings_norm = genre_embeddings / (np.linalg.norm(genre_embeddings, axis=1, keepdims=True) + 1e-9)
    tag_embeddings_norm = tag_embeddings / (np.linalg.norm(tag_embeddings, axis=1, keepdims=True) + 1e-9)
    
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