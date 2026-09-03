import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import uvicorn

# Add project root to sys.path to allow imports from database and model
sys.path.append(str(Path(__file__).parent.parent))

from database.database import MangaDatabase
from MangaRecommender.backend.model.model import get_recommendations, load_manga_embeddings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Manga Recommender API",
    description="API for personalized manga recommendations based on user likes.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API responses
class MangaBase(BaseModel):
    id: int
    title_english: Optional[str]
    title_romaji: Optional[str]
    image: Optional[str]

class MangaDetail(MangaBase):
    description: Optional[str]

class RecommendationResponse(BaseModel):
    recommendations: List[MangaBase]
    count: int

class GlobalProfileResponse(BaseModel):
    liked: List[MangaBase]
    disliked: List[MangaBase]

# Global variables to store embeddings for performance
# In a production app, these might be managed by a dependency or a singleton class
embeddings_data = {
    "ids": None,
    "desc_norm": None,
    "genre_norm": None,
    "tag_norm": None
}

@app.on_event("startup")
async def startup_event():
    """Load embeddings into memory when the server starts."""
    try:
        embeddings_path = Path(__file__).parent.parent / "data" / "embeddings.npz"
        if embeddings_path.exists():
            ids, desc_n, genre_n, tag_n = load_manga_embeddings(str(embeddings_path))
            embeddings_data["ids"] = ids
            embeddings_data["desc_norm"] = desc_n
            embeddings_data["genre_norm"] = genre_n
            embeddings_data["tag_norm"] = tag_n
            
            print(f"Successfully loaded {len(embeddings_data['ids'])} manga embeddings.")
        else:
            print(f"Warning: Embeddings file not found at {embeddings_path}")
    except Exception as e:
        print(f"Error during startup: {e}")

@app.get("/", tags=["General"])
async def root():
    return {
        "status": "online",
        "message": "Manga Recommender API is running",
        "docs": "/docs"
    }

@app.get("/manga/search", response_model=List[MangaBase], tags=["Manga"])
async def search_manga(q: str = Query(..., min_length=2), limit: int = 20):
    """Search for manga by title."""
    db = MangaDatabase()
    results = db.search_manga(q, limit=limit)
    db.close()
    
    return [
        {
            "id": row[0],
            "title_english": row[1],
            "title_romaji": row[2],
            "image": row[4]
        } for row in results
    ]
@app.get("/manga/queue", response_model = RecommendationResponse, tags = ["Manga", "User"])
async def get_manga_queue(limit: int = 10):
    db = MangaDatabase()
    db.create_user_table()
    db.create_user_dislikes()
    user_likes = db.get_user_likes()
    user_dislikes = db.get_user_dislikes()
    recorded_mangas = set(user_likes + user_dislikes)

    if not user_likes:
        results = []
        for m in db.get_all_manga():
            if m[0] in recorded_mangas:
                continue
            results.append({
                "id": m[0],
                "title_english": m[1],
                "title_romaji": m[2],
                "image": m[4]
            })
            if len(results) == limit:
                break
        db.close()
        return { "recommendations": results,
                 "count": len(results)
        }
    
    if embeddings_data["ids"] is not None and user_likes is not None:
        if not user_likes:
            db.close()
            return {"recommendations": [], "count": 0}

    # Extract user profile from likes
        idx = []
        for mid in user_likes:
            where_res = np.where(embeddings_data["ids"] == mid)[0]
            if len(where_res) > 0:
                idx.append(where_res[0])

        if not idx:
            db.close()
            return {"recommendations": [], "count": 0}

    # Compute user profile (mean of liked embeddings)
        u_desc = np.mean(embeddings_data["desc_norm"][idx], axis=0)
        u_tag = np.mean(embeddings_data["tag_norm"][idx], axis=0)
        u_genre = np.mean(embeddings_data["genre_norm"][idx], axis=0)

    # Normalize profile
        u_desc_norm = u_desc / (np.linalg.norm(u_desc) + 1e-9)
        u_tag_norm = u_tag / (np.linalg.norm(u_tag) + 1e-9)
        u_genre_norm = u_genre / (np.linalg.norm(u_genre) + 1e-9)

    # Get recommendation indices
        sorted_indices = get_recommendations(
            embeddings_data["desc_norm"],
            embeddings_data["tag_norm"],
            embeddings_data["genre_norm"],
            u_desc_norm,
            u_tag_norm,
            u_genre_norm,
            user_likes,
            embeddings_data["ids"]
        )
    
        results = []
        for index in sorted_indices:
            rid = embeddings_data["ids"][index]
            if int(rid) in recorded_mangas:
                continue
            m = db.get_manga_by_id(int(rid))
            if m:
                results.append({
                    "id": m[0],
                    "title_english": m[1],
                    "title_romaji": m[2],
                    "image": m[4]
                })
            if len(results) == limit:
                break
        db.close()
        return {"recommendations": results, "count": len(results)}

    db.close()
    return {"recommendations": [], "count": 0}
