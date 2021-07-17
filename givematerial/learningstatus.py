import abc
import json
import logging
from pathlib import Path
import requests
import sqlite3
import tempfile
import time
from typing import Any, Dict, Iterable, List, Optional


class LearnableStatus(abc.ABC):
    @abc.abstractmethod
    def get_known_learnables(self):
        pass

    @abc.abstractmethod
    def get_learning_learnables(self):
        pass


class FileBasedStatus(LearnableStatus):
    """Uses local text files to read known and learning words"""
    def __init__(
            self, known_words_file: Path, learning_words_file: Optional[Path]):
        self.known_words_file = known_words_file
        self.learning_words_file = learning_words_file

    def get_known_learnables(self) -> List[str]:
        return self._read_words_file(self.known_words_file)

    def get_learning_learnables(self) -> List[str]:
        return self._read_words_file(self.learning_words_file)

    @staticmethod
    def _read_words_file(path: Optional[Path]) -> List[str]:
        try:
            with open(path) as f:
                return [word.strip() for word in f]
        except OSError:
            return []
        except TypeError:
            return []


class SqliteBasedStatus(LearnableStatus):
    """Read learning status from SQLite"""
    def __init__(
            self, conn: sqlite3.Connection, user_identifier: str,
            language: str = None):
        self.conn = conn
        self.user_identifier = user_identifier
        self.language = language

    def get_known_learnables(self) -> List[str]:
        return self._get_by_status('known')

    def get_learning_learnables(self) -> List[str]:
        return self._get_by_status('learning')

    def _get_by_status(self, status: str) -> List[str]:
        cur = self.conn.cursor()

        if self.language:
            cur.execute(
                'SELECT learnable FROM user_status WHERE user_id = ? '
                'AND status = ? AND language = ?',
                (self.user_identifier, status, self.language))
        else:
            cur.execute(
                'SELECT learnable FROM user_status WHERE user_id = ? '
                'AND status = ?',
                (self.user_identifier, status))

        return [row[0] for row in cur.fetchall()]

    @staticmethod
    def _read_words_file(path: Optional[Path]) -> List[str]:
        try:
            with open(path) as f:
                return [word.strip() for word in f]
        except OSError:
            return []


class WanikaniStatus(LearnableStatus):
    """Reads kanji learning status from Wanikani"""
    def __init__(self, token: str):
        self.cache_file = \
            Path(tempfile.gettempdir()) / 'givematerial_wanikani.json'

        self.token = token
        self.headers = {
            'Wanikani-Revision': '20170710',
            'Authorization': f'Bearer {token}',
        }

        self.subjects = self._fetch_subjects()

        self.known_learnables = []
        self.learning_learnables = []

    def get_known_learnables(self) -> List[str]:
        if not self.known_learnables:
            self.known_learnables = self._fetch_known_kanji()

        return self.known_learnables

    def get_learning_learnables(self) -> List[str]:
        if not self.learning_learnables:
            self.learning_learnables = self._fetch_learning_kanji()

        return self.learning_learnables

    def _fetch_subjects(self) -> Dict[int, str]:
        subjects = self._load_local()
        if subjects:
            return subjects

        start_url = 'https://api.wanikani.com/v2/subjects'
        for data in self._iterate_wanikani(start_url):
            for subject in data:
                if subject['object'] == 'kanji':
                    subject_id = subject['id']
                    kanji = subject['data']['characters']

                    subjects[subject_id] = kanji

        self._store_local(subjects)
        return subjects

    def _fetch_learning_kanji(self):
        return self._fetch_kanji(levels=[1, 2, 3, 4])

    def _fetch_known_kanji(self):
        return self._fetch_kanji(levels=[5, 6, 7, 8, 9])

    def _fetch_kanji(self, levels: List[int]):
        levels_list = ','.join(map(str, levels))

        kanji = []
        start_url = \
            f'https://api.wanikani.com/v2/assignments?srs_stages={levels_list}'
        for data in self._iterate_wanikani(start_url):
            for assignment in data:
                if assignment['data']['subject_type'] == 'kanji':
                    subject_id = assignment['data']['subject_id']
                    kanji.append(self.subjects[subject_id])

        return kanji

    def _iterate_wanikani(self, start_url: str) -> Iterable[Any]:
        next_url = start_url

        while next_url:
            logging.debug(f'Fetching Wanikani URL {next_url}')

            response = requests.get(next_url, headers=self.headers)
            data = response.json()
            yield data['data']

            time.sleep(1)
            next_url = data['pages']['next_url']

    def _store_local(self, subjects: Dict[int, str]):
        with open(self.cache_file, 'wt') as f:
            json.dump(subjects, f)

    def _load_local(self) -> Dict[int, str]:
        try:
            with open(self.cache_file, 'rt') as f:
                data = json.load(f)
                # for some reason integer keys are converted to JSON strings
                # when I save the cache with json.dump
                return dict([(int(key), value) for key, value in data.items()])
        except FileNotFoundError:
            return {}


class AnkiStatus(LearnableStatus):
    """Reads learning status from Anki"""
    def __init__(self, deck_name: str):
        self.server = 'http://localhost:8765'
        self.deck_name = deck_name

        self.card_intervals = []

    def get_known_learnables(self) -> List[str]:
        if not self.card_intervals:
            self.card_intervals = self._get_intervals()

        return [word for (word, interval) in self.card_intervals.items()
                if interval >= 7]

    def get_learning_learnables(self) -> List[str]:
        if not self.card_intervals:
            self.card_intervals = self._get_intervals()

        return [word for (word, interval) in self.card_intervals.items()
                if 0 < interval < 7]

    def _get_intervals(self) -> Dict[str, int]:
        cards = self._perform_request(
            'findCards', {'query': f'deck:{self.deck_name}'})
        card_infos = self._perform_request('cardsInfo', {'cards': cards})

        intervals = {}
        for card in card_infos:
            word = card['fields']['Front']['value']
            interval = card['interval']

            intervals[word] = interval

        return intervals

    def _perform_request(self, action: str, params: Dict[str, Any]) -> Any:
        data = {
            'action': action,
            'version': 6,
            'params': params,
        }
        result = requests.post(self.server, json=data)
        return result.json()['result']
