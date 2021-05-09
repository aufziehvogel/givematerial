import classla
import json
from pathlib import Path
import re
from typing import Dict, List, Optional


class CroatianLemmatizer():
    def __init__(self, word_freqs_file: Path):
        self.freqs = self._load_lemma_frequencies(word_freqs_file)

        # restricting the processors to only "lemma" impairs prediction quality,
        # thus we just load all default processors
        self.nlp = classla.Pipeline('hr', type='nonstandard')

    def extract_learnables(self, text: str) -> List[str]:
        lemmas = self._text_lemmas(text)

        relevant_lemmas = [
            lemma for lemma, count in lemmas.items()
            # ignore special characters like dot or comma
            if count and not re.match('^[^a-z]+$', lemma)
        ]

        return relevant_lemmas

    def _text_lemmas(self, text: str) -> Dict[str, Optional[float]]:
        text = text.replace('\r\n', '\n')
        text = re.sub(r'\n\s*\n+', '\n', text)
        text = text.strip('\n')

        doc = self.nlp(text)
        lemmas = {}
        for word in doc.iter_words():
            if word.lemma in self.freqs:
                lemmas[word.lemma] = self.freqs[word.lemma]
            else:
                lemmas[word.lemma] = None

        return lemmas

    @staticmethod
    def _load_lemma_frequencies(freqs_file: Path):
        with open(freqs_file) as f:
            return json.load(f)


class JapaneseKanjiExtractor:
    def extract_learnables(self, text: str) -> List[str]:
        regex = u'[\u4e00-\u9faf\u3400-\u4dbf]'
        p = re.compile(regex, re.U)
        # remove duplicates
        return list(set(p.findall(text)))
