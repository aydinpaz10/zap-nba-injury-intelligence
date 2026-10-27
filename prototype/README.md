# NBA Injury Tracker — Original Prototype

This folder contains the original Python prototype that eventually developed into [Zap NBA Injury Intelligence](https://zapnba.com).

## Features
- Collects NBA injury report links.
- Retrieves NBA roster information.
- Tracks NBA injury news through RSS feeds.
- Stores collected information in SQLite.
- Displays searchable injury news using Streamlit.

## Installation

Requires Python 3.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Prototype

From the `prototype` directory, run:

```bash
python news_tracker.py
python injury_tracker.py
python roster_tracker.py
streamlit run app.py
```

The scripts create and populate a local SQLite database named `nba_injuries.db`.

**Note:** This is an early prototype, not the production code powering zapnba.com. External data sources may have changed, and successful execution is not guaranteed.
