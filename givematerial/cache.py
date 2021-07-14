import sqlite3
from typing import List, Tuple


class SqliteLearnableCache:
    def __init__(
            self, conn: sqlite3.Connection, user_identifier: str,
            language: str):
        self.conn = conn
        self.user_identifier = user_identifier
        self.language = language

    def read_cache(self) -> Tuple[List[str], List[str]]:
        cur = self.conn.cursor()

        cur.execute(
            'SELECT learnable, status FROM user_status '
            'WHERE user_id = ? AND language = ?',
            (self.user_identifier, self.language))

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
            'DELETE FROM user_status WHERE user_id = ? AND language = ?',
            (self.user_identifier, self.language))

        cur.executemany(
            'INSERT INTO user_status (user_id, learnable, status, language) VALUES (?, ?, "learning", ?)',
            [(self.user_identifier, learnable, self.language) for learnable in learning])
        cur.executemany(
            'INSERT INTO user_status (user_id, learnable, status, language) VALUES (?, ?, "known", ?)',
            [(self.user_identifier, learnable, self.language) for learnable in known])

        self.conn.commit()
