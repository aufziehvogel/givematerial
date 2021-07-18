import argparse
from dataclasses import dataclass
import json
import langdetect
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
    url: str


def fetch_lyrics_urls(artist_url: str) -> List[str]:
    r = requests.get(artist_url)
    urls = xextract.String(
        css='.albumDetail .toplist a.nested', attr='href').parse(r.text)
    return [urllib.parse.urljoin(artist_url, url) for url in urls]


def fetch_lyrics(lyrics_url: str) -> Lyrics:
    r = requests.get(lyrics_url)
    title = xextract.String(css='.lyricsContainer h2').parse(r.text)[0]
    title = title.replace(' Songtext', '')
    artist = \
        xextract.String(css='.contentHeader h1 span.sub a').parse(r.text)[0]
    lyrics = xextract.String(css='#lyrics', attr='_all_text').parse(r.text)[0]

    lyrics = re.sub(r'\<\!\-\-.+\]\]\>\*\/', '', lyrics, flags=re.DOTALL)

    return Lyrics(artist=artist, title=title, text=lyrics, url=lyrics_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u', '--url', action='append',
        required=True,
        help='Add artist URLs (may be repeated), '
        'e.g. https://www.songtexte.com/artist/enrique-iglesias-7bd62e44.html')
    parser.add_argument(
        '-o', '--output', required=False,
        help='Output folder for lyrics results, will be created. '
        'Defaults to "data/texts"')

    args = parser.parse_args()
    artist_pages = args.url
    outdir = Path(args.output) if args.output else Path('data/texts')

    lyrics_urls = []
    for artist_page in artist_pages:
        lyrics_urls += fetch_lyrics_urls(artist_page)
        time.sleep(1)

    for lyrics_url in lyrics_urls:
        try:
            lyrics = fetch_lyrics(lyrics_url)
        except:
            continue

        # TODO: Improve replacement of special chars
        artist_dirname = re.sub('[^0-9a-zA-Z- ]+', '-', lyrics.artist)
        title_filename = re.sub('[^0-9a-zA-Z- ]+', '-', lyrics.title).strip()
        artist_dir = outdir / artist_dirname
        artist_dir.mkdir(exist_ok=True, parents=True)

        print(f'Writing lyrics for {lyrics.artist} - {lyrics.title}')
        with open(artist_dir / f'{title_filename}.json', 'wt') as f:
            data = {
                'collection': 'lyrics',
                'title': f'{lyrics.artist} - {lyrics.title}',
                'text': lyrics.text,
                'language': langdetect.detect(lyrics.text),
                'url': lyrics.url,
            }
            json.dump(data, f)

        time.sleep(1)
