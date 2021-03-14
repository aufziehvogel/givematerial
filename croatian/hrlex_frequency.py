import collections
import json


if __name__ == '__main__':
    with open('data/vocabulary/hrLex_v1.3') as f:
        freqs = collections.defaultdict(float)
        for line in f:
            _, lemma, _, _, _, _, _, per_million_freq = line.split('\t')
            freqs[lemma] += float(per_million_freq)

    with open('data/vocabulary/word_frequencies.json', 'wt') as f:
        json.dump(freqs, f)
