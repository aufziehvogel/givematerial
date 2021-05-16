import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import requests
import time
from typing import List, Tuple
import xextract


@dataclass
class Text:
    title: str
    text: str


def fetch_texts_urls(main_url: str) -> List[Tuple[str, str]]:
    r = requests.get(main_url)
    data = json.loads(r.content.decode('utf-8-sig'))[0]

    urls = []
    for date in data:
        for item in data[date]:
            url = f'https://www3.nhk.or.jp/news/easy/{item["news_id"]}/{item["news_id"]}.html'
            tup = (url, item['title'])
            urls.append(tup)
    return urls


def fetch_text(text_url: str, title: str) -> Text:
    r = requests.get(text_url)
    html = r.content.decode('utf-8-sig')
    sections = xextract.String(
        css='.article-main__body', attr='_all_text').parse(html)
    text = '\n\n'.join([section.strip() for section in sections])
    text = text.replace('\t', '')

    return Text(title=title, text=text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', required=False,
        help='Output folder for lyrics results, will be created. '
        'Defaults to "lyrics"')

    args = parser.parse_args()
    outdir = Path(args.output) if args.output else Path('data/texts')

    main_page = 'https://www3.nhk.or.jp/news/easy/news-list.json'
    texts_urls = fetch_texts_urls(main_page)

    for text_url, title in texts_urls:
        filename = text_url.split('/')[-1]
        text = fetch_text(text_url, title)

        print(f'Writing text for {filename}')
        with open(outdir / f'{filename}.json', 'wt') as f:
            data = {
                'collection': 'nhk-easy',
                'title': f'{text.title}',
                'text': text.text,
                'language': 'jp',
                'url': text_url,
            }
            json.dump(data, f)

        time.sleep(1)
