import heroImg from './assets/hero.png'
import './App.css'
import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [mangas, setMangas] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [activePage, setActivePage] = useState("discover");
  const [profile, setProfile] = useState({ liked: [], disliked: [] });
  const [profileLoading, setProfileLoading] = useState(false);
  const [selectedManga, setSelectedManga] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [previousPage, setPreviousPage] = useState("discover");

  // Get manga from FastAPI when the page loads
  useEffect(() => {
    loadMangas();
  }, []);

  async function loadMangas() {
    try {
      const response = await fetch(
        `${API_URL}/manga/queue?limit=10`
      );

      if (!response.ok) {
        throw new Error("Failed to load manga");
      }

      const data = await response.json();

      setMangas(data.recommendations);
      setCurrentIndex(0);
    } catch (error) {
      console.error("Error loading manga:", error);
    } finally {
      setLoading(false);
    }
  }

  async function openProfile() {
    setActivePage("profile");
    setProfileLoading(true);

    try {
      const response = await fetch(`${API_URL}/user/profile`);
      if (!response.ok) {
        throw new Error("Failed to load profile");
      }
      setProfile(await response.json());
    } catch (error) {
      console.error("Error loading profile:", error);
      setProfile({ liked: [], disliked: [] });
    } finally {
      setProfileLoading(false);
    }
  }

  async function openMangaDetails(mangaId) {
    setPreviousPage(activePage);
    setActivePage("details");
    setDetailsLoading(true);

    try {
      const response = await fetch(`${API_URL}/manga/${mangaId}`);
      if (!response.ok) {
        throw new Error("Failed to load manga details");
      }
      setSelectedManga(await response.json());
    } catch (error) {
      console.error("Error loading manga details:", error);
      setSelectedManga(null);
    } finally {
      setDetailsLoading(false);
    }
  }

  async function clearProfile() {
    if (!window.confirm("Clear all liked and skipped manga?")) return;

    try {
      const response = await fetch(`${API_URL}/user/profile`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Failed to clear profile");
      }
      setProfile({ liked: [], disliked: [] });
      loadMangas();
    } catch (error) {
      console.error("Error clearing profile:", error);
    }
  }

  async function saveReaction(endpoint, action) {
    const manga = mangas[currentIndex];
    if (!manga || submitting) return;

    try {
      setSubmitting(true);
      const response = await fetch(
        `${API_URL}/user/${endpoint}/${manga.id}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to ${action} manga`);
      }

      const data = await response.json();
      const nextQueue = data.queue?.recommendations ?? [];

      // Keep showing the current batch. After its final card, replace it with
      // a fresh queue computed from every decision made in this batch.
      if (currentIndex === mangas.length - 1) {
        setMangas(nextQueue);
        setCurrentIndex(0);
      } else {
        setCurrentIndex((index) => index + 1);
      }
      console.log(`${action}:`, manga.title_english);
    } catch (error) {
      console.error(`Error trying to ${action} manga:`, error);
    } finally {
      setSubmitting(false);
    }
  }

  function handleLike() {
    return saveReaction("like", "like");
  }

  async function handleSkip() {
    return saveReaction("dislike", "dislike");
  }

  // Loading state
  if (loading) {
    return (
      <div className="app">
        <h1>Loading manga...</h1>
      </div>
    );
  }

  if (activePage === "profile") {
    return (
      <div className="app">
        <header className="app-header">
          <div>
            <h1>MangaMatch</h1>
            <p>Global profile</p>
          </div>
          <nav className="navigation">
            <button onClick={() => setActivePage("discover")}>Discover</button>
            <button className="active" onClick={openProfile}>Profile</button>
          </nav>
        </header>

        <main className="profile-page">
          <h2>Your global profile</h2>
          <p>These choices are shared by the application and affect the next recommendations.</p>
          <button className="clear-profile" onClick={clearProfile}>Clear profile</button>

          {profileLoading ? (
            <p>Loading profile...</p>
          ) : (
            <div className="profile-sections">
              <ProfileSection title="Liked manga" mangas={profile.liked} emptyText="No liked manga yet." onSelect={openMangaDetails} />
              <ProfileSection title="Skipped manga" mangas={profile.disliked} emptyText="No skipped manga yet." onSelect={openMangaDetails} />
            </div>
          )}
        </main>
      </div>
    );
  }

  if (activePage === "details") {
    return (
      <div className="app">
        <header className="app-header">
          <div>
            <h1>MangaMatch</h1>
            <p>Manga details</p>
          </div>
          <nav className="navigation">
            <button onClick={() => setActivePage("discover")}>Discover</button>
            <button onClick={openProfile}>Profile</button>
          </nav>
        </header>

        <main className="details-page">
          <button className="back-button" onClick={() => setActivePage(previousPage)}>← Back</button>
          {detailsLoading ? (
            <p>Loading details...</p>
          ) : selectedManga ? (
            <article className="details-card">
              <img src={selectedManga.image} alt={selectedManga.title_english || selectedManga.title_romaji} />
              <div>
                <h2>{selectedManga.title_english || selectedManga.title_romaji}</h2>
                <p className="romaji">{selectedManga.title_romaji}</p>
                <p className="description">{plainText(selectedManga.description)}</p>
              </div>
            </article>
          ) : (
            <p>Unable to load this manga.</p>
          )}
        </main>
      </div>
    );
  }

  // No manga returned by API
  if (mangas.length === 0) {
    return (
      <div className="app">
        <h1>No more manga!</h1>
      </div>
    );
  }

  // All manga have been viewed
  if (currentIndex >= mangas.length) {
    return (
      <div className="app">
        <h1>No more manga!</h1>
        <p>You've gone through the current queue.</p>
      </div>
    );
  }

  const manga = mangas[currentIndex];

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>MangaMatch</h1>
          <p>Discover your next favorite manga</p>
        </div>
        <nav className="navigation">
          <button className="active" onClick={() => setActivePage("discover")}>Discover</button>
          <button onClick={openProfile}>Profile</button>
        </nav>
      </header>

      <main>
        <div className="card">
          <img
            src={manga.image}
            alt={manga.title_english || manga.title_romaji}
            className="manga-image"
          />

          <div className="card-info">
            <h2>
              {manga.title_english || manga.title_romaji}
            </h2>

            <p>{manga.title_romaji}</p>
            <button className="details-button" onClick={() => openMangaDetails(manga.id)}>View details</button>
          </div>
        </div>

        <div className="buttons">
          <button
            className="skip"
            onClick={handleSkip}
            disabled={submitting}
          >
            ✕
          </button>

          <button
            className="like"
            onClick={handleLike}
            disabled={submitting}
          >
            ♥
          </button>
        </div>
      </main>
    </div>
  );
}

function ProfileSection({ title, mangas, emptyText, onSelect }) {
  return (
    <section className="profile-section">
      <h3>{title} ({mangas.length})</h3>
      {mangas.length === 0 ? (
        <p>{emptyText}</p>
      ) : (
        <div className="profile-manga-list">
          {mangas.map((manga) => (
            <button className="profile-manga" key={manga.id} onClick={() => onSelect(manga.id)}>
              <img src={manga.image} alt="" />
              <span>{manga.title_english || manga.title_romaji}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function plainText(value) {
  return (value || "No description available.").replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ");
}

export default App;
