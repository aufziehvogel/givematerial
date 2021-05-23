import sqlite3


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS user_status (
        learnable TEXT,
        status TEXT,
        user_id TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_user_status_user_id ON user_status (user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_user_status_user_id_status ON user_status (user_id, status)')

    cur.execute('''CREATE TABLE IF NOT EXISTS reading_list (
        user_id TEXT,
        text_url TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_reading_list_user_id ON reading_list (user_id)')

    cur.execute('''CREATE TABLE IF NOT EXISTS token_requests (
        user_id TEXT
    )''')
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_token_requests_user_id ON token_requests (user_id)')

    conn.commit()
