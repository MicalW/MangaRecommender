import requests
import time
import json
from database import MangaDatabase

url = "https://graphql.anilist.co"

query = '''
query ($id: Int, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        pageInfo {
            hasNextPage
        }
        media(id: $id, type: MANGA, sort: POPULARITY_DESC) {
            id
            title {
                romaji
                english
            }
            description
            genres
            tags {
                name
            }
            coverImage {
                large
            }
        }
    }
}
'''
all_manga = []
page = 1
while True:
    variables = {'page': page , 'perPage': 50}
    response = requests.post(url, json={'query': query, 'variables': variables})

    if response.status_code == 429:
        print("Rate limit hit, waiting...")
        time.sleep(61)
        continue

    if response.status_code != 200:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        break

    data = response.json()

    if data.get('errors'):
        print("API Error:", data['errors'])
        time.sleep(5)
        continue

    if not data.get('data'):
        print("No data returned:", data)
        time.sleep(5)
        continue

    page_data = data['data']['Page']
    manga_list = page_data['media']

    all_manga.extend(manga_list)
    if not page_data['pageInfo']['hasNextPage']:
        break
    print(f"Page {page} completed")
    page += 1
    if page > 10:
        break
    time.sleep(1)

with open('manga.json', 'w', encoding='utf-8') as f:
    json.dump(all_manga, f, ensure_ascii=False, indent=4)

print(f"Pobrano {len(all_manga)} mang. Zapisywanie do bazy sqlite...")
db = MangaDatabase()
db.insert_many(all_manga)
db.close()
print("Gotowe!")