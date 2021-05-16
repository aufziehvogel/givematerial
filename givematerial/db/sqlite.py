import sqlite3


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS user_status (
        learnable TEXT,
        status TEXT,
        user_id TEXT
    )''')
    cur.execute('CREATE INDEX idx_user_status_user_id ON user_status (user_id)')
    cur.execute('CREATE INDEX idx_user_status_user_id_status ON user_status (user_id, status)')
    conn.commit()
