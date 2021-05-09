# GiveMaterial

GiveMaterial should become a collection of scripts or tool to help you
find material (e.g. music, texts) in foreign languages.

The idea is to use your knowledge, compare it to a list of available material
and then propose something useful to you.

GiveMaterial uses a collection of texts to fetch recommendations from. It
loads current vocabulary knowledge from different providers.


## Usage

This is the usage guide after you have gone through the initial ingest of
some texts. I'm planning to make the initial ingest much simpler, too. The
"good" docs will be at the top of this document, the more convoluted stuff
(rough outlines, general ideas) more to the bottom.

GiveMaterial currently supports *Croatian* and *Japanese*. Croatian uses
vocabulary for text recommendation, Japanese uses Kanji. For Croatian, you
have to manage vocabulary status on your own with text files. Japanese kanji
knowledge is pulled from Wanikani.


### Croatian

To get some recommendations for Croatian execute:

```bash
givematerial -l hr
```

This will give you a list of texts with the new vocabulary at the top. If
you have looked up all vocabulary (and added it to your vocabulary learning
program like Anki), you can mark them as `learning` with the following
command:

```bash
gm-read -l hr word1 word2 word3 word4
```

This command will add `word1`, `word2`, `word3`, and `word4` to the list of
words that you are currently learning.

You can now choose to get new recommendations based on your updated learning
lists with `givematerial -l hr` again.

From time to time you should move the words from `learning` to `known`, I will
add some better way to do this than manually in the future.


### Japanese

Japanese recommendation uses Wanikani to retrieve your kanji knowledge. Thus,
you have to specify a read-only Wanikani token in the environment variable
`WANIKANI_TOKEN`.

To get some recommendations for Japanese execute:

```bash
WANIKANI_TOKEN=specify-your-token givematerial -l jp
```

This will fetch a list of kanji that you are currently learning (SRS levels
1 to 4), and a list of known kanji (SRS levels 5 to 9) from Wanikani.


## Data Store for Texts

GiveMaterial wants to be agnostic to the type of text that it recommends.
Currently, I use it for song lyrics, but I plan to extend it to Japanese
simple news. Other ideas might be Croatian news, English short stories,
movie sub titles and so on. Over time probably a vast set of metadata will
evolve, but for now texts must contain the following information:

- `collection`: a name for the collection from which this text comes and in
  which it should be displayed
- `title`: a title for the text
- `text`: the full text without any markup
- `language`: the language of this text

Additional fields are allowed, but not used for now. A possible method to use
this with lyrics could be to use the following scheme:

```json
{
    "collection": "lyrics",
    "title": "Artist - Title of Song",
    "text": "Full Lyrics of Song",
    "language": "en",
    "artist": "Artist",
    "songtitle": "Title of Song"
}
```

If you already know that you will only ever add lyrics, you could also set
the artist's name as `collection`.

The JSON documents for texts are stored in the folder `data/texts` or one or
multiple levels of subfolders within this folder. This means you are free to
structure your texts according to data sources.

There are some helper scripts to retrieve texts. For example, it's possible
to retrieve song lyrics for specific artists from tekstovi.net with the
following command:

```bash
python croatian/retrieval/tekstovi_lyrics.py \
    --url https://tekstovi.net/2,206,0.html --output data/texts/tekstovi
```


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

For vocabulary frequency analysis, download the hrLex dataset
([Ljubešić, Nikola, 2019, Inflectional lexicon hrLex 1.3, Slovenian language resource repository CLARIN.SI](http://hdl.handle.net/11356/1232)]) and convert it to a dictionary of frequencies per
lemma.

```bash
mkdir -p data/vocabulary
wget https://www.clarin.si/repository/xmlui/bitstream/handle/11356/1232/hrLex_v1.3.gz -O data/vocabulary/hrLex_v1.3.gz
gunzip data/vocabulary/hrLex_v1.3.gz
python croatian/hrlex_frequency.py
```

These commands transform the hrLex dataset to a dictionary of frequencies per
lemma at `data/vocabulary/word_frequencies.json`.

To get started with Croatian fetch some lyrics for your favourite artist, e.g.
Prljavo Kazaliste:

```bash
python croatian/retrieval/tekstovi_lyrics.py \
    --url https://tekstovi.net/2,206,0.html --output data/lyrics
```

This will download the lyrics and store them in text files in the folder
`data/lyrics`.

#### Lemmatizer

Next, you can use a lemmatizer to lemmatize the lyrics. You can choose between
`cstlemma` and `classla`.

##### cstlemma

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

##### classla

```bash
# Install classla and download Croatian models
pip install classla
python -c "import classla; classla.download('hr')"
python -c "import classla; classla.download('hr', type='nonstandard')"
```

classla allows you to list the lemmas including frequencies for all songs.
This will be improved to a more useful recommendation engine later:


## Japanese

Japanese lemmatization (or is it only tokenization?) [does exist](http://taku910.github.io/mecab/)
([project with install instructions in a dockerfile](https://github.com/CatalystCode/jp_tokenizer))
but since I study a lot with Wanikani using Kanji for recommendations would
be more useful (also quicker to implement).

- import Kanji status from Wanikani API
- use each individual kanji as lemma
- from there it's similar to the Croatian recommendation, just search for
  texts with a few unknown kanji

Japanese data sources:

- [NHK Easy](https://www3.nhk.or.jp/news/easy/)
- [Animelyrics](http://www.animelyrics.com/) (.jis suffix of URL is for
  Kanji version if available)


## English

In my opinion English also makes sense. While my level of English (and probably
that of everybody finding an open source project on Github) is already
okay'ish, I struggle with less frequent vocabulary used in novels and better
publications.

- challenge: for English I will need a good way to mark a lot of words as known
  quickly to initialize the system
  - might work to let the user specify all unknown words for a text and all
    others will be copied to their `known` list, e.g. with
    `givematerial unknown text-id-1 grommet pot-valor`
- possible data sources might be publications from big news papers or maybe
  also public fiction sites


## Get Recommendations

```bash
pip install -e .
givematerial -l hr
```

### Ideas

Good presentation of results is a quite hard task (at least for me).
Here are some ideas:

- calculate metrics for each song and for each artist and display them in a
  nice visual manner:
  - number of different words (for artists as a range with mean, min, max)
  - relative importance of words (average, min, max might help, but we probably
    have to improve it from there)
  - ideally the visualisation works in command line, because I currently
    don't want to invest time into designing an HTML page
  - number of unknown words (requires a list of known words)
    - for beginning just manage the vocab list as two simple text files where
      I manually add words; "learning" where I add words when I listen to a
      song and "known" where I add words when I feel like I know them
  - for artists something like a "percentage of all words from this artist
    that you already know"
- different categories to list texts are probably useful, e.g.
  - text with few unknown words (easy readings)
  - texts with unknown words with high frequency according to frequency
    stats (important to learn)
  - texts with unknown words that are occuring in many texts in the
    user's database (quick wins)
- not really related to this project directly (except if somebody wants to
  learn specific vocab), but interesting: create tag clouds of common words
  for artists; e.g. I would guess that for Thompson words like *domovina*
  are very common, and I've already seen *haljina* in two Prljavo Kazaliste
  lyrics now
- use [Anki Connect](https://foosoft.net/projects/anki-connect/)
  to read vocab knowledge from local Anki


### Open Issues

For raw `cstlemma` you have to remove all punctuation. Otherwise words won't
be recognized. Currently, this is not handled by the downloader because I
think it's not needed for ReLDI.
