Query support using SQLite

Files:
- data/conversations.db : SQLite database containing tables `conversations` and `messages`.
- scripts/build_db.py : Build or rebuild the DB from data/raw.jsonl and index/manifest.json.
- scripts/query_db.py : Run ad-hoc SQL queries against the DB.
- queries/examples.sql : Example queries to get started.

Usage:
1. Rebuild DB: python3 scripts/build_db.py
2. Run a query: python3 scripts/query_db.py "SELECT count(*) FROM messages"

This setup enables fast SQL queries from notebooks or command line. Replace or extend with DuckDB/Parquet if you prefer columnar analytics.
