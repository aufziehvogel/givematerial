import json
import os
from pathlib import Path
import heapq
import dataclasses
import sqlite3
import uuid
from typing import List, Iterable, Optional

import givematerial.extractors
import givematerial.learningstatus


@dataclasses.dataclass
class Text:
    collection: str
    title: str
    text: str
    language: str
    url: Optional[str]


@dataclasses.dataclass
class TextStats:
    title: str
    text: str
    known: List[str]
    unknown: List[str]
    learning: List[str]
    total: int
    url: Optional[str]


def iterate_texts(folder: Path, language: str) -> Iterable[Text]:
    for text_file in folder.rglob('*.json'):
        with open(text_file) as f:
            text = json.load(f)

        if text['language'] != language:
            continue

        yield Text(
            collection=text['collection'],
            title=text['title'],
            text=text['text'],
            language=text['language'],
            url=text['url'] if 'url' in text else None)


class LearnableCache:
    def __init__(self, cache_folder: Path):
        self.cache_folder = cache_folder

    def check_cache(self, title: str) -> List[str]:
        cache_file = self._cache_file(title)

        if cache_file.is_file():
            with open(cache_file, 'rt') as f:
                return json.load(f)

        return []

    def write_cache(self, title: str, lemmas: List[str]):
        cache_file = self._cache_file(title)

        with open(cache_file, 'wt') as f:
            json.dump(lemmas, f)

    def _cache_file(self, title: str) -> Path:
        return self.cache_folder / f'{title}.json'


def calc_recommendations(language) -> List[TextStats]:
    freqs_file = Path('data') / language / 'word_frequencies.json'
    texts_folder = Path('data') / 'texts'
    known_words_file = Path('data') / language / 'known'
    learning_words_file = Path('data') / language / 'learning'
    cache_folder = Path('data') / language / 'cache'

    learnable_provider = os.getenv('LEARNABLE_PROVIDER', 'files')

    known_learning_status = givematerial.learningstatus.FileBasedStatus(
        known_words_file, None)

    if learnable_provider == 'files':
        learning_status = givematerial.learningstatus.FileBasedStatus(
            known_words_file, learning_words_file)

    elif learnable_provider == 'anki':
        deck_name = os.getenv('ANKI_DECK')
        learning_status = givematerial.learningstatus.AnkiStatus(deck_name)

    elif learnable_provider == 'wanikani':
        wanikani_token = os.getenv('WANIKANI_TOKEN')
        learning_status = givematerial.learningstatus.WanikaniStatus(
            wanikani_token)

    elif learnable_provider == 'sqlite':
        sqlite_conn = sqlite3.connect('givematerial.sqlite')
        user_identifier = os.getenv('USER_IDENTIFIER', 'local')

        learning_status = givematerial.learningstatus.SqliteBasedStatus(
            sqlite_conn, user_identifier)

    else:
        raise NotImplementedError(
            f'Unknown learnable provider "{learnable_provider}"')

    if language == 'hr':
        learnable_extractor = givematerial.extractors.CroatianLemmatizer(
            freqs_file)
    elif language == 'jp':
        learnable_extractor = givematerial.extractors.JapaneseKanjiExtractor()
    else:
        raise NotImplementedError(
            f'Extractor for language "{language}" does not exist')

    known_words = learning_status.get_known_learnables() \
        + known_learning_status.get_known_learnables()
    learning_words = learning_status.get_learning_learnables()

    return get_recommendations(
        known_words, learning_words, cache_folder, texts_folder, language,
        learnable_extractor)


# TODO: Cleanup this function, far too many arguments
def get_recommendations(
        known_words: List[str], learning_words: List[str], cache_folder: Path,
        texts_folder: Path, language: str,
        learnable_extractor, count: int = 5) -> List[TextStats]:
    recommendations = []

    cache = LearnableCache(cache_folder)

    for text in iterate_texts(texts_folder, language):
        relevant_lemmas = cache.check_cache(text.title)
        if len(relevant_lemmas) == 0:
            relevant_lemmas = learnable_extractor.extract_learnables(text.text)
            cache.write_cache(text.title, relevant_lemmas)

        known_from_text = \
            [lemma for lemma in relevant_lemmas if lemma in known_words]
        learning_from_text = \
            [lemma for lemma in relevant_lemmas if lemma in learning_words]
        unknown_from_text = [
            lemma for lemma in relevant_lemmas
            if lemma not in known_words and lemma not in learning_words
        ]

        # add a uuid so that heapq never tries to compare TextStats to TextStats
        order = (abs(len(unknown_from_text) - 5), -len(learning_from_text), -len(relevant_lemmas), uuid.uuid4())
        text_stats = TextStats(
            title=text.title,
            text=text.text,
            known=known_from_text,
            unknown=unknown_from_text,
            learning=learning_from_text,
            total=len(relevant_lemmas),
            url=text.url)
        heapq.heappush(recommendations, (order, text_stats))

    return [ts for _, ts in heapq.nsmallest(count, recommendations)]


# Not used at the moment, will implement later
#def calc_artist_summary():
#        artist_summary[artist].append(len(relevant_lemmas))
#        artist_words[artist].update(relevant_lemmas)
#
#    artist_summary = collections.defaultdict(list)
#    artist_words = collections.defaultdict(collections.Counter)
#
#    #for artist, lengths in artist_summary.items():
#    #    print(artist)
#    #    print(f'Min length: {min(lengths)}')
#    #    print(f'Max length: {max(lengths)}')
#    #    print(f'Avg length: {sum(lengths) / float(len(lengths))}')
#
#    #for artist, words in artist_words.items():
#    #    known_from_artist = set(words).intersection(known_words)
#    #    unknown_from_artist = collections.Counter(words)
#    #    for word in known_words:
#    #        del unknown_from_artist[word]
#
#    #    print(artist)
#    #    print(f'Total vocab: {len(words)}')
#    #    print(f'Known vocab: {len(known_from_artist)}')
#    #    print(f'Unknown words: {unknown_from_artist.most_common()[0:50]}')
#