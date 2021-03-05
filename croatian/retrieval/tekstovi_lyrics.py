import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import requests
import time
from typing import List
import urllib
import xextract


@dataclass
class Lyrics:
    artist: str
    title: str
    text: str


def fetch_lyrics_urls(artist_url: str) -> List[str]:
    r = requests.get(artist_url)
    urls = xextract.String(css='.artLyrList a', attr='href').parse(r.text)
    return [urllib.parse.urljoin(artist_url, url) for url in urls]


def fetch_lyrics(lyrics_url: str) -> Lyrics:
    r = requests.get(lyrics_url)
    artist, title = \
        xextract.String(css='.lyricCapt', attr='_all_text').parse(r.text)
    lyrics = xextract.String(css='.lyric').parse(r.text)
    lyrics_text = '\n\n'.join(lyrics)
    lyrics_text = lyrics_text.replace('\r\n', '\n')

    return Lyrics(artist=artist, title=title, text=lyrics_text)


if __name__ == '__main__':
    # tekstovi.net is awesome, because:
    # - their website is nice and simple - whenever I see them in search
    #   results for lyrics, I am happy
    # - they don't try to block right click, selection of text and so on
    # - they have nice CSS annotation for parsing
    #
    # Please don't abuse their niceness. Only scrape for your own personal
    # use, remain polite (i.e. have sleeps between requests) and only scrape
    # the lyrics you need.

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u', '--url', action='append',
        required=True,
        help='Add artist URLs (may be repeated), '
        'e.g. https://tekstovi.net/2,206,0.html')
    parser.add_argument(
        '-o', '--output', required=False,
        help='Output folder for lyrics results, will be created. '
        'Defaults to "lyrics"')

    args = parser.parse_args()
    artist_pages = args.url
    outdir = Path(args.output) if args.output else Path('lyrics')

    lyrics_urls = []
    for artist_page in artist_pages:
        lyrics_urls += fetch_lyrics_urls(artist_page)
        time.sleep(1)

    for lyrics_url in lyrics_urls:
        lyrics = fetch_lyrics(lyrics_url)

        # TODO: Improve replacement of special chars
        artist_dirname = re.sub('[^0-9a-zA-Z- ]+', '-', lyrics.artist)
        title_filename = re.sub('[^0-9a-zA-Z- ]+', '-', lyrics.title).strip()
        artist_dir = outdir / artist_dirname
        artist_dir.mkdir(exist_ok=True, parents=True)

        print(f'Writing lyrics for {lyrics.artist} - {lyrics.title}')
        with open(artist_dir / title_filename, 'wt') as f:
            f.write(lyrics.text)

        time.sleep(1)
