#!/usr/bin/env python3
"""Build SQLite DB from data/raw.jsonl and index/manifest.json
Usage: python3 scripts/build_db.py
"""
import sqlite3, json, os
from datetime import datetime

RAW_JSONL='data/raw.jsonl'
MANIFEST='index/manifest.json'
DB_PATH='data/conversations.db'

if not os.path.exists(RAW_JSONL):
    print('raw.jsonl not found:', RAW_JSONL)
    raise SystemExit(1)

conn=sqlite3.connect(DB_PATH)
cur=conn.cursor()
# create tables
cur.executescript('''
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  safe_id TEXT,
  start_time TEXT,
  end_time TEXT,
  participants TEXT,
  message_count INTEGER,
  transcript TEXT,
  summary TEXT,
  source TEXT
);
CREATE TABLE messages (
  rowid INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation TEXT,
  time TEXT,
  author TEXT,
  author_orig TEXT,
  message_raw TEXT,
  message TEXT,
  source TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation);
CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(time);
''')
conn.commit()

# load conversations metadata if present
if os.path.exists(MANIFEST):
    with open(MANIFEST,'r',encoding='utf-8') as f:
        mf=json.load(f)
    convs=mf.get('conversations', [])
    for c in convs:
        cur.execute('''INSERT OR REPLACE INTO conversations (id,safe_id,start_time,end_time,participants,message_count,transcript,summary,source) VALUES (?,?,?,?,?,?,?,?,?)''', (
            c.get('id'), c.get('safe_id'), c.get('start_time'), c.get('end_time'), json.dumps(c.get('participants') or []), c.get('message_count') or 0, c.get('transcript'), c.get('summary'), c.get('source')
        ))
    conn.commit()

# stream raw.jsonl into messages table
cnt=0
with open(RAW_JSONL,'r',encoding='utf-8') as f:
    to_insert=[]
    for line in f:
        if not line.strip():
            continue
        obj=json.loads(line)
        to_insert.append((obj.get('conversation'), obj.get('time'), obj.get('author'), obj.get('author_orig'), obj.get('message_raw'), obj.get('message'), obj.get('source')))
        if len(to_insert)>=1000:
            cur.executemany('INSERT INTO messages (conversation,time,author,author_orig,message_raw,message,source) VALUES (?,?,?,?,?,?,?)', to_insert)
            conn.commit()
            cnt+=len(to_insert)
            to_insert=[]
    if to_insert:
        cur.executemany('INSERT INTO messages (conversation,time,author,author_orig,message_raw,message,source) VALUES (?,?,?,?,?,?,?)', to_insert)
        conn.commit()
        cnt+=len(to_insert)
print('Inserted messages:', cnt)
conn.close()
