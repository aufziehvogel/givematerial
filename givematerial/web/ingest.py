import logging
import os
import sqlite3
import time

from givematerial.learningstatus import LearnableStatus, WanikaniStatus
from givematerial.cache import SqliteLearnableCache
from givematerial.db.sqlite import create_tables


def ingest(
        learnable_status_provider: LearnableStatus,
        cache: SqliteLearnableCache):
    known = learnable_status_provider.get_known_learnables()
    learning = learnable_status_provider.get_learning_learnables()

    cache.update_cache(learning, known)


def add_download_request(token: str, conn: sqlite3.Connection):
    c = conn.cursor()
    try:
        c.execute('INSERT INTO token_requests (user_id) VALUES (?)', (token,))
        conn.commit()
    except sqlite3.IntegrityError:
        # just ignore duplicate errors
        pass


def get_open_download_requests(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute('SELECT user_id FROM token_requests')

    return [row[0] for row in c.fetchall()]


def finish_download_request(token: str, conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute('DELETE FROM token_requests WHERE user_id = ?', (token,))
    conn.commit()


def loop(conn: sqlite3.Connection):
    while True:
        for token in get_open_download_requests(conn):
            logging.info(f'Fetch info for token {token} from Wanikani')
            status = WanikaniStatus(token)
            cache = SqliteLearnableCache(conn, token)

            ingest(status, cache)

            finish_download_request(token, conn)

        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('LOGLEVEL'))
    sqlite_conn = sqlite3.connect('givematerial.sqlite')
    create_tables(sqlite_conn)
    loop(sqlite_conn)
