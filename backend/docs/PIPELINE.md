# Pipeline danych i embeddingów

Ten dokument opisuje pełny przepływ przygotowania danych używanych przez Manga Recommender: od pobrania mang z AniList, przez zapis w SQLite, aż po utworzenie embeddingów wykorzystywanych przez API.

## Przepływ

```text
AniList GraphQL API
        |
        |  model/mangaRequest.py
        v
data/manga.db (SQLite)
        |
        |  model/processing.py + SentenceTransformer
        v
data/embeddings.npz
        |
        |  api/main.py
        v
rekomendacje HTTP
```

## 1. Przygotowanie środowiska

Wykonaj polecenia z katalogu głównego projektu:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Do pobierania danych i pierwszego tworzenia embeddingów potrzebne jest połączenie z internetem. Model `all-MiniLM-L6-v2` zostanie automatycznie pobrany przez bibliotekę Sentence Transformers, jeśli nie ma go jeszcze w lokalnym cache.

## 2. Pobranie danych z AniList

Uruchom:

```powershell
python model/mangaRequest.py
```

Skrypt wykonuje zapytania GraphQL do `https://graphql.anilist.co` i pobiera popularne pozycje typu `MANGA`. Dla każdej mangi zapisuje:

- identyfikator AniList;
- tytuł angielski i romaji;
- opis;
- adres dużej okładki;
- gatunki;
- tagi i ich ranking.

W razie limitu zapytań AniList (`HTTP 429`) skrypt czeka 61 sekund i ponawia żądanie. Aktualna konfiguracja pobiera maksymalnie 10 stron po 50 pozycji, czyli do 500 mang.

### Wynik

Powstaje lub zostaje zaktualizowany plik `data/manga.db`. Tymczasowy plik `manga.json` jest zapisywany w bieżącym katalogu uruchomienia i zawiera surową odpowiedź z AniList.

## 3. Tworzenie bazy SQLite

Za utworzenie struktury odpowiada klasa `MangaDatabase` w `database/database.py`. Jest wywoływana automatycznie zarówno podczas importu danych, jak i przez API.

W bazie znajdują się tabele:

| Tabela | Zawartość |
| --- | --- |
| `manga` | Dane podstawowe mangi: tytuły, opis i okładka. |
| `tags` | Unikalne nazwy tagów. |
| `manga_tags` | Powiązania manga–tag wraz z rankingiem taga. |
| `genres` | Unikalne nazwy gatunków. |
| `manga_genres` | Powiązania manga–gatunek. |
| `user_likes` | Lokalnie zapisane polubienia użytkownika. |
| `user_dislikes` | Tabela przygotowana na nielubiane tytuły. |

Tabele `user_likes` i `user_dislikes` są tworzone dopiero wtedy, gdy wywoła je odpowiedni fragment aplikacji.

### Kontrola bazy

Po imporcie możesz sprawdzić liczbę zaimportowanych rekordów:

```powershell
python -c "from database.database import MangaDatabase; db=MangaDatabase(); print(len(db.get_all_manga())); db.close()"
```

## 4. Przygotowanie cech tekstowych

Skrypt `model/processing.py` odczytuje dane z bazy i tworzy trzy tekstowe reprezentacje dla każdej mangi:

1. **Opis** — HTML jest odkodowywany, usuwane są tagi HTML, a następnie zostaje pierwszy wiersz tekstu.
2. **Gatunki** — nazwy gatunków są łączone w jeden tekst.
3. **Tagi** — nazwy tagów są łączone w jeden tekst; tagi o rankingu `>= 75` są powtarzane dwukrotnie, a o rankingu `>= 90` trzykrotnie.

Powtarzanie tagów wzmacnia ich wpływ na końcowy wektor.

## 5. Generowanie embeddingów

Uruchom:

```powershell
python model/processing.py
```

Skrypt ładuje model `all-MiniLM-L6-v2` i koduje osobno opisy, gatunki oraz tagi. Wynik zapisuje w pliku `data/embeddings.npz`.

Plik zawiera cztery tablice NumPy:

| Klucz | Opis |
| --- | --- |
| `ids` | Identyfikatory AniList odpowiadające wektorom. |
| `description_embeddings` | Wektory opisów. |
| `genre_embeddings` | Wektory gatunków. |
| `tag_embeddings` | Wektory tagów. |

## 6. Wykorzystanie przez API

Przy starcie `api/main.py` odczytuje `data/embeddings.npz`, normalizuje każdy wektor i trzyma go w pamięci. Po dodaniu polubień API:

1. pobiera embeddingi polubionych mang;
2. uśrednia je osobno dla opisów, tagów i gatunków;
3. wylicza podobieństwo kosinusowe między profilem użytkownika a wszystkimi mangami;
4. łączy wyniki z wagami: tagi `0.5`, opis `0.3`, gatunki `0.2`;
5. usuwa z rankingu tytuły już polubione;
6. zwraca najwyżej ocenione pozycje.

Uruchomienie API:

```powershell
python -m uvicorn api.main:app --reload
```

## Kolejność odtworzenia danych

Gdy chcesz zbudować dane od początku, wykonaj kroki w tej kolejności:

```powershell
python model/mangaRequest.py
python model/processing.py
python -m uvicorn api.main:app --reload
```

Po każdej zmianie danych w `data/manga.db` ponownie wygeneruj `data/embeddings.npz` i zrestartuj API. Dzięki temu identyfikatory w bazie i w pliku embeddingów pozostaną zgodne.

## Rozwiązywanie problemów

| Problem | Co sprawdzić |
| --- | --- |
| API zwraca `503` dla rekomendacji | Upewnij się, że istnieje `data/embeddings.npz`; uruchom `python model/processing.py`. |
| Brak wyników rekomendacji | Dodaj co najmniej jedno polubienie przez `POST /user/like/{manga_id}` i sprawdź, czy jego ID występuje w embeddingach. |
| Import zatrzymuje się z błędem HTTP | Sprawdź połączenie z AniList; skrypt sam obsługuje limit `429`. |
| Embeddingi nie odpowiadają danym | Po imporcie lub modyfikacji bazy uruchom ponownie `model/processing.py`. |
