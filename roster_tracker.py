import sqlite3
import time
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

SEASON = "2026-27"

db = sqlite3.connect("nba_injuries.db")
db.execute("""
CREATE TABLE IF NOT EXISTS nba_rosters (
    player_id INTEGER,
    player_name TEXT,
    team_id INTEGER,
    team_name TEXT,
    position TEXT,
    jersey TEXT,
    season TEXT,
    PRIMARY KEY (player_id, season)
)
""")

successful = 0

for team in teams.get_teams():
    print(f"Downloading {team['full_name']}...", flush=True)

    try:
        roster = commonteamroster.CommonTeamRoster(
            team_id=team["id"],
            season=SEASON,
            timeout=15
        ).get_data_frames()[0]

        if roster.empty:
            print("No players returned")
            continue

        for _, player in roster.iterrows():
            db.execute("""
                INSERT OR REPLACE INTO nba_rosters
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                int(player["PLAYER_ID"]),
                player["PLAYER"],
                team["id"],
                team["full_name"],
                player["POSITION"],
                str(player["NUM"]),
                SEASON
            ))

        db.commit()
        successful += 1
        print(f"Saved {len(roster)} players")

    except Exception as e:
        print(f"FAILED: {str(e)[:120]}")

    time.sleep(1)

count = db.execute(
    "SELECT COUNT(*) FROM nba_rosters WHERE season = ?",
    (SEASON,)
).fetchone()[0]

print(f"\nTeams downloaded: {successful}/30")
print(f"Players saved: {count}")

db.close()
