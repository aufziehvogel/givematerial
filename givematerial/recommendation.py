import classla
import json
from pathlib import Path
import re
import heapq
import dataclasses
import uuid
from typing import Dict, List, Optional


@dataclasses.dataclass
class TextStats:
    artist: str
    title: str
    text: str
    unknown: List[str]
    learning: int
    total: int


def load_lemma_frequencies(freqs_file: Path):
    with open(freqs_file) as f:
        return json.load(f)


def iterate_lyrics(folder: Path):
    for lyrics_file in folder.glob('*/*'):
        with open(lyrics_file) as f:
            text = f.read()

        title = lyrics_file.name
        artist = lyrics_file.parent.name

        yield artist, title, text


def text_lemmas(artist: str, title: str, text: str, cache_folder, nlp, freqs) -> Dict[str, Optional[float]]:
    cache_file = cache_folder / f'{artist}-{title}.json'
    if cache_file.is_file():
        with open(cache_file, 'rt') as f:
            lemmas = json.load(f)
    else:
        text = text.replace('\r\n', '\n')
        text = re.sub(r'\n\s*\n+', '\n', text)
        text = text.strip('\n')

        doc = nlp(text)
        lemmas = {}
        for word in doc.iter_words():
            if word.lemma in freqs:
                lemmas[word.lemma] = freqs[word.lemma]
            else:
                lemmas[word.lemma] = None

        with open(cache_file, 'wt') as f:
            json.dump(lemmas, f)

    return lemmas


def read_words_file(path: Path):
    with open(path) as f:
        return [word.strip() for word in f]


def calc_recommendations(language):
    freqs_file = Path('data') / language / 'word_frequencies.json'
    lyrics_folder = Path('data') / language / 'lyrics'
    known_words_file = Path('data') / language / 'known'
    learning_words_file = Path('data') / language / 'learning'
    cache_folder = Path('data') / language / 'cache'

    known_words = read_words_file(known_words_file)
    learning_words = read_words_file(learning_words_file)

    freqs = load_lemma_frequencies(freqs_file)
    # restricting the processors to only "lemma" impairs prediction quality,
    # thus we just load all default processors
    nlp = classla.Pipeline('hr', type='nonstandard')

    recommendations = []

    for artist, title, text in iterate_lyrics(lyrics_folder):
        lemmas = text_lemmas(artist, title, text, cache_folder, nlp, freqs)

        relevant_lemmas = [
            lemma for lemma, count in lemmas.items()
            # ignore special characters like dot or comma
            if count and not re.match('^[^a-z]+$', lemma)
        ]

        known_from_text = \
            [lemma for lemma in relevant_lemmas if lemma in known_words]
        learning_from_text = \
            [lemma for lemma in relevant_lemmas if lemma in learning_words]
        unknown_from_text = [
            lemma for lemma in relevant_lemmas
            if lemma not in known_words and lemma not in learning_words
        ]

        all_word_freqs = []
        unknown_word_freqs = []
        for word in relevant_lemmas:
            all_word_freqs.append(lemmas[word])
        for word in unknown_from_text:
            unknown_word_freqs.append(lemmas[word])

        # add a uuid so that heapq never tries to compare TextStats to TextStats
        order = (abs(len(unknown_from_text) - 5), -len(learning_from_text), -len(relevant_lemmas), uuid.uuid4())
        text_stats = TextStats(
            artist=artist,
            title=title,
            text=text,
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