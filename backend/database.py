import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "kenshu.db"

def get_db_connection():
    # timeout=15.0 ensures that if another process/thread locks the DB, it waits up to 15s
    conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
    # Enable dict-like access for rows
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    """テーブルを作成する"""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                month TEXT,
                uploaded_at TEXT,
                round INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                management_number TEXT,
                comment TEXT DEFAULT '',
                checked BOOLEAN DEFAULT 0,
                updated_at TEXT DEFAULT '',
                data TEXT DEFAULT '{}',
                FOREIGN KEY(session_id) REFERENCES sessions(id),
                UNIQUE(session_id, management_number)
            )
        """)
        
        # Create indexes to speed up lookup
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_month ON sessions(month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_session_id ON records(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_management_number ON records(management_number)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_records_session_mgmt ON records(session_id, management_number)")
        
        conn.commit()
    finally:
        conn.close()

# 初期化実行
init_db()

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
