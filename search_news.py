import sqlite3

db = sqlite3.connect("nba_injuries.db")

player = input("Search player or team: ").strip()

rows = db.execute("""
    SELECT title, published, url
    FROM nba_news
    WHERE title LIKE ?
    ORDER BY published DESC
    LIMIT 10
""", (f"%{player}%",)).fetchall()

print(f"\nFound {len(rows)} articles:\n")

for title, published, url in rows:
    print(title)
    print(published)
    print(url)
    print()

db.close()
