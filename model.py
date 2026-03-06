import json
import html
import re
from collections import Counter
from sentence_transformers import SentenceTransformer
import numpy as np
from database.database import MangaDatabase

def text_builder(manga: dict, popular_tags: set) -> str:
    manga_id = manga.get("id")
    title_english = manga.get("title", {}).get("english") or "Unknown"
    title_romaji = manga.get("title", {}).get("romaji") or "Unknown"
    description = manga.get("description", "") or "No description available."
    tags_list = [t["name"] for t in manga.get("tags", []) if t["name"] in popular_tags]
    tags = ", ".join(tags_list)
    genres = ", ".join(manga.get("genres", []))
    return f"ID: {manga_id}\nTitle: {title_english} ({title_romaji})\nDescription: {description}\nTags: {tags}\nGenres: {genres}"

with open("manga.json", "r", encoding="utf-8") as f:
    manga_data = json.load(f)
all_tags = [tag["name"] for manga in manga_data for tag in manga.get("tags", [])]
tag_counts = Counter(all_tags)
popular_tags = {tag for tag, count in tag_counts.items() if count >= 40}
manga_preembedding = [text_builder(manga, popular_tags) for manga in manga_data]

db = MangaDatabase()
db.insert_many(manga_data)

print(db.get_all_manga())
db.close()
print("Gotowe!")




# model = SentenceTransformer("all-MiniLM-L6-v2")
# embeddings = model.encode(manga_preembedding, batch_size=32, show_progress_bar=True)
# np.save("embeddings.npy", embeddings.astype(np.float16))
