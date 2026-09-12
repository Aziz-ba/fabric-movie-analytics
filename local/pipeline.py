"""Local, dependency-light reproduction of the Fabric medallion pipeline.

Runs the same Bronze -> Silver -> Gold logic with pandas on data/movie_metadata.csv,
so anyone can reproduce the analytics without a Microsoft Fabric workspace.

    python local/pipeline.py
"""
import pathlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD = ROOT / "local" / "gold"
ASSETS = ROOT / "assets"
GOLD.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

# ---------- BRONZE: raw ingest ----------
bronze = pd.read_csv(ROOT / "data" / "movie_metadata.csv")

# ---------- SILVER: clean, type, derive ----------
silver = bronze.copy()
silver["movie_title"] = silver["movie_title"].str.replace("\xa0", "", regex=False).str.strip()
silver = silver.dropna(subset=["imdb_score", "title_year"])
silver["title_year"] = silver["title_year"].astype(int)
silver["decade"] = (silver["title_year"] // 10 * 10).astype(int)
# ROI where we have both budget and gross (same-currency caveat noted in README)
silver["roi"] = silver["gross"] / silver["budget"]

# ---------- GOLD: analytics-ready aggregates ----------
# 1) Top movies by rating (with a minimum vote threshold)
top_movies = (silver[silver["num_voted_users"] >= 100000]
              .sort_values("imdb_score", ascending=False)
              [["movie_title", "title_year", "imdb_score", "num_voted_users"]]
              .head(20))
top_movies.to_csv(GOLD / "top_movies.csv", index=False)

# 2) Rating by genre (a movie can have several genres)
genre = silver.assign(genre=silver["genres"].str.split("|")).explode("genre")
by_genre = (genre.groupby("genre")
            .agg(avg_rating=("imdb_score", "mean"), films=("imdb_score", "size"))
            .query("films >= 50").sort_values("avg_rating", ascending=False).round(2))
by_genre.to_csv(GOLD / "rating_by_genre.csv")

# 3) Rating by decade
by_decade = (silver.groupby("decade")
             .agg(avg_rating=("imdb_score", "mean"), films=("imdb_score", "size"))
             .round(2))
by_decade.to_csv(GOLD / "rating_by_decade.csv")

# 4) Top directors (min 5 films)
by_director = (silver.groupby("director_name")
               .agg(avg_rating=("imdb_score", "mean"), films=("imdb_score", "size"))
               .query("films >= 5").sort_values("avg_rating", ascending=False).round(2).head(15))
by_director.to_csv(GOLD / "top_directors.csv")

# 5) Correlations with rating
corr = silver[["imdb_score", "budget", "gross", "duration", "num_voted_users",
               "movie_facebook_likes"]].corr()["imdb_score"].drop("imdb_score").round(3)
corr.sort_values().to_csv(GOLD / "rating_correlations.csv")

# ---------- Charts ----------
ax = by_genre["avg_rating"].sort_values().plot(kind="barh", figsize=(7, 6), color="#117865")
ax.set_title("Average IMDb score by genre"); ax.set_xlabel("Avg IMDb score")
plt.tight_layout(); plt.savefig(ASSETS / "rating_by_genre.png", dpi=130); plt.close()

ax = by_decade["avg_rating"].plot(marker="o", figsize=(7, 4), color="#29B5E8")
ax.set_title("Average IMDb score by decade"); ax.set_ylabel("Avg IMDb score"); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(ASSETS / "rating_by_decade.png", dpi=130); plt.close()

# ---------- Insights to stdout ----------
print("=== KEY INSIGHTS ===")
print(f"Movies analyzed (silver): {len(silver)}")
print(f"Best genre: {by_genre.index[0]} ({by_genre.iloc[0]['avg_rating']} avg over {int(by_genre.iloc[0]['films'])} films)")
print(f"Worst genre: {by_genre.index[-1]} ({by_genre.iloc[-1]['avg_rating']} avg)")
print(f"Budget vs rating correlation: {corr['budget']}  (gross: {corr['gross']}, votes: {corr['num_voted_users']}, duration: {corr['duration']})")
print(f"Best decade: {by_decade['avg_rating'].idxmax()}s ({by_decade['avg_rating'].max()})")
print(f"Top director (>=5 films): {by_director.index[0]} ({by_director.iloc[0]['avg_rating']})")
print("Gold tables + charts written.")
