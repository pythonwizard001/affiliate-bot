# scripts/queue_manager.py
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("data/jobs.db")

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB.as_posix())
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seed TEXT,
        title TEXT,
        slug TEXT UNIQUE,
        meta TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        updated_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def enqueue_briefs(briefs):
    conn = sqlite3.connect(DB.as_posix())
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for b in briefs:
        try:
            cur.execute(
                "INSERT INTO briefs (seed,title,slug,meta,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (b['seed'], b['title'], b['slug'], b.get('meta',''), now, now)
            )
        except sqlite3.IntegrityError:
            # duplicate slug -> skip
            continue
    conn.commit()
    conn.close()

def fetch_pending(limit=10):
    conn = sqlite3.connect(DB.as_posix())
    cur = conn.cursor()
    cur.execute("SELECT id,seed,title,slug,meta FROM briefs WHERE status='pending' ORDER BY id LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(id=r[0], seed=r[1], title=r[2], slug=r[3], meta=r[4]) for r in rows]

def mark(id, status):
    conn = sqlite3.connect(DB.as_posix())
    cur = conn.cursor()
    cur.execute("UPDATE briefs SET status=?, updated_at=? WHERE id=?", (status, datetime.utcnow().isoformat(), id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized:", DB.as_posix())
