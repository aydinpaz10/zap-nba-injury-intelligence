import requests
import feedparser
import sqlite3
from datetime import datetime, timezone

url = "https://news.google.com/rss/search?q=NBA+injury&hl=en-US&gl=US&ceid=US:en"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

feed = feedparser.parse(response.content)

db = sqlite3.connect("nba_injuries.db")

db.execute("""
CREATE TABLE IF NOT EXISTS nba_news (
    url TEXT PRIMARY KEY,
    title TEXT,
    source TEXT,
    published TEXT,
    collected_at TEXT
)
""")

saved = 0

for article in feed.entries:
    result = db.execute("""
        INSERT OR IGNORE INTO nba_news
        VALUES (?, ?, ?, ?, ?)
    """, (
        article.link,
        article.title,
        "Google News",
        article.get("published", ""),
        datetime.now(timezone.utc).isoformat()
    ))
    saved += result.rowcount

db.commit()

print("Articles found:", len(feed.entries))
print("New articles saved:", saved)
print("Total in SQL:", db.execute(
    "SELECT COUNT(*) FROM nba_news"
).fetchone()[0])

print("\nLATEST HEADLINES:")
for row in db.execute(
    "SELECT title FROM nba_news ORDER BY published DESC LIMIT 5"
):
    print("-", row[0])

db.close()
