import logging
from pathlib import Path
import requests
import time
from typing import Any, Dict, Iterable, List


class FileBasedStatus:
    """Uses local text files to read known and learning words"""
    def __init__(self, known_words_file: Path, learning_words_file: Path):
        self.known_words_file = known_words_file
        self.learning_words_file = learning_words_file

    def get_known_learnables(self) -> List[str]:
        return self._read_words_file(self.known_words_file)

    def get_learning_learnables(self) -> List[str]:
        return self._read_words_file(self.learning_words_file)

    @staticmethod
    def _read_words_file(path: Path) -> List[str]:
        with open(path) as f:
            return [word.strip() for word in f]


class WanikaniStatus:
    """Reads kanji learning status from Wanikani"""
    def __init__(self, token: str):
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
        # TODO: cache this on local disk
        logging.warning(
            'Cache not implemented, yet. Pulling all subjects from Wanikani '
            'each time. Do not call too often.')

        subjects = {}

        start_url = 'https://api.wanikani.com/v2/subjects'
        for data in self._iterate_wanikani(start_url):
            for subject in data:
                if subject['object'] == 'kanji':
                    subject_id = subject['id']
                    kanji = subject['data']['characters']

                    subjects[subject_id] = kanji

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
