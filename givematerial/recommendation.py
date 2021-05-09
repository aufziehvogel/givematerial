import json
from pathlib import Path
import heapq
import dataclasses
import uuid
from typing import List, Iterable

import givematerial.extractors


@dataclasses.dataclass
class Text:
    collection: str
    title: str
    text: str
    language: str


@dataclasses.dataclass
class TextStats:
    title: str
    text: str
    unknown: List[str]
    learning: int
    total: int


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
            language=text['language'])


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


def read_words_file(path: Path):
    with open(path) as f:
        return [word.strip() for word in f]


def calc_recommendations(language):
    freqs_file = Path('data') / language / 'word_frequencies.json'
    texts_folder = Path('data') / 'texts'
    known_words_file = Path('data') / language / 'known'
    learning_words_file = Path('data') / language / 'learning'
    cache_folder = Path('data') / language / 'cache'

    known_words = read_words_file(known_words_file)
    learning_words = read_words_file(learning_words_file)

    if language == 'hr':
        learnable_extractor = givematerial.extractors.CroatianLemmatizer(
            freqs_file)
    elif language == 'jp':
        learnable_extractor = givematerial.extractors.JapaneseKanjiExtractor()
    else:
        raise NotImplementedError(
            f'Extractor for language "{language}" does not exist')

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
            unknown=unknown_from_text,
            learning=len(learning_from_text),
            total=len(relevant_lemmas))
        heapq.heappush(recommendations, (order, text_stats))

    return heapq.nsmallest(5, recommendations)


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