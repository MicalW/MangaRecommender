import re
import json
from sentence_transformers import SentenceTransformer
import numpy as np

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&quot;", "\"", text)
    text = re.sub(r"&apos;", "'", text)
    return text

def text_builder(manga: dict) -> str:
    text = ""
    description = clean_text(manga.get("description", "")) or " "

    tags = ", ".join([
        t["name"] for t in manga.get("tags", [])])

    genres = ", ".join(manga.get("genres", []))

    text += f"Description: {description}\n"
    text += f"Tags: {tags}\n"
    text += f"Genres: {genres}\n"
    return text

manga_data = []

with open("manga.json", "r", encoding="utf-8") as f:
    manga_data = json.load(f)

manga_preembedding = [text_builder(manga) for manga in manga_data]


model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(
    manga_preembedding,
    batch_size=32,
    show_progress_bar=True)

embeddings = embeddings.astype(np.float16)

np.save("embeddings.npy", embeddings)