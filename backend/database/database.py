import sqlite3
from pathlib import Path

class MangaDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "manga.db"

        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.cursor = self.conn.cursor()
        self.create_table()


    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga (
                id INTEGER PRIMARY KEY,
                title_english TEXT,
                title_romaji TEXT,
                description TEXT,
                image TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga_tags (
                manga_id INTEGER,
                tag_id INTEGER,
                rank INTEGER,
                PRIMARY KEY (manga_id, tag_id),
                -- Automatyczne usuwanie powiązań
                FOREIGN KEY (manga_id) REFERENCES manga(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga_genres (
                manga_id INTEGER,
                genre_id INTEGER,
                PRIMARY KEY (manga_id, genre_id),
                -- Automatyczne usuwanie powiązań
                FOREIGN KEY (manga_id) REFERENCES manga(id) ON DELETE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
            )
        ''')
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_likes (manga_id INTEGER PRIMARY KEY)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_dislikes (manga_id INTEGER PRIMARY KEY)"
        )
        self.conn.commit()
    
    def insert_manga(self, manga_data):
        manga_id = manga_data.get('id')
        
        title_data = manga_data.get('title', {})
        title_english = title_data.get('english') or title_data.get('romaji') or 'Unknown'
        title_romaji = title_data.get('romaji') or title_data.get('english') or 'Unknown'
        
        description = manga_data.get('description', '')
        
        cover_image = manga_data.get('coverImage', {}).get('large', '')

        # 1. Wstawienie/Aktualizacja mangi (bez kolumny tags)
        self.cursor.execute('''
            INSERT OR REPLACE INTO manga (id, title_english, title_romaji, description, image)
            VALUES (?, ?, ?, ?, ?)
        ''', (manga_id, title_english, title_romaji, description, cover_image))
        
        # 2. Obsługa tagów
        tags_raw = manga_data.get('tags') or []
        for tag_obj in tags_raw:
            tag_name = tag_obj.get('name')
            tag_rank = tag_obj.get('rank')
            if not tag_name:
                continue
            

            self.cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
            self.cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            tag_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                'INSERT OR IGNORE INTO manga_tags (manga_id, tag_id, rank) VALUES (?, ?, ?)',
                (manga_id, tag_id, tag_rank),
            )
        # 3. Obsługa gatunków
        genres_list = manga_data.get('genres') or []
        for genre in genres_list:
            self.cursor.execute('INSERT OR IGNORE INTO genres (name) VALUES (?)', (genre,))
            self.cursor.execute('SELECT id FROM genres WHERE name = ?', (genre,))
            genre_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                'INSERT OR IGNORE INTO manga_genres (manga_id, genre_id) VALUES (?, ?)',
                (manga_id, genre_id),
            )

    def insert_many(self, manga_list):
        for manga in manga_list:
            self.insert_manga(manga)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_all_manga(self):
        self.cursor.execute('SELECT * FROM manga')
        return self.cursor.fetchall()

    def get_all_tags(self):
        self.cursor.execute('SELECT * FROM tags')
        return self.cursor.fetchall()

    def get_all_manga_tags(self):
        self.cursor.execute('SELECT * FROM manga_tags')
        return self.cursor.fetchall()
    def get_genres_for_manga(self):
        self.cursor.execute('SELECT m.id, g.name FROM manga m JOIN manga_genres mg ON m.id = mg.manga_id JOIN genres g ON g.id = mg.genre_id')
        return self.cursor.fetchall()
    def get_tags_for_manga(self):
        self.cursor.execute('SELECT m.id, t.name FROM manga m JOIN manga_tags mt ON m.id = mt.manga_id JOIN tags t ON t.id = mt.tag_id')
        return self.cursor.fetchall()
    def get_tags_for_manga_with_rank(self):
        self.cursor.execute('SELECT m.id, t.name, mt.rank FROM manga m JOIN manga_tags mt ON m.id = mt.manga_id JOIN tags t ON t.id = mt.tag_id')
        return self.cursor.fetchall()
    def get_description_for_manga(self):
        self.cursor.execute('SELECT m.id, m.description FROM manga m')
        return self.cursor.fetchall()

    def get_manga_by_id(self, manga_id):
        self.cursor.execute('SELECT id, title_english, title_romaji, description, image FROM manga WHERE id = ?', (manga_id,))
        return self.cursor.fetchone()

    def search_manga(self, query, limit=10):
        self.cursor.execute('''
            SELECT id, title_english, title_romaji, description, image 
            FROM manga 
            WHERE title_english LIKE ? OR title_romaji LIKE ? 
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        return self.cursor.fetchall()

    def create_user_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_likes (manga_id INTEGER PRIMARY KEY)")
        self.conn.commit()
    def add_user_like(self, manga_id):
        self.cursor.execute("INSERT OR IGNORE INTO user_likes (manga_id) VALUES (?)", (manga_id,))
        self.conn.commit()
    def remove_user_like(self, manga_id):
        self.cursor.execute("DELETE FROM user_likes WHERE manga_id = ?", (manga_id,))
        self.conn.commit()
    def get_user_likes(self):
        self.cursor.execute("SELECT manga_id FROM user_likes")
        return [row[0] for row in self.cursor.fetchall()]
    def clear_user_likes(self):
        self.cursor.execute("DELETE FROM user_likes")
        self.conn.commit()

    def create_user_dislikes(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_dislikes (manga_id INTEGER PRIMARY KEY)")
        self.conn.commit()
    def add_user_dislike(self, manga_id):
        self.cursor.execute("INSERT OR IGNORE INTO user_dislikes (manga_id) VALUES (?)", (manga_id,))
        self.conn.commit()
    def remove_user_dislike(self, manga_id):
        self.cursor.execute("DELETE FROM user_dislikes WHERE manga_id = ?", (manga_id,))
        self.conn.commit()
    def set_global_reaction(self, manga_id, liked):
        """Save one global reaction; a manga can belong to only one list."""
        target_table = "user_likes" if liked else "user_dislikes"
        other_table = "user_dislikes" if liked else "user_likes"
        self.cursor.execute(f"DELETE FROM {other_table} WHERE manga_id = ?", (manga_id,))
        self.cursor.execute(f"INSERT OR IGNORE INTO {target_table} (manga_id) VALUES (?)", (manga_id,))
        self.conn.commit()
    def get_user_dislikes(self):
        self.cursor.execute("SELECT manga_id FROM user_dislikes")
        return [row[0] for row in self.cursor.fetchall()]
    def clear_user_dislikes(self):
        self.cursor.execute("DELETE FROM user_dislikes")
        self.conn.commit()

    # DB_PATH = "manga.db"

    @staticmethod
    def get_connection():
        db_path = Path(__file__).parent.parent / "data" / "manga.db"
        return sqlite3.connect(str(db_path))

if __name__ == '__main__':
    db = MangaDatabase()
    print("Database connection opened and table checked/created.")
    db.clear_user_likes()
    db.close()
