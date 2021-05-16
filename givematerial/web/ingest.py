import sqlite3
import sys

from givematerial.learningstatus import LearnableStatus, WanikaniStatus
from givematerial.cache import SqliteLearnableCache
from givematerial.db.sqlite import create_tables


def ingest(
        learnable_status_provider: LearnableStatus,
        cache: SqliteLearnableCache):
    known = learnable_status_provider.get_known_learnables()
    learning = learnable_status_provider.get_learning_learnables()

    cache.update_cache(learning, known)


if __name__ == '__main__':
    token = sys.argv[1]

    status = WanikaniStatus(token)

    conn = sqlite3.connect('givematerial.sqlite')
    create_tables(conn)

    cache = SqliteLearnableCache(conn, token)

    ingest(status, cache)
