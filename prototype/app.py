import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="NBA Injury Intelligence",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Injury Intelligence")
st.caption("NBA injury news and player availability research")

db = sqlite3.connect("nba_injuries.db")

df = pd.read_sql_query("""
    SELECT title, source, published, url
    FROM nba_news
""", db)

db.close()

df["published_dt"] = pd.to_datetime(df["published"], format="mixed", utc=True, errors="coerce")
df = df.sort_values("published_dt", ascending=False)

st.metric("Articles Tracked", len(df))

search = st.text_input(
    "Search players, teams, or injuries",
    placeholder="Stephen Curry"
)

if search:
    df = df[
        df["title"].str.contains(
            search, case=False, na=False, regex=False
        )
    ]

st.subheader(f"News Results ({len(df)})")

for _, article in df.iterrows():
    with st.container(border=True):
        st.markdown(f"**{article['title']}**")
        st.caption(article["published"])
        st.link_button("Read Article", article["url"])
