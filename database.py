import sqlite3

conn = sqlite3.connect('manga.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS manga (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        genres TEXT,
        tags TEXT,
        image TEXT
    )
''')

conn.commit()
conn.close()