# Manga Recommender

Backend API rekomendujący mangę na podstawie tytułów oznaczonych przez użytkownika jako lubiane. Projekt korzysta z danych AniList, bazy SQLite oraz embeddingów tekstowych do porównywania opisów, tagów i gatunków.

## Funkcje

- wyszukiwanie mang po tytule;
- pobieranie szczegółów mangi;
- zapisywanie polubionych tytułów w lokalnej bazie;
- rekomendacje oparte na podobieństwie kosinusowym embeddingów;
- automatyczna dokumentacja interaktywna FastAPI pod `/docs`.

## Jak działa rekomendowanie

1. Skrypt importu pobiera mangi z AniList i zapisuje je do `data/manga.db`.
2. Skrypt przetwarzania tworzy osobne embeddingi dla opisu, gatunków i tagów.
3. Po polubieniu tytułów API uśrednia ich wektory, tworząc profil użytkownika.
4. Tytuły są sortowane według ważonego wyniku podobieństwa:

   - tagi: `0.5`;
   - opis: `0.3`;
   - gatunki: `0.2`.

   Polubione już tytuły są wykluczane z wyników.

## Wymagania

- Python 3.10 lub nowszy;
- `pip`;
- opcjonalnie: dostęp do internetu, gdy baza i embeddingi mają zostać zbudowane od zera.

## Uruchomienie

W katalogu projektu utwórz i aktywuj środowisko wirtualne, a następnie zainstaluj zależności:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Uruchom serwer:

```powershell
python -m uvicorn api.main:app --reload
```

API będzie dostępne pod adresem `http://127.0.0.1:8000`, a dokumentacja Swagger UI pod `http://127.0.0.1:8000/docs`.

## Endpointy

| Metoda | Ścieżka | Opis |
| --- | --- | --- |
| `GET` | `/` | Stan usługi i odnośnik do dokumentacji. |
| `GET` | `/manga/search?q={tekst}&limit={n}` | Wyszukuje mangi po tytule. Parametr `q` ma co najmniej 2 znaki. |
| `GET` | `/manga/{manga_id}` | Zwraca szczegóły wskazanej mangi. |
| `GET` | `/manga/queue?limit={n}` | Zwraca kolejkę tytułów lub rekomendacje dla zapisanych polubień. |
| `POST` | `/user/like/{manga_id}` | Zapisuje polubienie tytułu dostępnego w zbiorze embeddingów. |
| `POST` | `/user/dislike/{manga_id}` | Zwraca potwierdzenie oznaczenia tytułu jako nielubiany. |
| `GET` | `/user/profile` | Zwraca globalną listę polubionych i odrzuconych mang. |
| `GET` | `/user/recommendations?limit={n}` | Zwraca spersonalizowane rekomendacje. |

Przykładowa sesja:

```powershell
# Wyszukaj tytuł
Invoke-RestMethod "http://127.0.0.1:8000/manga/search?q=naruto"

# Dodaj polubienie (użyj identyfikatora z wyniku wyszukiwania)
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/user/like/20"

# Pobierz rekomendacje
Invoke-RestMethod "http://127.0.0.1:8000/user/recommendations?limit=10"
```

## Dane i ponowne budowanie embeddingów

Repozytorium zawiera przykładowe pliki `data/manga.db` i `data/embeddings.npz`. Aby odtworzyć dane:

```powershell
# Pobiera dane z AniList i zapisuje je w bazie SQLite.
python model/mangaRequest.py

# Tworzy data/embeddings.npz z użyciem all-MiniLM-L6-v2.
python model/processing.py
```

Model SentenceTransformer może zostać pobrany przy pierwszym uruchomieniu skryptu tworzącego embeddingi. Po zmianie zawartości bazy uruchom ponownie `model/processing.py`, aby `embeddings.npz` odpowiadał aktualnym danym.

Pełny opis przepływu danych znajduje się w [docs/PIPELINE.md](docs/PIPELINE.md).

## Struktura projektu

```text
api/main.py              aplikacja FastAPI i endpointy HTTP
database/database.py     schemat SQLite oraz operacje na danych
model/mangaRequest.py    import popularnych mang z AniList
model/processing.py      przygotowanie cech i generowanie embeddingów
model/model.py           ranking rekomendacji
data/manga.db            lokalna baza mang
data/embeddings.npz      zapisane embeddingi używane przez API
```

## Uwagi

- Polubienia i odrzucenia są przechowywane w jednym, globalnym profilu w `data/manga.db`; aplikacja nie rozróżnia kont użytkowników.
- Aplikacja domyślnie zezwala w CORS na frontend pod `http://localhost:5173`.
- Endpointy rekomendacyjne wymagają istniejącego i zgodnego z bazą pliku `data/embeddings.npz`.
- Zmiana decyzji jest automatyczna: `like` usuwa wcześniejszy `dislike`, a `dislike` usuwa wcześniejszy `like`.
