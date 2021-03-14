import classla
import json
from pathlib import Path
import re


def load_lemma_frequencies(freqs_file: Path):
    with open(freqs_file) as f:
        return json.load(f)


def iterate_lyrics(folder: Path):
    for lyrics_file in folder.glob('*/*'):
        with open(lyrics_file) as f:
            text = f.read()

        title = lyrics_file.name
        artist = lyrics_file.parent.name

        yield (artist, title, text)


if __name__ == '__main__':
    freqs_file = Path('data/vocabulary/word_frequencies.json')
    lyrics_folder = Path('data/lyrics/')

    freqs = load_lemma_frequencies(freqs_file)
    # restricting the processors to only "lemma" impairs prediction quality,
    # thus we just load all default processors
    nlp = classla.Pipeline('hr', type='nonstandard')

    for artist, title, text in iterate_lyrics(lyrics_folder):
        text = text.replace('\r\n', '\n')
        text = re.sub(r'\n\s*\n+', '\n', text)
        text = text.strip('\n')

        doc = nlp(text)
        lemmas = {}
        lemma_text = []
        for word in doc.iter_words():
            if word.lemma in freqs:
                lemmas[word.lemma] = freqs[word.lemma]
            else:
                lemmas[word.lemma] = None
            lemma_text.append(word.lemma)

        print(f'{artist} - {title}')
        print(lemmas)
