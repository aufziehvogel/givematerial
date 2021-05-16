import argparse
import logging
import os

from givematerial import recommendation


def main():
    logging.basicConfig(level=os.getenv('LOGLEVEL'))

    parser = argparse.ArgumentParser(description='Get text recommendations')
    parser.add_argument('--language', '-l', dest='language', required=True)
    args = parser.parse_args()

    for ts in recommendation.calc_recommendations(args.language):
        print(
            f'== {ts.title} (learning {len(ts.learning)}, total {ts.total}, unknown {len(ts.unknown)}) ==')
        print()
        print(' '.join(ts.unknown))
        print()
        print(ts.text)
        print()
        print()


def manage_read():
    parser = argparse.ArgumentParser(description='Manage read markers')
    parser.add_argument('--language', '-l', dest='language', required=True)
    parser.add_argument('learning', nargs='*')
    args = parser.parse_args()

    with open(f'data/{args.language}/learning', 'at') as f:
        for word in args.learning:
            f.write(f'{word}\n')