@app.get("/manga/{manga_id}", response_model=MangaDetail, tags=["Manga"])
async def get_manga_details(manga_id: int):
    """Get detailed information about a specific manga."""
    db = MangaDatabase()
    manga = db.get_manga_by_id(manga_id)
    db.close()
    
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
        
    return {
        "id": manga[0],
        "title_english": manga[1],
        "title_romaji": manga[2],
        "description": manga[3],
        "image": manga[4]
    }

@app.post("/user/like/{manga_id}", tags=["User"])
async def like_manga(manga_id: int):
    """Register a like for a manga to improve recommendations."""
    if embeddings_data["ids"] is None:
        raise HTTPException(status_code=503, detail="Recommendation engine is not initialized (embeddings missing)")

    db = MangaDatabase()
    # Check if manga exists in our dataset
    if manga_id not in embeddings_data["ids"]:
        db.close()
        raise HTTPException(status_code=400, detail="Manga ID not in recommendation dataset")

    db.set_global_reaction(manga_id, liked=True)
    db.close()
    
    return {
        "message": "Manga liked successfully",
        "manga_id": manga_id,
        "queue": await get_manga_queue()
    }

@app.get("/user/profile", response_model=GlobalProfileResponse, tags=["User"])
async def get_global_profile():
    """Return the one global profile shared by the application."""
    db = MangaDatabase()
    def manga_items(manga_ids):
        items = []
        for manga_id in manga_ids:
            manga = db.get_manga_by_id(manga_id)
            if manga:
                items.append({
                    "id": manga[0],
                    "title_english": manga[1],
                    "title_romaji": manga[2],
                    "image": manga[4]
                })
        return items

    profile = {
        "liked": manga_items(db.get_user_likes()),
        "disliked": manga_items(db.get_user_dislikes())
    }
    db.close()
    return profile

@app.delete("/user/profile", tags=["User"])
async def clear_global_profile():
    """Remove every saved reaction from the one global profile."""
    db = MangaDatabase()
    db.clear_user_likes()
    db.clear_user_dislikes()
    db.close()
    return {"message": "Global profile cleared"}

@app.get("/user/recommendations", response_model=RecommendationResponse, tags=["User"])
async def get_user_recommendations(limit: int = 10):
    """Get personalized recommendations based on the user's liked manga."""
    if embeddings_data["ids"] is None:
        raise HTTPException(status_code=503, detail="Recommendation engine is not initialized")

    db = MangaDatabase()
    user_likes = db.get_user_likes()
    user_dislikes = db.get_user_dislikes()
    
    if not user_likes:
        db.close()
        return {"recommendations": [], "count": 0}
    # Extract user profile from likes
    idx = []
    for mid in user_likes:
        where_res = np.where(embeddings_data["ids"] == mid)[0]
        if len(where_res) > 0:
            idx.append(where_res[0])

    if not idx:
        db.close()
        return {"recommendations": [], "count": 0}

    # Compute user profile (mean of liked embeddings)
    u_desc = np.mean(embeddings_data["desc_norm"][idx], axis=0)
    u_tag = np.mean(embeddings_data["tag_norm"][idx], axis=0)
    u_genre = np.mean(embeddings_data["genre_norm"][idx], axis=0)

    # Normalize profile
    u_desc_norm = u_desc / (np.linalg.norm(u_desc) + 1e-9)
    u_tag_norm = u_tag / (np.linalg.norm(u_tag) + 1e-9)
    u_genre_norm = u_genre / (np.linalg.norm(u_genre) + 1e-9)

    # Get recommendation indices
    sorted_indices = get_recommendations(
        embeddings_data["desc_norm"],
        embeddings_data["tag_norm"],
        embeddings_data["genre_norm"],
        u_desc_norm,
        u_tag_norm,
        u_genre_norm,
        user_likes,
        embeddings_data["ids"]
    )
    
    results = []
    recorded_mangas = set(user_likes + user_dislikes)
    for index in sorted_indices:
        rid = embeddings_data["ids"][index]
        if int(rid) in recorded_mangas:
            continue
        m = db.get_manga_by_id(int(rid))
        if m:
            results.append({
                "id": m[0],
                "title_english": m[1],
                "title_romaji": m[2],
                "image": m[4]
            })
        if len(results) == limit:
            break
    
    db.close()
    return {"recommendations": results, "count": len(results)}

@app.post("/user/dislike/{manga_id}", tags=["User"])
async def dislike_manga(manga_id: int):
    db = MangaDatabase()
    if not db.get_manga_by_id(manga_id):
        db.close()
        raise HTTPException(status_code=404, detail="Manga not found")

    db.set_global_reaction(manga_id, liked=False)

    db.close()

    return {
        "message": "Manga disliked successfully",
        "manga_id": manga_id,
        "queue": await get_manga_queue()
    }
if __name__ == "__main__":
    uvicorn.run("main:app", host="[IP_ADDRESS]", port=8000, reload=True)
