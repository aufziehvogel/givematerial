import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import requests
import time
from typing import List
import xextract


@dataclass
class Text:
    title: str
    text: str
    url: str


def fetch_article_urls(feed_url: str) -> List[str]:
    r = requests.get(feed_url)
    urls = xextract.String(css='rss channel item link').parse(r.text)
    return urls


def fetch_article(url: str) -> Text:
    r = requests.get(url)
    title = xextract.String(css='.single__title .title').parse(r.text)[0]
    content = xextract.String(css='.article__content', attr='_all_text').parse(r.text)[0]

    return Text(title=title, text=content, url=url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', required=False,
        help='Output folder for lyrics results, will be created. '
        'Defaults to "lyrics"')

    args = parser.parse_args()
    outdir = Path(args.output) if args.output else Path('data/texts')

    article_urls = fetch_article_urls('https://www.poslovni.hr/feed')
    time.sleep(1)

    for url in article_urls:
        article = fetch_article(url)
        article_id = url.split('-')[-1]

        print(f'Writing text {article.title}')
        with open(outdir / f'{article_id}.json', 'wt') as f:
            data = {
                'collection': 'news',
                'title': f'Poslovni - {article.title}',
                'text': article.text,
                'language': 'hr',
                'url': article.url,
            }
            json.dump(data, f)

        time.sleep(1)
