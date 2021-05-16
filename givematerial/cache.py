import sqlite3
from typing import List, Tuple


class SqliteLearnableCache:
    def __init__(self, conn: sqlite3.Connection, user_identifier: str):
        self.conn = conn
        self.user_identifier = user_identifier

    def read_cache(self) -> Tuple[List[str], List[str]]:
        cur = self.conn.cursor()

        cur.execute(
            'SELECT learnable, status FROM user_status WHERE user_id = ?',
            (self.user_identifier,))

        learning = []
        known = []
        for row in cur.fetchall():
            if row[1] == 'learning':
                learning.append(row[0])
            elif row[1] == 'known':
                known.append(row[0])

        return learning, known

    def update_cache(self, learning: List[str], known: List[str]):
        cur = self.conn.cursor()

        cur.execute(
            'DELETE FROM user_status WHERE user_id = ?', (self.user_identifier,))

        cur.executemany(
            'INSERT INTO user_status (user_id, learnable, status) VALUES (?, ?, "learning")',
            [(self.user_identifier, learnable) for learnable in learning])
        cur.executemany(
            'INSERT INTO user_status (user_id, learnable, status) VALUES (?, ?, "known")',
            [(self.user_identifier, learnable) for learnable in known])

        self.conn.commit()
