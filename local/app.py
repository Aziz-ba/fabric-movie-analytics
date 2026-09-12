"""Interactive dashboard over the Gold tables produced by local/pipeline.py.

    pip install streamlit pandas plotly
    python local/pipeline.py     # build the gold tables first
    streamlit run local/app.py
"""
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

GOLD = pathlib.Path(__file__).resolve().parent / "gold"

st.set_page_config(page_title="Movie Analytics", layout="wide")
st.title("🎬 Movie Analytics — Gold layer dashboard")
st.caption("Interactive view of the medallion pipeline's Gold tables (run local/pipeline.py first).")

if not (GOLD / "rating_by_genre.csv").exists():
    st.warning("Gold tables not found. Run `python local/pipeline.py` first.")
    st.stop()

genre = pd.read_csv(GOLD / "rating_by_genre.csv")
decade = pd.read_csv(GOLD / "rating_by_decade.csv")
directors = pd.read_csv(GOLD / "top_directors.csv")
corr = pd.read_csv(GOLD / "rating_correlations.csv")
corr.columns = ["feature", "correlation_with_rating"]

c1, c2 = st.columns(2)
with c1:
    st.subheader("Average rating by genre")
    st.plotly_chart(px.bar(genre.sort_values("avg_rating"), x="avg_rating", y="genre",
                           orientation="h", height=500), use_container_width=True)
with c2:
    st.subheader("What correlates with rating?")
    st.plotly_chart(px.bar(corr.sort_values("correlation_with_rating"),
                           x="correlation_with_rating", y="feature", orientation="h",
                           height=500, color="correlation_with_rating",
                           color_continuous_scale="RdBu"), use_container_width=True)

st.subheader("Average rating by decade")
st.plotly_chart(px.line(decade, x="decade", y="avg_rating", markers=True), use_container_width=True)

st.subheader("Top directors (min 5 films)")
st.dataframe(directors, use_container_width=True)
