import sqlite3


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS user (
        user_id TEXT,
        oauth_name TEXT,
        oauth_provider TEXT,
        display_name TEXT,
        language TEXT,
        last_login DATETIME,
        wanikani_token TEXT,
        UNIQUE(oauth_name, oauth_provider),
        UNIQUE(user_id)
    )''')

    # TODO: Use a numeric id for foreign key to user
    cur.execute('''CREATE TABLE IF NOT EXISTS srs (
        user_id TEXT,
        name TEXT,
        login TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_srs_user_id ON srs (user_id)')

    cur.execute('''CREATE TABLE IF NOT EXISTS user_status (
        learnable TEXT,
        status TEXT,
        user_id TEXT,
        language TEXT
    )''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_user_status_user_id ON user_status (user_id, language)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_user_status_user_id_status ON user_status (user_id, status, language)')

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
