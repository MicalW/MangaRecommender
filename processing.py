import json
import html
import re
from collections import Counter
from database.database import MangaDatabase

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



if __name__ == '__main__':
    with open("manga.json", "r", encoding="utf-8") as f:
        manga_data = json.load(f)

    popular_tags = get_popular_tags(manga_data, 40)

    for manga in manga_data:
        manga["description"] = clean_description_from_html(manga)
        manga["tags"] = [
        t for t in manga.get("tags", [])
        if t["name"] in popular_tags
        ]
    db = MangaDatabase()
    db.insert_many(manga_data)

    print(db.get_all_manga())
    db.close()
    print("Gotowe!")