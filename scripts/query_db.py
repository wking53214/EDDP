#!/usr/bin/env python3
"""Run a SQL query against data/conversations.db
Usage: python3 scripts/query_db.py "SELECT count(*) FROM messages"
"""
import sqlite3, sys, os
DB='data/conversations.db'
if not os.path.exists(DB):
    print('DB not found. Run scripts/build_db.py first.')
    raise SystemExit(1)
q=' '.join(sys.argv[1:]) if len(sys.argv)>1 else 'SELECT conversation, COUNT(*) as cnt FROM messages GROUP BY conversation ORDER BY cnt DESC LIMIT 10;'
conn=sqlite3.connect(DB)
cur=conn.cursor()
for row in cur.execute(q):
    print(row)
conn.close()
