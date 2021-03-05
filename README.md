# GiveMaterial

GiveMaterial should become a collection of scripts or tool to help you
find material (e.g. music, texts) in foreign languages.

The idea is to use your knowledge, compare it to a list of available material
and then propose something useful to you.

It's more a collection of ideas at the moment. Hope I will be able to do it
step-by-step.

## Requirements

1. create vocabulary lists of most important vocab for a language, e.g. for Anki
2. extract current knowledge of vocabulary from vocab learning tool
3. collect lyrics/texts in foreign languages (lyrics probably best for starting)
4. standardize words in texts (lemmatization?) -> list of vocabulary in lyrics
5. compare vocabulary knowledge to collected lyrics, recommend good matches
6. provide link to recommended lyrics and youtube video

Useful sets of tasks on their own:

- `1.`: Gives us list of vocab to learn
- `3. + 4.`: Gives us a nice collection of lyrics with the vocab they contain


## Croatian

- lyrics can be found on [tekstovi.net](https://tekstovi.net/)
- lemmatization with [cstlemma](https://github.com/kuhumcst/cstlemma)
  and [models from Agic et al.](http://nlp.ffzg.hr/resources/models/tagging/)
  (old version?) or the API (latest version?)
  - models from ffzg blog led to segfault, but models distributed by cstlemma
    work fine (much bigger dict file for some reason)
- vocabulary lists:
  - FFZG has a [psycholinguistic database with frequency counts](http://megahr.ffzg.unizg.hr/en/?page_id=609) - but doesn't
    contain basic words which are irrelevant to their project
  - [Wikipedia list](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Serbo-Croatian_wordlist) - many mistakes with inflections etc.
  - [Mnemosyne list](https://mnemosyne-proj.org/cards/2500-english-croatian-vocabulary-cards) - saw at least one minor mistake, but in general looks OK
  - [easy-croatian.com Anki deck](https://ankiweb.net/shared/info/190661393) -
    not sorted by frequency
- vocabulary including frequencies:
  - Ljubešić, Nikola, 2019, Inflectional lexicon hrLex 1.3,
    Slovenian language resource repository CLARIN.SI,
    http://hdl.handle.net/11356/1232. 

### Getting Started

To get started with Croatian fetch some lyrics for your favourite artist, e.g.
Prljavo Kazaliste:

```bash
python croatian/retrieval/tekstovi_lyrics.py \
    --url https://tekstovi.net/2,206,0.html --output data/lyrics
```

This will download the lyrics and store them in text files in the folder
`data/lyrics`.

Next, you can use a lemmatizer to lemmatize the lyrics. Currently, we only
support the locally installed `cstlemma`, but this will change soon.

```bash
# Install cstlemma and download Croatian models
cd tools/cstlemma
bash install.sh
cd ../../

./tools/cstlemma/cstlemma/cstlemma \
    -d tools/cstlemma/models/croatian/dict \
    -f tools/cstlemma/models/croatian/flexrules \
    -i data/lyrics/Prljavo\ Kazaliste/Kise\ jesenje
```

### Open Issues

For raw `cstlemma` you have to remove all punctuation. Otherwise words won't
be recognized. Currently, this is not handled by the downloader because I
think it's not needed for ReLDI.
