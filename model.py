import json
from collections import Counter
from sentence_transformers import SentenceTransformer
import numpy as np
from database.database import MangaDatabase

# def text_builder(manga: dict, popular_tags: set) -> str:
#     manga_id = manga.get("id")
#     title_english = manga.get("title", {}).get("english") or "Unknown"
#     title_romaji = manga.get("title", {}).get("romaji") or "Unknown"
#     description = manga.get("description", "") or "No description available."
#     tags_list = [t["name"] for t in manga.get("tags", []) if t["name"] in popular_tags]
#     tags = ", ".join(tags_list)
#     genres = ", ".join(manga.get("genres", []))
#     return f"ID: {manga_id}\nTitle: {title_english} ({title_romaji})\nDescription: {description}\nTags: {tags}\nGenres: {genres}"

if __name__ == "__main__":
    a



# model = SentenceTransformer("all-MiniLM-L6-v2")
# embeddings = model.encode(manga_preembedding, batch_size=32, show_progress_bar=True)
# np.save("embeddings.npy", embeddings.astype(np.float16))
