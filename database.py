import sqlite3

class MangaDatabase:
    def __init__(self, db_path='manga.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                genres TEXT,
                tags TEXT,
                image TEXT
            )
        ''')
        self.conn.commit()

    def insert_manga(self, manga_data):
        manga_id = manga_data.get('id')
        
        # Wyciągnij najlepszy dostępny tytuł (romaji jako domyślny, ewentualnie angielski)
        title_data = manga_data.get('title', {})
        title = title_data.get('english') or title_data.get('romaji') or 'Unknown'
        
        description = manga_data.get('description', '')
        
        # Złącz listę gatunków w jeden string oddzielony przecinkiem (np. "Action, Adventure")
        genres_list = manga_data.get('genres') or []
        genres = ", ".join(genres_list)
        
        # Wyciągnij same nazwy z obiektów tagów i połącz je przecinkami (np. "Superhero, School")
        tags_raw = manga_data.get('tags') or []
        tags_list = [tag.get('name') for tag in tags_raw if tag.get('name')]
        tags = ", ".join(tags_list)
        
        # Pobierz link do dużej okładki
        cover_image = manga_data.get('coverImage', {}).get('large', '')

        # Wstawienie do bazy danych (Używamy INSERT OR REPLACE, aby nadpisać w razie istnienia tego samego ID)
        self.cursor.execute('''
            INSERT OR REPLACE INTO manga (id, title, description, genres, tags, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (manga_id, title, description, genres, tags, cover_image))
        
        self.conn.commit()

    def insert_many(self, manga_list):
        for manga in manga_list:
            self.insert_manga(manga)

    def close(self):
        self.conn.close()

# Przykładowe użycie (gdy odpalimy plik bezpośrednio)
if __name__ == '__main__':
    db = MangaDatabase()
    print("Database connection opened and table checked/created.")
    # db.insert_manga({"id": 1, ...})
    db.close()