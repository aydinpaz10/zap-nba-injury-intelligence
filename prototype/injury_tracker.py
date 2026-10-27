import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

URL = "https://official.nba.com/nba-injury-report-2026-27-season/"

db = sqlite3.connect("nba_injuries.db")
db.execute("""
CREATE TABLE IF NOT EXISTS reports (
    url TEXT PRIMARY KEY,
    discovered_at TEXT
)
""")

response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

reports = set()

for link in soup.find_all("a", href=True):
    url = urljoin(URL, link["href"])
    if "Injury-Report_" in url and ".pdf" in url:
        reports.add(url)

for url in reports:
    db.execute(
        "INSERT OR IGNORE INTO reports VALUES (?, ?)",
        (url, datetime.now(timezone.utc).isoformat())
    )

db.commit()

print(f"Found {len(reports)} injury reports")
print(f"Total saved: {db.execute('SELECT COUNT(*) FROM reports').fetchone()[0]}")

db.close()
